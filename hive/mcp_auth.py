"""SDK OAuth authorization on read-only discovery, with a single transmission per tool call."""
import asyncio
import json
import time
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from . import gateway, store, tools, vault


class Grant:
    def __init__(self, entry):
        key = gateway.hash_token(json.dumps([entry['url'],entry['oauth'],entry['grant']],sort_keys=True))
        self.path = str(Path(gateway.cfg_path()).parent/'mcp-grants'/(key+'.json'))
        self.provider = None

    def load(self):
        return vault.load_json(self.path,{})

    async def get_tokens(self):
        from mcp.shared.auth import OAuthToken
        data = self.load()
        if data.get('tokens'):
            return OAuthToken.model_validate(data['tokens'])

    async def set_tokens(self,tokens):
        ctx = self.provider.context
        if not ctx.protected_resource_metadata:
            raise tools.Refused('The authorization server did not identify the protected resource.')
        with store.transaction():
            data = self.load()
            data.update(tokens=tokens.model_dump(mode='json'),issuer=ctx.auth_server_url,
                        resource=ctx.protected_resource_metadata.model_dump(mode='json'),
                        metadata=ctx.oauth_metadata.model_dump(mode='json'),expires=time.time()+tokens.expires_in
                        if tokens.expires_in is not None else None)
            vault.save_json(self.path,data)

    async def get_client_info(self):
        from mcp.shared.auth import OAuthClientInformationFull
        data = self.load().get('client')
        return OAuthClientInformationFull.model_validate(data) if data else None

    async def set_client_info(self,info):
        with store.transaction():
            data = self.load()
            data['client'] = info.model_dump(mode='json')
            vault.save_json(self.path,data)


def callback(name, params):
    state, code = params.get('state',''), params.get('code','')
    if not state or not code or len(state)>256 or len(code)>8192:
        return False
    digest = gateway.hash_token(state)
    with store.transaction() as con:
        row = con.execute('SELECT 1 FROM oauth_callbacks WHERE state_hash=? AND connector=? AND expires>? AND response IS NULL',
                          (digest,name,time.time())).fetchone()
        if not row:
            return False
        sealed = vault._fernet_cls()(vault._key()).encrypt(code.encode())
        con.execute('UPDATE oauth_callbacks SET response=? WHERE state_hash=?',(sealed,digest))
        return True


def provider(entry, interactive=False):
    from mcp.client.auth import OAuthClientProvider
    from mcp.shared.auth import OAuthClientMetadata, OAuthMetadata, ProtectedResourceMetadata
    grant = Grant(entry)
    cfg = gateway.config()
    if not cfg:
        raise tools.Refused('Configure the HTTPS callback gateway before MCP login.')
    name = entry['oauth']
    callback_url = cfg['origin']+'/oauth/'+name
    state = None
    async def redirect(url):
        nonlocal state
        if not interactive:
            raise tools.Refused('A fresh connector login is required.')
        auth = urlsplit(url)
        q = parse_qs(auth.query)
        if (auth.scheme!='https' or q.get('code_challenge_method')!=['S256'] or not q.get('code_challenge')
                or q.get('resource')!=[client.context.get_resource_url()] or q.get('redirect_uri')!=[callback_url]
                or not client.context.protected_resource_metadata):
            raise tools.Refused('The authorization request lacks the protected resource or PKCE binding.')
        state = q['state'][0]
        store.connect().execute('INSERT INTO oauth_callbacks VALUES(?,?,?,NULL)',
                                (gateway.hash_token(state),name,time.time()+300))
        print('Open this authorization URL in your browser:\n'+url,flush=True)
    async def returned():
        digest = gateway.hash_token(state)
        try:
            while True:
                row = store.connect().execute('SELECT response FROM oauth_callbacks WHERE state_hash=? AND expires>?',
                                              (digest,time.time())).fetchone()
                if not row:
                    raise tools.Refused('The OAuth login expired.')
                if row[0]:
                    return vault._fernet_cls()(vault._key()).decrypt(row[0]).decode(),state
                await asyncio.sleep(.2)
        finally:
            store.connect().execute('DELETE FROM oauth_callbacks WHERE state_hash=?',(digest,))

    class ScopedProvider(OAuthClientProvider):
        async def _initialize(self):
            await super()._initialize()
            saved = grant.load()
            if saved.get('resource'):
                self.context.protected_resource_metadata = ProtectedResourceMetadata.model_validate(saved['resource'])
                self.context.oauth_metadata = OAuthMetadata.model_validate(saved['metadata'])
                self.context.auth_server_url = saved['issuer']
                self.context.token_expiry_time = saved.get('expires')

        async def async_auth_flow(self,request):
            body = await request.aread()
            payload = json.loads(body) if body and request.method=='POST' else {}
            if isinstance(payload,dict) and payload.get('method')=='tools/call':
                # SDK reauthentication on 401 can resend the request. A call has one wire attempt.
                from . import connectors
                current = connectors.config().get(name,{})
                if (not self.context.is_token_valid() or str(request.url)!=entry['url'] or
                        current.get('grant')!=entry['grant'] or current.get('url')!=entry['url']):
                    raise tools.Refused('The approved connector grant changed or expired.')
                self._add_auth_header(request)
                yield request
                return
            flow = super().async_auth_flow(request)
            response = None
            try:
                while True:
                    outbound = await flow.asend(response)
                    response = yield outbound
            except StopAsyncIteration:
                return
            finally:
                await flow.aclose()

    client = ScopedProvider(entry['url'],OAuthClientMetadata(client_name='Hive',redirect_uris=[callback_url],
                            token_endpoint_auth_method='none',grant_types=['authorization_code','refresh_token']),
                            grant,redirect,returned)
    grant.provider = client
    return client
