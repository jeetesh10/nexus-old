import os
import time
import uuid
import requests

BASE = os.getenv("ORCH_URL", "http://127.0.0.1:8080")
MONGO_DB = os.getenv("MONGO_DB", "nexus")


def wait_for_health(url: str, timeout: int = 30) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            r = requests.get(f"{url}/health", timeout=2)
            if r.status_code == 200 and r.json().get("status") == "ok":
                return
        except requests.RequestException:
            pass
        time.sleep(0.5)
    raise RuntimeError("orchestrator health check failed to become healthy")


def test_full_crud_lifecycle_and_query():
    # wait for app + mongo to be ready
    wait_for_health(BASE)

    coll = f"test_collection_{uuid.uuid4().hex[:8]}"
    payload = {"data": {"created_by": "orchestrator-test", "note": "make nexus visible"}}

    # Create
    r = requests.post(f"{BASE}/{coll}", json=payload, timeout=5)
    assert r.status_code == 201, r.text
    created = r.json()
    assert "id" in created
    created_id = created["id"]

    # Get
    r = requests.get(f"{BASE}/{coll}/{created_id}", timeout=5)
    assert r.status_code == 200, r.text
    doc_resp = r.json()
    assert doc_resp["id"] == created_id
    # document should contain the stored data
    assert doc_resp["document"].get("created_by") == "orchestrator-test"

    # Update
    upd = {"data": {"note": "updated"}}
    r = requests.put(f"{BASE}/{coll}/{created_id}", json=upd, timeout=5)
    assert r.status_code == 200, r.text
    assert r.json()["document"]["note"] == "updated"

    # Query
    q = {"filter": {}, "limit": 10}
    r = requests.post(f"{BASE}/{coll}/query", json=q, timeout=5)
    assert r.status_code == 200, r.text
    body = r.json()
    assert "results" in body and isinstance(body["results"], list)
    assert any((created_id == (doc.get("_id") or doc.get("id"))) or doc.get("created_by") == "orchestrator-test" for doc in body["results"])

    # Collections list should include our collection
    r = requests.get(f"{BASE}/collections", timeout=5)
    assert r.status_code == 200, r.text
    names = r.json().get("collections", [])
    assert coll in names

    # Delete
    r = requests.delete(f"{BASE}/{coll}/{created_id}", timeout=5)
    assert r.status_code == 204, r.text

    # Ensure deleted
    r = requests.get(f"{BASE}/{coll}/{created_id}", timeout=5)
    assert r.status_code == 404


def test_info_endpoint():
    wait_for_health(BASE)
    r = requests.get(f"{BASE}/info", timeout=5)
    assert r.status_code == 200
    body = r.json()
    assert body.get("db") == MONGO_DB
    assert "uri" in body