# VPS Security Hardening Notes

Recommended hardening for the M1F research server:

- Disable password login after SSH key access is confirmed.
- Use a non-root deploy user for routine operation.
- Enable UFW and allow only SSH.
- Do not open Freqtrade WebUI ports to the public internet.
- Use SSH tunnel or VPN for WebUI.
- Do not save exchange API keys on the server.
- Do not save withdrawal-enabled exchange keys.
- Run `apt update && apt upgrade` regularly.
- Keep Docker limited to this local research/backtest environment.
- This server is not a live trading environment.
- This project stage is Freqtrade feasibility only.
