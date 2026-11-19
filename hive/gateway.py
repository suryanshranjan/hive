"""Optional host-local gateway. The owner's reverse proxy terminates HTTPS."""
import argparse
import asyncio
import hashlib
import json
import os
import re
import secrets
import subprocess
import threading
import time
from pathlib import Path
from urllib.parse import urlsplit

from . import browser, policy, sandbox, store, tasks, tools, vault

COOKIE = '__Host-hive-control'
COMMAND = re.compile(r'^(browser takeover(?: ([0-9a-f]{12}))?|return browser|revoke browser)$',re.I)


def command(ch, repo, text):
    match = COMMAND.fullmatch(text.strip())
    if not match:
        return None
    if match[1].lower().startswith('browser takeover'):
        url = issue(ch,repo,match[2])
        ch.send_link('This single-use browser link expires in two minutes.','Open browser',url)
    elif match[1].lower() == 'revoke browser':
        revoke(ch,repo)
        ch.send('The browser link and owner session have been revoked. Automation is paused.')
    else:
        ch.send(give_back(ch,repo))
    return 'browser_control'


def cfg_path():
    return str(Path(browser.folder()).parent / 'gateway.json')


def config():
    return vault.load_json(cfg_path(), {})


def hash_token(value):
    return hashlib.sha256(value.encode()).hexdigest()


def held(repo):
    return store.connect().execute('SELECT 1 FROM browser_control WHERE project=?',
                                   (tasks._project(repo),)).fetchone() is not None


def issue(ch, repo, tid=None):
    cfg = config()
    if not cfg or not browser.config().get('control') or not browser.config().get('enabled'):
        raise tools.Refused('Configure the HTTPS gateway, set up browser control and enable the browser first.')
    owner, chat, project = tasks._scope(ch,repo)
    if tid and not tasks.get(tid,ch,repo):
        raise tools.Refused('That task is unavailable in this project.')
    ticket = secrets.token_urlsafe(32)
    with browser.LOCK:
        session = browser.session_for(repo)
        if not session.headed:
            raise tools.Refused('Restart the listener to use the headed browser.')
        revoke(ch,repo)
        store.connect().execute('INSERT OR REPLACE INTO browser_control VALUES(?,?,?,?,?,?,?,?,?)',
                                (project,owner,chat,tid,session.container,hash_token(ticket),time.time()+120,None,None))
    return cfg['origin'] + '/control#' + ticket


def revoke(ch, repo):
    scope = tasks._scope(ch,repo)
    with browser.LOCK:
        row = store.connect().execute('SELECT * FROM browser_control WHERE owner_id=? AND chat_id=? AND project=?',
                                      scope).fetchone()
        if row:
            store.connect().execute('UPDATE browser_control SET ticket=NULL,session=NULL WHERE project=?',(scope[2],))
            # Stop the owner's control socket before automation can inspect the page.
            subprocess.run(sandbox.docker()+['exec',row['container'],'pkill','-x','x11vnc'],
                           capture_output=True,timeout=12)


def give_back(ch, repo, cookie=None):
    scope = tasks._scope(ch,repo)
    with browser.LOCK:
        row = store.connect().execute('SELECT * FROM browser_control WHERE owner_id=? AND chat_id=? AND project=?',scope).fetchone()
        if not row:
            raise tools.Refused('There is no browser takeover in this project.')
        if cookie and (row['session'] != hash_token(cookie) or row['session_until'] <= time.time()):
            raise tools.Refused('The owner session expired or was revoked.')
        revoke(ch,repo)
        session = browser.session_for(repo)
        if session.container != row['container']:
            raise tools.Refused('The original browser session ended. Open a new takeover to sign in again.')
        fresh = session.call('inspect',{})['data']
        if fresh.get('takeover_required'):
            raise tools.Refused('The browser is still on a sign-in screen. Open a fresh takeover link to finish.')
        with store.transaction() as con:
            con.execute('DELETE FROM browser_control WHERE project=?',(scope[2],))
            if row['task_id']:
                task = tasks.get(row['task_id'],ch,repo)
                if task and not task['control']:
                    from . import dispatcher
                    meta = task['metadata']
                    meta['returned_page'] = fresh
                    tasks.update(task['id'],metadata=meta)
                    if task['mode']=='adaptive' and task['state']=='waiting_browser':
                        tasks.update(task['id'],state='queued',detail='Owner returned browser control.')
                        dispatcher.enqueue(task,policy.RequestContext(project=repo,update_id='return:'+secrets.token_hex(8)))
    return 'Browser control returned. Hive inspected the current page.'


def session_row(cookie):
    if not cookie:
        return None
    return store.connect().execute('SELECT * FROM browser_control WHERE session=? AND session_until>?',
                                   (hash_token(cookie),time.time())).fetchone()


def app(origin):
    from starlette.applications import Starlette
    from starlette.responses import Response, HTMLResponse, JSONResponse
    from starlette.routing import Route, WebSocketRoute
    from starlette.websockets import WebSocketDisconnect
    def same_host(req):
        return req.headers.get('host','').lower()==urlsplit(origin).netloc.lower()
    def same_origin(req):
        return same_host(req) and req.headers.get('origin')==origin
    def private(response):
        response.headers.update({'Cache-Control':'no-store','Referrer-Policy':'no-referrer','X-Content-Type-Options':'nosniff'})
        return response
    async def page(req):
        if not same_host(req):
            return Response(status_code=403)
        nonce = secrets.token_urlsafe(18)
        script = """
const status = document.querySelector('p');
const ticket = location.hash.slice(1);
history.replaceState(null,'','/control');
try {
  if (ticket) {
    const r = await fetch('/exchange',{method:'POST',body:ticket});
    if (!r.ok) throw Error('Link expired or already used.');
  }
  const {default:RFB} = await import('/assets/core/rfb.js');
  const screen = new RFB(document.querySelector('main'),'wss://'+location.host+'/socket');
  let returning=false;
  screen.scaleViewport=true;
  const keyboard=document.querySelector('input');
  const sendText=value=>{
    for(const char of value){
      const code=char.codePointAt(0);
      screen.sendKey(code<=255?code:0x01000000+code);
    }
    keyboard.value='';
  };
  keyboard.oninput=e=>{if(!e.isComposing) sendText(keyboard.value);};
  keyboard.onkeydown=e=>{
    const code={Enter:0xff0d,Tab:0xff09,Backspace:0xff08}[e.key];
    if(code){e.preventDefault();screen.sendKey(code);}
  };
  keyboard.onbeforeinput=e=>{
    if(e.inputType==='deleteContentBackward'){e.preventDefault();screen.sendKey(0xff08);}
  };
  screen.addEventListener('connect',()=>status.textContent='You have control');
  screen.addEventListener('disconnect',()=>{if(!returning) status.textContent='Disconnected';});
  document.querySelector('button').onclick=async()=>{
    returning=true;
    const r=await fetch('/return',{method:'POST'});
    status.textContent=await r.text();
    if (r.ok) screen.disconnect();
  };
} catch(e) { status.textContent=e.message; }
"""
        body = ('<!doctype html><meta name="viewport" content="width=device-width,initial-scale=1">'
                '<title>Hive browser</title><p>Connecting…</p><button>Return control to Hive</button>'
                '<label>Phone keyboard <input type="password" autocomplete="off" autocapitalize="off" spellcheck="false"></label>'
                '<main style="height:80vh"></main>' + f'<script nonce="{nonce}" type="module">{script}</script>')
        resp = private(HTMLResponse(body))
        resp.headers['Content-Security-Policy'] = (f"default-src 'self'; script-src 'self' 'nonce-{nonce}'; "
            f"connect-src 'self' wss://{urlsplit(origin).netloc}; style-src 'unsafe-inline'; img-src 'self' data:; "
            "frame-ancestors 'none'; object-src 'none'; base-uri 'none'")
        return resp
    async def exchange(req):
        if not same_origin(req):
            return Response(status_code=403)
        body = await req.body()
        if not re.fullmatch(rb'[A-Za-z0-9_-]{43}',body):
            return Response(status_code=403)
        cookie = secrets.token_urlsafe(32)
        with store.transaction() as con:
            won = con.execute('UPDATE browser_control SET ticket=NULL,session=?,session_until=? WHERE ticket=? AND ticket_until>?',
                              (hash_token(cookie),time.time()+600,hash_token(body.decode()),time.time())).rowcount
        if not won:
            return Response(status_code=403)
        response = private(Response(status_code=204))
        response.set_cookie(COOKIE,cookie,max_age=600,secure=True,httponly=True,samesite='strict',path='/')
        return response
    async def asset(req):
        row = session_row(req.cookies.get(COOKIE))
        path = req.path_params['path']
        if (not same_host(req) or not row or not re.fullmatch(r'(core|vendor)/[A-Za-z0-9_./-]+\.js',path)
                or '..' in path.split('/')):
            return Response(status_code=403)
        got = await asyncio.to_thread(subprocess.run,sandbox.docker()+['exec',row['container'],'cat','/usr/share/novnc/'+path],
                                      capture_output=True,timeout=15)
        return private(Response(got.stdout,media_type='text/javascript')) if not got.returncode else Response(status_code=404)
    async def release(req):
        row = session_row(req.cookies.get(COOKIE))
        if not same_origin(req) or not row:
            return Response(status_code=403)
        class OwnerChat:
            chat = row['chat_id']
        try:
            msg = await asyncio.to_thread(give_back,OwnerChat(),row['project'],req.cookies[COOKIE])
        except tools.Refused as exc:
            return private(Response(str(exc),status_code=409))
        resp = private(Response(msg))
        resp.delete_cookie(COOKIE,path='/',secure=True,httponly=True,samesite='strict')
        return resp
    async def socket(ws):
        cookie = ws.cookies.get(COOKIE)
        row = session_row(cookie)
        if not same_origin(ws) or not row:
            await ws.close(code=1008)
            return
        await ws.accept(subprotocol='binary' if 'binary' in ws.scope.get('subprotocols',[]) else None)
        proc = await asyncio.create_subprocess_exec(*sandbox.docker(),'exec','-i',row['container'],
                  'python','-m','hive.vnc_pipe',stdin=asyncio.subprocess.PIPE,stdout=asyncio.subprocess.PIPE,
                  stderr=asyncio.subprocess.DEVNULL)
        async def upstream():
            while data := await proc.stdout.read(65536):
                if not session_row(cookie):
                    return
                await ws.send_bytes(data)
        async def downstream():
            while session_row(cookie):
                data = await ws.receive_bytes()
                if not session_row(cookie):
                    return
                proc.stdin.write(data)
                await proc.stdin.drain()
        async def expiry():
            while session_row(cookie):
                await asyncio.sleep(0.25)
        pumps = [asyncio.create_task(fn()) for fn in (upstream,downstream,expiry)]
        try:
            await asyncio.wait(pumps,return_when=asyncio.FIRST_COMPLETED)
        finally:
            for pump in pumps:
                pump.cancel()
            await asyncio.gather(*pumps,return_exceptions=True)
            proc.stdin.close()
            if proc.returncode is None:
                proc.terminate()
            await proc.wait()
            try:
                await ws.close()
            except (RuntimeError,WebSocketDisconnect):
                pass
    async def callback(req):
        from . import mcp_auth
        if not same_host(req) or not mcp_auth.callback(req.path_params['name'],req.query_params):
            return private(Response('Invalid or expired login.',status_code=403))
        return private(Response('Sign-in response received. Return to Hive.'))
    async def ready(req):
        return JSONResponse({'gateway':'ready'}) if same_host(req) else Response(status_code=403)
    return Starlette(routes=[Route('/ready',ready),Route('/control',page),Route('/exchange',exchange,methods=['POST']),
        Route('/return',release,methods=['POST']),Route('/assets/{path:path}',asset),WebSocketRoute('/socket',socket),
        Route('/oauth/{name}',callback)])


def serve():
    cfg = config()
    if not cfg:
        return None
    store.connect().execute('UPDATE browser_control SET ticket=NULL,session=NULL')
    import uvicorn
    server = uvicorn.Server(uvicorn.Config(app(cfg['origin']),host='127.0.0.1',port=cfg['port'],
                                           access_log=False,proxy_headers=False,log_level='warning'))
    threading.Thread(target=server.run,daemon=True).start()
    return server


def main(argv):
    parser = argparse.ArgumentParser(prog='hive gateway')
    parser.add_argument('command',choices=['configure','check'])
    parser.add_argument('address',nargs='?')
    parser.add_argument('--port',type=int,default=8791)
    args = parser.parse_args(argv)
    if args.command == 'configure':
        url = urlsplit(args.address or '')
        if (url.scheme!='https' or not url.hostname or url.username or url.password or url.path not in ('','/')
                or url.query or url.fragment or not 1<=args.port<=65535):
            parser.error('Supply the public HTTPS origin and a valid loopback port.')
        vault.save_json(cfg_path(),{'origin':'https://'+url.netloc,'port':args.port})
        print('Gateway configuration saved. Restart hive listen.')
        return 0
    import urllib.request
    cfg = config()
    if not cfg:
        print('Gateway is unconfigured.'); return 1
    with urllib.request.urlopen(cfg['origin']+'/ready',timeout=10) as response:
        ready = json.load(response).get('gateway')=='ready'
    print('Ready' if ready else 'Readiness check failed')
    return int(not ready)
