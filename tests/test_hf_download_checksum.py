import hashlib, types, contextlib, io, pathlib, json
from unittest.mock import patch, MagicMock
from dualgpuopt.model import hf_client as hf

def _fake_meta(sha):
    meta = {"siblings":[{"rfilename":"file.safetensors","size":11,"sha256":sha}]}
    r = MagicMock(); r.json.return_value = meta; r.raise_for_status=lambda:None
    return r

class _FakeStream:
    def __init__(self, data): self.data=data
    def __enter__(self): return self
    def __exit__(self,*_): pass
    def iter_content(self, _): yield self.data
    def raise_for_status(self): pass

def test_checksum_mismatch(tmp_path):
    data = b"hello world"
    bad_sha = "deadbeef"*8
    good_sha = hashlib.sha256(data).hexdigest()
    # patch metadata (sha) & stream
    with patch("requests.get") as r:
        r.side_effect = [_fake_meta(bad_sha), _FakeStream(data)]
        dest = tmp_path/"d"
        try:
            hf.download("any","safetensors",dest)
        except RuntimeError as e:
            assert "mismatch" in str(e)
        else:
            assert False, "Expected checksum error"

def test_checksum_ok(tmp_path):
    data = b"hello ok!"
    sha = hashlib.sha256(data).hexdigest()
    with patch("requests.get") as r:
        r.side_effect = [_fake_meta(sha), _FakeStream(data)]
        dest = tmp_path/"d"
        out = hf.download("any","safetensors",dest)
        assert out.exists() and out.read_bytes()==data 