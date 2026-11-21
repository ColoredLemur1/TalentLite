from app.middleware import SECURITY_HEADERS


def _assert_security_headers(response):
    for name, value in SECURITY_HEADERS.items():
        assert response.headers.get(name) == value, name


def test_health_with_key_returns_200_ok(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_security_headers_on_200(client):
    r = client.get("/health")
    assert r.status_code == 200
    _assert_security_headers(r)


def test_security_headers_on_401(anon_client):
    r = anon_client.get("/health")
    assert r.status_code == 401
    _assert_security_headers(r)


def test_security_headers_on_404(client):
    r = client.get("/nope")
    assert r.status_code == 404
    _assert_security_headers(r)
