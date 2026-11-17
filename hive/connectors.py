"""Owner-configured MCP Streamable HTTP connections, using the official v1 SDK.

Discovery is explicit. Server risk hints are ignored: tools require approval unless
the owner explicitly lists them as read-only. Credentials stay in the vault/env.
"""
import argparse
import asyncio
import hashlib
import json
import os
import re
from datetime import timedelta
from urllib.parse import urlparse

from . import memory, tools, vault


def path():
    return os.path.join(os.path.dirname(memory.DIR), 'mcp.json')


def config():
    return vault.load_json(path(), {})


def _url(url):
    parsed = urlparse(url)
    if (parsed.scheme not in ('http', 'https') or not parsed.hostname or parsed.username or parsed.password or
            parsed.fragment or (parsed.scheme == 'http' and parsed.hostname not in ('localhost', '127.0.0.1', '::1'))):
        raise ValueError('Use an HTTPS MCP endpoint, or HTTP on localhost, without embedded credentials.')
    return url


def fingerprint(name):
    entry = config().get(name)
    if entry is None:
        return 'missing'
    token = os.environ.get(entry.get('token_env', ''), '')
    return hashlib.sha256(json.dumps([entry, token], sort_keys=True).encode()).hexdigest()


async def _request(entry, operation, name=None, args=None):
    try:
        from mcp import ClientSession
        from mcp.client.streamable_http import streamablehttp_client
    except ImportError:
        raise RuntimeError('Install the MCP extra: pip install "hive-swarm[mcp]"') from None
    headers = {}
    env_name = entry.get('token_env')
    if env_name:
        token = os.environ.get(env_name)
        if not token:
            raise RuntimeError('The configured MCP token environment variable is missing.')
        headers['Authorization'] = 'Bearer ' + token
    async with streamablehttp_client(_url(entry['url']), headers=headers, timeout=timedelta(seconds=20),
                                     sse_read_timeout=timedelta(seconds=45)) as (read, write, _):
        async with ClientSession(read, write, read_timeout_seconds=timedelta(seconds=45)) as session:
            await session.initialize()
            found, cursor, cursors = [], None, set()
            for _ in range(20):
                result = await session.list_tools(cursor=cursor)
                found.extend(tool.model_dump(mode='json', by_alias=True) for tool in result.tools)
                cursor = result.nextCursor
                if not cursor:
                    break
                if cursor in cursors:
                    raise RuntimeError('MCP discovery repeated a page cursor.')
                cursors.add(cursor)
            else:
                raise RuntimeError('MCP discovery exceeded 20 pages.')
            if len(found) > 200:
                raise RuntimeError('A connector may expose at most 200 tools.')
            if operation == 'discover':
                return found
            current = next((t for t in found if t['name'] == name), None)
            expected = next((t for t in entry.get('tools', []) if t['name'] == name), None)
            if not current or not expected or current.get('inputSchema') != expected.get('inputSchema'):
                raise tools.Refused('The MCP tool schema changed. Run hive mcp refresh before calling it.')
            # Never retry tools/call here: a lost response can follow a successful write.
            result = await session.call_tool(name, arguments=args)
            return result.model_dump(mode='json', by_alias=True)


def request(entry, operation, name=None, args=None):
    async def bounded():
        return await asyncio.wait_for(_request(entry, operation, name, args), timeout=60)
    return asyncio.run(bounded())


def refresh(name):
    entries = config()
    if name not in entries:
        raise ValueError('Unknown MCP connection')
    found = request(entries[name], 'discover')
    names = set()
    for item in found:
        tool_name = item.get('name')
        if not isinstance(tool_name, str) or not re.fullmatch(r'[A-Za-z0-9_.-]{1,128}', tool_name) or tool_name in names:
            raise ValueError('Invalid or duplicate MCP tool name')
        names.add(tool_name)
        # Check schemas now; required arguments are checked when actually called.
        from jsonschema import Draft202012Validator
        Draft202012Validator.check_schema(item.get('inputSchema', {}))
    entries[name]['tools'] = found
    vault.save_json(path(), entries)
    return len(found)


def catalog(repo):
    from .runtime_tools import Tool
    out = []
    for name, entry in config().items():
        identity = fingerprint(name)
        for item in entry.get('tools', []):
            remote_name = item['name']
            read = remote_name in entry.get('read_tools', [])
            def call(args, server=name, tool_name=remote_name, expected=identity, readonly=read):
                if fingerprint(server) != expected:
                    raise tools.Refused('The MCP connection changed. Start a new request.')
                result = request(config()[server], 'call', tool_name, args)
                return {'status': ('failed' if readonly else 'unknown') if result.get('isError') else 'done',
                        'data': result.get('structuredContent') or result.get('content', [])}
            out.append(Tool(f'mcp.{name}.{remote_name}', item.get('description', '')[:1200], item['inputSchema'],
                            tools.READ if read else tools.EXTERNAL, read, call, identity))
    return out


def main(argv):
    parser = argparse.ArgumentParser(prog='hive mcp')
    sub = parser.add_subparsers(dest='command', required=True)
    add = sub.add_parser('add'); add.add_argument('name'); add.add_argument('url')
    add.add_argument('--token-env', default=''); add.add_argument('--read-tool', action='append', default=[])
    for command in ('refresh', 'remove'):
        sub.add_parser(command).add_argument('name')
    sub.add_parser('list')
    args = parser.parse_args(argv)
    entries = config()
    if args.command == 'list':
        for name, entry in entries.items():
            print(f"{name}: {len(entry.get('tools', []))} tools; {len(entry.get('read_tools', []))} owner-marked reads")
        return 0
    if args.command == 'add':
        if not re.fullmatch(r'[a-z][a-z0-9_-]{0,31}', args.name):
            parser.error('Connection names use lowercase letters, numbers, underscores or hyphens.')
        if args.token_env and not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', args.token_env):
            parser.error('--token-env must name an environment variable, not contain its value.')
        entries[args.name] = {'url': _url(args.url), 'token_env': args.token_env,
                              'read_tools': args.read_tool, 'tools': []}
        vault.save_json(path(), entries)
    if args.command == 'remove':
        entries.pop(args.name, None); vault.save_json(path(), entries); return 0
    print(f'{args.name}: discovered {refresh(args.name)} tools.')
    return 0
