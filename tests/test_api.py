from fastapi.testclient import TestClient
from dualgpuopt.serve.legal_api import app, api_tokens

def _add_tmp_token():
    tok = "test_token"
    api_tokens[tok] = 9999999999
    return tok

client = TestClient(app)

def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] in ("ok", "unavailable")

def test_auth_and_rate_limit(monkeypatch):
    tok = _add_tmp_token()
    headers = {"X-API-Key": tok}
    # first call should work (model may be unavailable => 503 but not 401/429)
    r1 = client.post("/api/chat", headers=headers,
                     json={"prompt":"bonjour", "use_rag":False})
    assert r1.status_code in (200,503)

    # exceed tiny limit by monkey‑patching RATE_LIMIT
    from dualgpuopt.serve import legal_api
    monkeypatch.setattr(legal_api, "RATE_LIMIT", 1)
    r2 = client.post("/api/chat", headers=headers,
                     json={"prompt":"encore", "use_rag":False})
    assert r2.status_code == 429 