"""Owner-selected Docker stdio servers. No host shell or implicit host credentials."""
import os
from pathlib import Path
import re
import subprocess

from . import sandbox, tools


def mount(value):
    path = Path(value).resolve(strict=True)
    home = Path.home().resolve()
    if (not path.is_file() and not path.is_dir()) or home==path or path in home.parents or home in path.parents:
        raise tools.Refused('Select a file or directory outside the host home.')
    if (',' in str(path) or 'docker.sock' in str(path).lower() or 'docker_engine' in str(path).lower()
            or str(path).startswith('\\\\') or path.is_socket()):
        raise tools.Refused('Host sockets and device paths cannot be mounted.')
    if path.is_dir() and any(p.is_socket() or p.name.lower()=='docker.sock' for p in path.rglob('*')):
        raise tools.Refused('The selected mount contains a socket.')
    return str(path)


def entry(image, args, env, mounts, read):
    if not image or image.startswith('-') or not isinstance(args,list) or not all(isinstance(a,str) for a in args):
        raise tools.Refused('Specify a Docker image and a JSON array of string arguments.')
    if any(not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*',name) for name in env):
        raise tools.Refused('Select credentials by environment variable name.')
    sha = subprocess.check_output(sandbox.docker()+['image','inspect','--format','{{.Id}}',image],text=True).strip()
    if not re.fullmatch(r'sha256:[a-f0-9]{64}',sha):
        raise tools.Refused('The local image identity is unavailable.')
    return {'transport':'stdio','image':sha,'args':args,'env':env,'mounts':[mount(p) for p in mounts],
            'read_tools':read,'tools':[]}


def transport(cfg):
    from mcp import StdioServerParameters
    from mcp.client.stdio import stdio_client
    docker = sandbox.docker()
    args = docker[1:]+['run','--rm','--init','-i','--pull=never','--read-only','--network','none',
                       '--user','65534','--cap-drop','ALL','--security-opt','no-new-privileges',
                       '--pids-limit','128','--memory','512m','--cpus','1','--tmpfs','/tmp:rw,nosuid,nodev,size=64m']
    env = {}
    for name in cfg['env']:
        if name not in os.environ:
            raise tools.Refused('A selected stdio credential is unavailable.')
        args += ['--env',name]
        env[name] = os.environ[name]
    for n,source in enumerate(cfg['mounts']):
        path = sandbox.host_path(mount(source))
        args += ['--mount',f'type=bind,source={path},target=/inputs/{n},readonly']
    return stdio_client(StdioServerParameters(command=docker[0],args=args+[cfg['image'],*cfg['args']],env=env))
