> ⚠️ **Consolidated into [shesh-core](https://github.com/gaganjainse/shesh-core)** — this module now lives in the shesh-core monorepo (same package name, same console script). Archived 2026-08-13.

# 💬 shesh-messaging

Messaging bridges — Telegram/Signal as isolated opt-in services.

- Part of [Shesh ecosystem](https://github.com/gaganjainse/shesh-ecosystem)
- Layer: Soma (body)
- Provides: telegram-bridge, signal-bridge
- Isolated: each bridge runs as separate systemd user service with its own account, opt-in, not enabled by default

## Tools
- `send_telegram` — send message via Telegram Bot API (needs TELEGRAM_BOT_TOKEN via shesh-secrets)
- `send_signal` — send via signal-cli (needs SIGNAL account)
- `list_bridges` — list enabled bridges

Security: bridges refuse to send secrets, protected paths, and require explicit opt-in `~/.config/shesh/messaging/{telegram,signal}.enabled` + token via shesh-secrets.

## Dev
```bash
uv sync && uv run pytest
```

## Security

Security posture and vulnerability reporting: [canonical ecosystem security
policy](https://github.com/gaganjainse/shesh-ecosystem/blob/main/SECURITY.md).
