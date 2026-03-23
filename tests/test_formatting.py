from vibecode_b24_bot.formatting import bb


def test_bold():
    assert bb.bold("test") == "[b]test[/b]"


def test_italic():
    assert bb.italic("test") == "[i]test[/i]"


def test_underline():
    assert bb.underline("test") == "[u]test[/u]"


def test_strike():
    assert bb.strike("test") == "[s]test[/s]"


def test_code():
    assert bb.code("x = 1") == "[code]x = 1[/code]"


def test_link_bare():
    assert bb.link("https://example.com") == "[url]https://example.com[/url]"


def test_link_with_text():
    assert bb.link("https://example.com", "Click") == "[url=https://example.com]Click[/url]"


def test_quote():
    assert bb.quote("hello") == "[quote]hello[/quote]"


def test_list():
    assert bb.list(["a", "b", "c"]) == "[list][*]a[*]b[*]c[/list]"


def test_list_empty():
    assert bb.list([]) == "[list][/list]"


def test_mention():
    assert bb.mention(42) == "[user=42][/user]"


def test_strip():
    assert bb.strip("[b]bold[/b] and [i]italic[/i]") == "bold and italic"


def test_strip_with_attrs():
    assert bb.strip("[url=https://x.com]link[/url]") == "link"


def test_strip_nested():
    assert bb.strip("[b][i]nested[/i][/b]") == "nested"
