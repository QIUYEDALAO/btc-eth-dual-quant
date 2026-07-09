# Freqtrade WebUI On VPS

The current M1F deployment does not start live trading. WebUI is only for
future local research checks.

Rules:

- Bind WebUI only to `127.0.0.1` on the VPS.
- Do not expose port 8080 publicly.
- Access through SSH tunnel:

```bash
ssh -L 8080:127.0.0.1:8080 $VPS_HOST
```

Then open:

```text
http://127.0.0.1:8080
```

Do not configure real exchange API keys. Do not use dry-run with real API
credentials. Do not run live mode.
