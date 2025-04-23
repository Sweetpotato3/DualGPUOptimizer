import json

import faiss
import numpy as np

from dualgpuopt.rag.retrieve import LegalRetriever


def _dummy_faiss(tmp_path):
    dim = 384
    idx = faiss.IndexFlatIP(dim)
    vecs = np.zeros((8, dim), dtype="float32")
    for i in range(8):
        vecs[i, i % dim] = 1.0  # Each vector has a 1.0 in a different position
    idx.add(vecs)
    fidx = tmp_path / "mini.faiss"
    faiss.write_index(idx, str(fidx))
    with open(str(fidx) + ".meta.json", "w") as fh:
        for i in range(8):
            fh.write(json.dumps({"id": i, "text": f"doc{i}", "source": "test"}) + "\n")
    return fidx


def test_retrieval(tmp_path, monkeypatch):
    fidx = _dummy_faiss(tmp_path)
    # monkey‑patch sentence_transformer.encode to deterministic unit vecs
    import sentence_transformers

    class DummyModel:
        def get_sentence_embedding_dimension(self):
            return 384

        def encode(self, qs, **k):
            v = np.zeros(384, dtype="float32")
            v[0] = 1.0
            return v

    monkeypatch.setattr(
        sentence_transformers, "SentenceTransformer", lambda *_a, **_k: DummyModel()
    )
    retr = LegalRetriever(str(fidx), device="cpu")
    res = retr.retrieve("anything", k=2, threshold=-1.0)
    
    # We need at least one result
    assert len(res) >= 1
    
    # The first result should have text and citation
    assert "text" in res[0]
    assert "citation" in res[0]
    assert "source" in res[0]
    assert res[0]["source"] == "test"
