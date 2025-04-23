from dualgpuopt.ingest.clean_html import clean_html

def test_basic_strip():
    raw = "<html><head><style>p{}</style></head><body><h1>Hi</h1><script>x</script>\n<p>Art&nbsp;1&nbsp;C.c.Q.</p></body></html>"
    txt = clean_html(raw)
    assert txt == "Hi\nArt 1 C.c.Q." 