from bs4 import BeautifulSoup
from pathlib import Path
import json
import re
import sys

def clean_file(fp: Path) -> str:
    soup = BeautifulSoup(fp.read_text(encoding='utf-8'), 'lxml')
    for tag in soup(['script','style','header','footer','nav']): tag.decompose()
    text = re.sub(r"\s+", " ", soup.get_text(" ", strip=True))
    return text

if __name__ == "__main__":
    raw_dir, out = Path(sys.argv[1]), Path(sys.argv[2])
    out.open('w').write('')
    with out.open('a', encoding='utf-8') as fh:
        for fp in raw_dir.rglob('*.htm*'):
            txt = clean_file(fp)
            fh.write(json.dumps({'text': txt}, ensure_ascii=False)+'\n') 