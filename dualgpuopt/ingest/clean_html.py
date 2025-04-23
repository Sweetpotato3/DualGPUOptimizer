from __future__ import annotations
import re
import html
import bs4
from pathlib import Path

SCRIPT_STYLE = ("script", "style", "noscript")

def clean_html(raw: str) -> str:
    soup = bs4.BeautifulSoup(raw, "lxml")
    for tag in soup(SCRIPT_STYLE):
        tag.decompose()
    text = soup.get_text(separator="\n")
    text = html.unescape(text)
    text = re.sub(r"\n{2,}", "\n", text)          # collapse blank lines
    text = re.sub(r"[ \t]+", " ", text).strip()
    return text

def clean_file(path: Path) -> str:
    return clean_html(path.read_text(encoding="utf-8", errors="ignore"))

if __name__ == "__main__":
    import sys
    import json
    root = Path(sys.argv[1])
    out  = Path(sys.argv[2])
    out.open("w").write(
        "\n".join(json.dumps({"text": clean_file(p)})
                  for p in root.rglob("*.html"))
    )
