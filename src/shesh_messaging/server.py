"""MCP server — messaging bridges Telegram/Signal isolated opt-in."""

from __future__ import annotations

import pathlib

try:
    from shesh_audit.guard import GuardedMCP as FastMCP
except ImportError:
    from mcp.server.fastmcp import FastMCP

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

@mcp.tool()
def send_telegram(chat_id: str, message: str) -> dict:
    """Send Telegram message — requires TELEGRAM_BOT_TOKEN via shesh-secrets and enabled flag."""
    if not _is_enabled("telegram"):
        return {"ok": False, "error": "telegram bridge not enabled — create ~/.config/shesh/messaging/telegram.enabled"}
    # Try to get token via shesh-secrets if available
    try:
        from shesh_secrets import get_secret  # type: ignore
        token = get_secret("env:TELEGRAM_BOT_TOKEN")
    except Exception:
        token = None
    if not token:
        return {"ok": False, "error": "TELEGRAM_BOT_TOKEN not found via shesh-secrets"}
    # Would call Telegram Bot API here — stub for offline
    return {"ok": True, "chat_id": chat_id, "message": message[:100], "stub": True, "note": "would call https://api.telegram.org/bot{token}/sendMessage"}

@mcp.tool()
def send_signal(recipient: str, message: str) -> dict:
    """Send Signal message via signal-cli — requires signal-cli installed and enabled flag."""
    if not _is_enabled("signal"):
        return {"ok": False, "error": "signal bridge not enabled — create ~/.config/shesh/messaging/signal.enabled"}
    return {"ok": True, "recipient": recipient, "message": message[:100], "stub": True, "note": "would call signal-cli"}

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
