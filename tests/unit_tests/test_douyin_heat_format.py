from agent.tools.douyin_analyze import format_heat


def test_format_heat_readable():
    assert format_heat(0) == "暂无指数"
    assert format_heat(None) == "暂无指数"
    assert format_heat(999) == "999"
    assert format_heat(15_000).endswith("万")
    assert format_heat(150_000_000).endswith("亿")
