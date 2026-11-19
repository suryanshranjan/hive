"""Real headed Chromium and noVNC from a phone-sized browser over local HTTPS."""
import datetime as dt
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

sys.path.insert(0,os.getcwd())
from hive import browser, gateway, memory, sandbox, store


class PhoneFixture(unittest.TestCase):
    def test_stdio_container_passes_only_selected_credentials_and_mounts(self):
        import json
        from hive import connectors,mcp_stdio
        server = """
import json,os,sys
for line in sys.stdin:
    req=json.loads(line)
    if 'id' not in req: continue
    method=req['method']
    if method=='initialize':
        result={'protocolVersion':req['params']['protocolVersion'],'serverInfo':{'name':'fixture','version':'1'},'capabilities':{'tools':{}}}
    elif method=='tools/list':
        result={'tools':[{'name':'inspect','inputSchema':{'type':'object','properties':{}}}]}
    elif method=='tools/call':
        data=[os.getenv('HIVE_FIXTURE_SELECTED'),os.getenv('HIVE_FIXTURE_PRIVATE'),os.path.exists('/var/run/docker.sock'),open('/inputs/0').read()]
        result={'content':[{'type':'text','text':json.dumps(data)}]}
    print(json.dumps({'jsonrpc':'2.0','id':req['id'],'result':result}),flush=True)
"""
        with tempfile.TemporaryDirectory(dir=os.getcwd()) as folder:
            path=Path(folder)/'document'
            path.write_text('registered',encoding='utf-8')
            cfg=mcp_stdio.entry('python:3.12-slim',['python','-u','-c',server],['HIVE_FIXTURE_SELECTED'],[path],['inspect'])
            with patch.dict(os.environ,{'HIVE_FIXTURE_PRIVATE':'private','HIVE_FIXTURE_SELECTED':'selected'}):
                cfg['tools']=connectors.request(cfg,'discover')
                result=connectors.request(cfg,'call','inspect',{})
            self.assertEqual(json.loads(result['content'][0]['text']),['selected',None,False,'registered'])

    def test_phone_signin_and_return(self):
        import uvicorn
        from cryptography import x509
        from cryptography.hazmat.primitives import hashes,serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        from playwright.sync_api import sync_playwright
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            self.addCleanup(store.close)
            with socket.socket() as sock:
                sock.bind(('127.0.0.1',0))
                port=sock.getsockname()[1]
            origin=f'https://127.0.0.1:{port}'
            key=rsa.generate_private_key(public_exponent=65537,key_size=2048)
            name=x509.Name([x509.NameAttribute(x509.oid.NameOID.COMMON_NAME,'localhost')])
            now=dt.datetime.now(dt.timezone.utc)
            cert=(x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(key.public_key())
                  .serial_number(x509.random_serial_number()).not_valid_before(now-dt.timedelta(minutes=1))
                  .not_valid_after(now+dt.timedelta(hours=1)).sign(key,hashes.SHA256()))
            (root/'cert').write_bytes(cert.public_bytes(serialization.Encoding.PEM))
            (root/'key').write_bytes(key.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,
                                                       serialization.NoEncryption()))
            web='http://127.0.0.1:8042'
            class Owner:
                chat=111
            with (patch.object(memory,'DIR',str(root/'rules')),patch.object(gateway,'config',return_value={'origin':origin}),
                  patch.object(browser,'config',return_value={'enabled':True,'control':True,'local_origins':[web]})):
                session=browser.session_for(folder)
                session.call('inspect',{})
                inspect=subprocess.check_output(sandbox.docker()+['inspect','--format',
                    '{{range .Mounts}}{{if eq .Destination "/profile"}}{{.Name}}{{end}}{{end}}',session.container],text=True).strip()
                server=uvicorn.Server(uvicorn.Config(gateway.app(origin),host='127.0.0.1',port=port,
                                    ssl_certfile=str(root/'cert'),ssl_keyfile=str(root/'key'),log_level='error',access_log=False))
                thread=threading.Thread(target=server.run,daemon=True)
                thread.start()
                try:
                    page_html=('<body onclick="document.querySelector(\'input\').focus()" style="min-height:100vh">'
                               '<form onsubmit="event.preventDefault();if(document.querySelector(\'input\').value===\'fixture\')'
                               'location.href=\'/done.html\'"><input autofocus type=password><button>Sign in</button></form>')
                    fixture=("from pathlib import Path;from http.server import HTTPServer,SimpleHTTPRequestHandler;"
                             "import os;os.chdir('/tmp');Path('login.html').write_text("+repr(page_html)+");"
                             "Path('done.html').write_text('<h1>Fixture signed in</h1>');"
                             "\nclass Site(SimpleHTTPRequestHandler):\n def do_GET(self):\n"
                             "  if self.path=='/done.html': Path('signed-in').touch()\n"
                             "  super().do_GET()\nHTTPServer(('127.0.0.1',8042),Site).serve_forever()")
                    subprocess.run(sandbox.docker()+['exec','-d',session.container,'python','-c',fixture],check=True)
                    subprocess.run(sandbox.docker()+['exec',session.container,'curl','-fsS','--retry','8',
                                   '--retry-connrefused','--retry-delay','1',web+'/login.html'],
                                   check=True,capture_output=True,timeout=15)
                    self.assertTrue(session.call('open',{'url':web+'/login.html'})['data']['takeover_required'])
                    link=gateway.issue(Owner(),folder)
                    with sync_playwright() as p:
                        phone=p.chromium.launch(executable_path=p.chromium.executable_path)
                        try:
                            page=phone.new_page(viewport={'width':390,'height':844},is_mobile=True,
                                                has_touch=True,ignore_https_errors=True)
                            page.goto(link)
                            page.get_by_text('You have control',exact=True).wait_for(timeout=90000)
                            page.get_by_role('main').locator('canvas').tap()
                            keyboard=page.get_by_label('Phone keyboard')
                            keyboard.fill('fixture')
                            keyboard.press('Enter')
                            check=("import time;from pathlib import Path; "
                                   "exec(\"for i in range(50):\\n if Path('/tmp/signed-in').exists(): break\\n time.sleep(.1)\");"
                                   "assert Path('/tmp/signed-in').exists(),'Fixture sign-in did not complete'")
                            subprocess.run(sandbox.docker()+['exec',session.container,'python','-c',check],check=True)
                            with page.expect_response(lambda r:r.url.endswith('/return')) as released:
                                page.get_by_text('Return control to Hive').click()
                            self.assertEqual(released.value.status,200,released.value.text())
                            page.get_by_text('Browser control returned.',exact=False).wait_for(timeout=10000)
                            self.assertIn('Fixture signed in',session.call('inspect',{})['data']['text'])
                        finally:
                            phone.close()
                finally:
                    server.should_exit=True
                    thread.join(8)
                    browser.close_all()
                    subprocess.run(sandbox.docker()+['volume','rm',inspect],check=True,capture_output=True)
                    store.close()


if __name__=='__main__':
    unittest.main()
