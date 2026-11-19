# Owner control gateway

The listener serves an optional gateway on loopback. Configure an HTTPS hostname on
your own host, point DNS at your reverse proxy and install the extras in the listener's
Python environment.

```sh
python -m pip install -e ".[gateway,mcp]"
hive browser setup
hive browser setup-control
hive browser enable
hive gateway configure https://hive.example.org --port 8791
```

A Caddy site on the same host can forward HTTP and WebSocket traffic over loopback.
Replace the example hostname with your own.

```caddyfile
hive.example.org {
    reverse_proxy 127.0.0.1:8791
}
```

Restart `hive listen` and run `hive gateway check` from a machine that can reach the
public hostname with a trusted certificate. The proxy must preserve Host and Origin.
Disable request-body and callback-query logging in the proxy. Hive disables gateway
access logs. Expose only the HTTPS proxy port.

## Phone sign-in

Send `browser takeover <task-id>` in the owner's Telegram chat. Open the button within
two minutes. The one-time secret lives in the URL fragment and is exchanged for a
Secure, HttpOnly, SameSite cookie. The session lasts ten minutes. The mobile view
has a phone keyboard input for remote text and a **Return control to Hive** button.
The browser runs headed Chromium on a virtual display inside the private browser
container. Each noVNC connection uses a private socket pair over Docker exec.

While the owner has control Hive refuses browser tool calls. Return control after
sign-in. Hive checks the current page before resuming an eligible task. A page still
showing a login prompt requires another takeover. Telegram also accepts `revoke browser`
to invalidate the link and session and `return browser` to hand control back.
Expired or revoked sessions leave automation paused. Browser profiles stay on this host.

## MCP credentials

```sh
hive mcp add reports https://reports.example.org/mcp --oauth --read-tool search
hive mcp login reports
```

Open the authorization URL printed by the login command. The server must support
protected-resource discovery and client registration. The installed MCP SDK handles
PKCE, resource selection and token exchange. The callback binds state to the configured
connector. Grants and client registration information are encrypted with Hive's vault.
Each explicit login changes the connector binding and invalidates prior tool decisions.
Token refresh occurs during read-only protocol traffic. A failed tool call requires
outcome inspection.

For a Docker stdio server, pull the image on the listener host and register it by
image name. Hive binds the resolved image ID, the argument array and the selected
environment credentials and read-only mounts to the connector.

```sh
hive mcp add-stdio catalog my-catalog:1 --args '["serve","--stdio"]' --env CATALOG_TOKEN --mount /srv/hive-inputs/catalog --read-tool search
```

The first selected mount appears as `/inputs/0` in the container. The runtime uses
a non-root user, a read-only root filesystem, a temporary directory and disabled
networking. The host home and Docker socket are excluded. Leave tools off the read
list when their execution may have side effects.
