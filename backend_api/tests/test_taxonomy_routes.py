import pytest

@pytest.mark.pg_required
def test_get_taxonomy_tree(client):
    r = client.get("/taxonomy")
    assert r.status_code == 200
    tree = r.json()
    # OpenAPI suggests array of objects
    assert isinstance(tree, list)

@pytest.mark.pg_required
def test_post_mapping_validation_and_success(client):
    # Mapping requires an existing job for path param but logic uses only job existence
    # Upload first to create job
    import io
    data = io.BytesIO(b"Hello")
    r = client.post("/uploads", files={"file": ("x.txt", data, "text/plain")})
    assert r.status_code == 200
    jid = r.json()["id"]

    # Missing payload field -> 422
    r2 = client.post(f"/jobs/{jid}/taxonomy/map", json={})
    assert r2.status_code == 422

    # Provide minimal mapping payload
    r3 = client.post(f"/jobs/{jid}/taxonomy/map", json={"raw_value": "AppOne", "l1_id": None, "l2_id": None, "l3_id": None})
    assert r3.status_code == 200
    body = r3.json()
    assert body.get("ok") is True
    assert "mapping_id" in body
