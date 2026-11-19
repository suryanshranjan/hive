"""Ticket, origin, callback, OAuth state and container configuration boundaries."""
import asyncio
import json
import os
from pathlib import Path
import sys
import time
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, os.getcwd())
import test_tasks as fixtures
from hive import browser, gateway, mcp_auth, mcp_stdio, store, tools


class GatewayTests(unittest.TestCase):
    setUp = fixtures.TaskTests.setUp
    channel = fixtures.TaskTests.channel

    def test_takeover_session_replay_expiry_and_revocation(self):
        from starlette.testclient import TestClient
        origin = 'https://fixture.invalid'
        client = TestClient(gateway.app(origin),base_url=origin,headers={'origin':origin})
        session = Mock(headed=True,container='fixture')
        store.connect()
        with (patch.object(gateway,'config',return_value={'origin':origin}),
              patch.object(browser,'config',return_value={'enabled':True,'control':True}),
              patch.object(browser,'session_for',return_value=session),patch('hive.gateway.subprocess')):
            ticket = gateway.issue(self.ch,self.repo).split('#')[1]
            self.assertTrue(gateway.held(self.repo))
            with self.assertRaises(tools.Refused):
                browser.call(self.repo,'inspect',{})
            self.assertEqual(client.post('/exchange',content=ticket,headers={'origin':'https://other.invalid'}).status_code,403)
            resp = client.post('/exchange',content=ticket)
            self.assertEqual(resp.status_code,204)
            for flag in ('HttpOnly','Secure','SameSite=strict'):
                self.assertIn(flag,resp.headers['set-cookie'])
            cookie = resp.cookies[gateway.COOKIE]
            self.assertEqual(client.post('/exchange',content=ticket).status_code,403)
            gateway.revoke(self.ch,self.repo)
            self.assertIsNone(gateway.session_row(cookie))
            ticket = gateway.issue(self.ch,self.repo).split('#')[1]
            store.connect().execute('UPDATE browser_control SET ticket_until=0')
            self.assertEqual(client.post('/exchange',content=ticket).status_code,403)
            session.call.return_value={'data':{'url':'https://fixture.invalid/done'}}
            gateway.give_back(self.ch,self.repo)
            self.assertFalse(gateway.held(self.repo))

    def test_callback_state_connector_expiry_and_single_use(self):
        digest = gateway.hash_token('good')
        store.connect().execute('INSERT INTO oauth_callbacks VALUES(?,?,?,NULL)',(digest,'fixture',time.time()+30))
        with patch.dict(os.environ,{'HIVE_MASTER_KEY':'fixture-key'}):
            for name,state in [('other','good'),('fixture','bad')]:
                self.assertFalse(mcp_auth.callback(name,{'state':state,'code':'private-code'}))
            self.assertTrue(mcp_auth.callback('fixture',{'state':'good','code':'private-code'}))
            self.assertFalse(mcp_auth.callback('fixture',{'state':'good','code':'second'}))
        sealed=store.connect().execute('SELECT response FROM oauth_callbacks').fetchone()[0]
        self.assertNotIn(b'private-code',sealed)

    def test_sdk_rejects_unbound_login_and_tool_auth_never_replays(self):
        import httpx
        from mcp.shared.auth import OAuthToken
        entry = {'url':'https://fixture.invalid/mcp','oauth':'fixture','grant':'A'}
        async def exercise():
            auth = mcp_auth.provider(entry,True)
            with self.assertRaises(tools.Refused):
                await auth.context.redirect_handler('https://login.invalid/authorize?state=invalid')
            auth.context.current_tokens=OAuthToken(access_token='fixture',token_type='Bearer')
            req = httpx.Request('POST',entry['url'],json={'method':'tools/call'})
            flow = auth.async_auth_flow(req)
            attempt = await flow.asend(None)
            self.assertEqual(attempt.headers['Authorization'],'Bearer fixture')
            with self.assertRaises(StopAsyncIteration):
                await flow.asend(httpx.Response(401,request=req))
            auth.context.token_expiry_time=time.time()-1
            with self.assertRaises(tools.Refused):
                await auth.async_auth_flow(req).asend(None)
        with (patch.object(gateway,'config',return_value={'origin':'https://owner.invalid'}),
              patch('hive.connectors.config',return_value={'fixture':entry})):
            asyncio.run(exercise())

    def test_stdio_mount_excludes_home_and_host_socket(self):
        with self.assertRaises(tools.Refused):
            mcp_stdio.mount(Path.home())
        with self.assertRaises(tools.Refused):
            mcp_stdio.mount(Path.home().parent)
        sock = Path(self.temp.name)/'docker.sock'
        sock.touch()
        with self.assertRaises(tools.Refused):
            mcp_stdio.mount(sock)

    def test_sdk_discovery_pkce_exchange_and_refresh_are_resource_bound(self):
        import base64,hashlib
        import httpx
        from urllib.parse import parse_qs,urlsplit
        entry={'url':'https://reports.invalid/mcp','oauth':'fixture','grant':'A'}
        issuer='https://identity.invalid'
        token_forms=[]
        challenge=[]
        def serve(req):
            url=str(req.url)
            if url==entry['url']:
                if req.headers.get('authorization') in ('Bearer fixture-access','Bearer refreshed'):
                    return httpx.Response(200,json={})
                return httpx.Response(401,headers={'WWW-Authenticate':
                    'Bearer resource_metadata="https://reports.invalid/.well-known/oauth-protected-resource/mcp"'})
            if 'oauth-protected-resource' in url:
                return httpx.Response(200,json={'resource':entry['url'],'authorization_servers':[issuer]})
            if '.well-known/' in url:
                return httpx.Response(200,json={'issuer':issuer,'authorization_endpoint':issuer+'/authorize',
                    'token_endpoint':issuer+'/token','registration_endpoint':issuer+'/register',
                    'response_types_supported':['code'],'code_challenge_methods_supported':['S256']})
            if url.endswith('/register'):
                return httpx.Response(201,json=dict(json.loads(req.content),client_id='fixture-client'))
            if url.endswith('/token'):
                form=parse_qs(req.content.decode())
                self.assertEqual(form['resource'],[entry['url']])
                token_forms.append(form)
                if form['grant_type']==['authorization_code']:
                    encoded=base64.urlsafe_b64encode(hashlib.sha256(form['code_verifier'][0].encode()).digest()).decode().rstrip('=')
                    self.assertEqual(encoded,challenge[0])
                    self.assertEqual(form['code'],['fixture-code'])
                return httpx.Response(200,json={'access_token':'fixture-access' if len(token_forms)==1 else 'refreshed',
                    'refresh_token':'private-refresh','token_type':'Bearer','expires_in':120})
            return httpx.Response(404)
        def sign_in(message,**kwargs):
            parts=parse_qs(urlsplit(message.splitlines()[-1]).query)
            challenge.extend(parts['code_challenge'])
            self.assertTrue(mcp_auth.callback('fixture',{'state':parts['state'][0],'code':'fixture-code'}))
        async def run():
            async with httpx.AsyncClient(transport=httpx.MockTransport(serve)) as client:
                response=await client.get(entry['url'],auth=mcp_auth.provider(entry,True))
                self.assertEqual(response.status_code,200)
                grant=mcp_auth.Grant(entry)
                raw=Path(grant.path).read_text()
                self.assertNotIn('private-refresh',raw)
                saved=grant.load()
                saved['expires']=time.time()-5
                from hive import vault
                vault.save_json(grant.path,saved)
                self.assertEqual((await client.get(entry['url'],auth=mcp_auth.provider(entry))).status_code,200)
        with (patch.object(gateway,'config',return_value={'origin':'https://owner.invalid'}),
              patch.dict(os.environ,{'HIVE_MASTER_KEY':'fixture-key'}),patch('builtins.print',side_effect=sign_in)):
            asyncio.run(run())
        self.assertEqual([f['grant_type'][0] for f in token_forms],['authorization_code','refresh_token'])


if __name__=='__main__':
    unittest.main()
