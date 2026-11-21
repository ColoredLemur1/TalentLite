"""POST /candidates and GET /candidates/{id}: every input limit, duplicates and no data leaks."""

import json
import logging
import re

from app.db import connect, insert_candidate
from tests.helpers import candidate_payload as p

ISO_UTC = re.compile(r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$")


def _create(client, **overrides):
    return client.post("/candidates", json=p(**overrides))


def _assert_422(r):
    assert r.status_code == 422, r.text
    assert r.json()["error"]["code"] == "validation_error"


# --- Create and read ---------------------------------------------------------


def test_create_candidate_returns_201_with_normalized_email(client):
    r = _create(client, email=" Ana.Torres@Example.COM ")
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["email"] == "ana.torres@example.com"
    assert body["latest_analysis"] is None


def test_get_candidate_returns_same_data(client):
    created = _create(client).json()
    r = client.get(f"/candidates/{created['id']}")
    assert r.status_code == 200
    assert r.json() == created


def test_get_missing_candidate_returns_404(client):
    r = client.get("/candidates/999")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "not_found"


def test_get_candidate_non_integer_id_returns_422(client):
    _assert_422(client.get("/candidates/abc"))


def test_get_candidate_zero_or_negative_id_returns_422(client):
    _assert_422(client.get("/candidates/0"))
    _assert_422(client.get("/candidates/-1"))


def test_get_candidate_id_above_int64_returns_422_not_500(client):
    _assert_422(client.get(f"/candidates/{2**63}"))


def test_get_candidate_has_exactly_the_brief_fields(client):
    created = _create(client).json()
    r = client.get(f"/candidates/{created['id']}")
    assert set(r.json()) == {
        "id",
        "name",
        "email",
        "cv_text",
        "created_at",
        "latest_analysis",
    }


def test_created_at_is_utc_iso8601(client):
    assert ISO_UTC.match(_create(client).json()["created_at"])


# --- cv_text -----------------------------------------------------------------


def test_cv_exactly_20000_chars_returns_201(client):
    assert _create(client, cv_text="a" * 20000).status_code == 201


def test_cv_20001_chars_returns_422(client):
    _assert_422(_create(client, cv_text="a" * 20001))


def test_cv_20000_multibyte_chars_returns_201(client):
    assert _create(client, cv_text="ñ" * 20000).status_code == 201


def test_cv_empty_returns_422(client):
    _assert_422(_create(client, cv_text=""))


def test_cv_whitespace_only_returns_422(client):
    _assert_422(_create(client, cv_text="   \n "))


def test_cv_is_stored_unstripped(client):
    created = _create(client, cv_text=" CV ")
    assert created.status_code == 201, created.text
    r = client.get(f"/candidates/{created.json()['id']}")
    assert r.json()["cv_text"] == " CV "


def test_cv_with_control_chars_roundtrips(client):
    cv = "línea1\r\n\tlínea2\x00fin"
    created = _create(client, cv_text=cv)
    assert created.status_code == 201, created.text
    r = client.get(f"/candidates/{created.json()['id']}")
    assert r.json()["cv_text"] == cv


# --- name --------------------------------------------------------------------


def test_name_empty_or_whitespace_returns_422(client):
    _assert_422(_create(client, name=""))
    _assert_422(_create(client, name="   "))


def test_name_100_chars_ok_101_returns_422(client):
    assert _create(client, name="a" * 100).status_code == 201
    _assert_422(_create(client, name="a" * 101, email="otra@example.com"))


def test_name_is_stored_stripped(client):
    assert _create(client, name="  Ana  ").json()["name"] == "Ana"


def test_unicode_name_roundtrip(client):
    created = _create(client, name="Zoë Ñúñez 李").json()
    r = client.get(f"/candidates/{created['id']}")
    assert r.json()["name"] == "Zoë Ñúñez 李"


def test_sql_like_name_stored_literally(client):
    name = "Robert'); DROP TABLE candidates;--"
    created = _create(client, name=name)
    assert created.status_code == 201
    r = client.get(f"/candidates/{created.json()['id']}")
    assert r.json()["name"] == name
    assert _create(client, email="otra@example.com").status_code == 201


# --- email -------------------------------------------------------------------


def test_invalid_email_returns_422(client):
    for email in ["not-an-email", "a@", "@b.com", "a b@c.com"]:
        _assert_422(_create(client, email=email))


def test_email_254_chars_returns_201(client):
    email = "a" * 64 + "@" + "b" * 63 + "." + "c" * 63 + "." + "d" * 57 + ".com"
    assert len(email) == 254
    assert _create(client, email=email).status_code == 201


def test_email_255_chars_returns_422(client):
    email = "a" * 64 + "@" + "b" * 63 + "." + "c" * 63 + "." + "d" * 58 + ".com"
    assert len(email) == 255
    _assert_422(_create(client, email=email))


def test_422_does_not_echo_submitted_email(client):
    r = _create(client, email="pii-marker@@x")
    _assert_422(r)
    assert "pii-marker" not in r.text


# --- Body shape --------------------------------------------------------------


def test_extra_field_returns_422(client):
    _assert_422(client.post("/candidates", json={**p(), "role": "admin"}))


def test_missing_field_returns_422(client):
    body = p()
    del body["cv_text"]
    _assert_422(client.post("/candidates", json=body))


def test_wrong_type_returns_422(client):
    _assert_422(_create(client, name=123))


def test_body_not_json_returns_422(client):
    r = client.post(
        "/candidates", content=b"{bad", headers={"Content-Type": "application/json"}
    )
    _assert_422(r)


def test_body_json_array_returns_422(client):
    _assert_422(client.post("/candidates", json=[p()]))


def test_non_json_content_type_returns_422(client):
    r = client.post(
        "/candidates",
        content=json.dumps(p()).encode(),
        headers={"Content-Type": "text/plain"},
    )
    _assert_422(r)


# --- Duplicates --------------------------------------------------------------


def test_duplicate_email_returns_409(client):
    assert _create(client).status_code == 201
    r = _create(client)
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "conflict"


def test_duplicate_email_different_case_and_spaces_returns_409(client):
    assert _create(client).status_code == 201
    assert _create(client, email=" ANA.TORRES@example.com").status_code == 409


def test_duplicate_inserted_directly_returns_409(client, settings):
    conn = connect(settings.database_path)
    try:
        insert_candidate(
            conn, name="Ana Torres", email="ana.torres@example.com", cv_text="CV"
        )
    finally:
        conn.close()
    assert _create(client).status_code == 409


def test_409_body_does_not_echo_email(client):
    _create(client)
    r = _create(client)
    assert r.status_code == 409
    assert "ana.torres" not in r.text


# --- Logs --------------------------------------------------------------------


def test_create_candidate_logs_no_personal_data(client, caplog):
    payload = p()
    with caplog.at_level(logging.DEBUG):
        r = client.post("/candidates", json=payload)
    assert r.status_code == 201
    for value in payload.values():
        assert value not in caplog.text
