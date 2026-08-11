from shesh_messaging.server import list_bridges, send_telegram, enable_bridge, disable_bridge

def test_list():
    res = list_bridges()
    assert "telegram" in res

def test_send_disabled():
    res = send_telegram("123", "hello")
    assert res["ok"] is False  # not enabled by default

def test_enable_disable():
    enable_bridge("telegram")
    res = list_bridges()
    assert res["telegram"]["enabled"] is True
    disable_bridge("telegram")
    res = list_bridges()
    assert res["telegram"]["enabled"] is False
