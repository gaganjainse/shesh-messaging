"""MCP server — messaging bridges Telegram/Signal isolated opt-in."""

from __future__ import annotations

import os
import pathlib

try:
    from shesh_audit.mcp_guard import GuardedMCP as FastMCP
except ImportError:
    from fastmcp import FastMCP

mcp = FastMCP("shesh-messaging")

BRIDGE_DIR = pathlib.Path.home() / ".config/shesh/messaging"

def _is_enabled(bridge: str) -> bool:
    flag = BRIDGE_DIR / f"{bridge}.enabled"
    return flag.exists()

@mcp.tool()
def list_bridges() -> dict:
    """List messaging bridges and whether enabled."""
    return {
        "telegram": {"enabled": _is_enabled("telegram"), "needs": "TELEGRAM_BOT_TOKEN via shesh-secrets"},
        "signal": {"enabled": _is_enabled("signal"), "needs": "signal-cli + SIGNAL account"},
        "note": "Bridges are isolated opt-in, create flag file ~/.config/shesh/messaging/{telegram,signal}.enabled to enable",
    }

def _get_token() -> str | None:
    """TELEGRAM_BOT_TOKEN via shesh-secrets, else plain environment."""
    try:
        from shesh_secrets import get_secret  # type: ignore

        try:
            token = get_secret("env:TELEGRAM_BOT_TOKEN")
            if token:
                return token
        except (OSError, KeyError, RuntimeError):
            pass
    except ImportError:
        pass
    return os.environ.get("TELEGRAM_BOT_TOKEN")


def _telegram_api(token: str, method: str, payload: dict, timeout: int = 10) -> dict:
    """Call the Telegram Bot API. The token only ever lives in the URL path
    of an in-memory request — never in logs, errors, or the return value."""
    import json
    import urllib.error
    import urllib.request

    req = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/{method}",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="replace")[:200]
        raise RuntimeError(f"telegram HTTP {exc.code}: {detail}") from exc
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"telegram request failed: {exc}") from exc


@mcp.tool()
def send_telegram(chat_id: str, message: str) -> dict:
    """Send a real Telegram message via the Bot API.

    Requires the bridge flag and TELEGRAM_BOT_TOKEN (shesh-secrets or env).
    """
    if not _is_enabled("telegram"):
        return {"ok": False, "error": "telegram bridge not enabled — create ~/.config/shesh/messaging/telegram.enabled"}
    token = _get_token()
    if not token:
        return {"ok": False, "error": "TELEGRAM_BOT_TOKEN not found (shesh-secrets env:TELEGRAM_BOT_TOKEN or environment)"}
    try:
        resp = _telegram_api(token, "sendMessage", {"chat_id": chat_id, "text": message})
    except RuntimeError as exc:
        return {"ok": False, "error": str(exc)}
    result = resp.get("result", {})
    return {
        "ok": bool(resp.get("ok")),
        "chat_id": chat_id,
        "message_id": result.get("message_id"),
        "date": result.get("date"),
    }


@mcp.tool()
def send_signal(recipient: str, message: str) -> dict:
    """Send a real Signal message via signal-cli (must be installed+registered)."""
    if not _is_enabled("signal"):
        return {"ok": False, "error": "signal bridge not enabled — create ~/.config/shesh/messaging/signal.enabled"}
    import shutil
    import subprocess

    cli = shutil.which("signal-cli")
    if not cli:
        return {"ok": False, "error": "signal-cli not installed"}
    account = _get_signal_account()
    if not account:
        return {"ok": False, "error": "SIGNAL_ACCOUNT not configured (shesh-secrets env:SIGNAL_ACCOUNT or environment)"}
    try:
        proc = subprocess.run(
            [cli, "-a", account, "send", "-m", message, recipient],
            capture_output=True, text=True, timeout=30, check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return {"ok": False, "error": f"signal-cli failed: {exc}"}
    if proc.returncode != 0:
        return {"ok": False, "error": f"signal-cli exit {proc.returncode}: {proc.stderr.strip()[:200]}"}
    return {"ok": True, "recipient": recipient, "sent": True}


def _get_signal_account() -> str | None:
    try:
        from shesh_secrets import get_secret  # type: ignore

        try:
            account = get_secret("env:SIGNAL_ACCOUNT")
            if account:
                return account
        except (OSError, KeyError, RuntimeError):
            pass
    except ImportError:
        pass
    return os.environ.get("SIGNAL_ACCOUNT")

@mcp.tool()
def enable_bridge(bridge: str) -> dict:
    """Enable a bridge by creating flag file (requires user confirmation in real use)."""
    if bridge not in ("telegram", "signal"):
        return {"ok": False, "error": "unknown bridge, use telegram or signal"}
    BRIDGE_DIR.mkdir(parents=True, exist_ok=True)
    flag = BRIDGE_DIR / f"{bridge}.enabled"
    flag.write_text("enabled\n")
    return {"ok": True, "bridge": bridge, "flag": str(flag)}

@mcp.tool()
def disable_bridge(bridge: str) -> dict:
    """Disable a bridge."""
    flag = BRIDGE_DIR / f"{bridge}.enabled"
    if flag.exists():
        flag.unlink()
    return {"ok": True, "bridge": bridge, "disabled": True}

def main() -> None:
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()
