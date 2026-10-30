import pytest

from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_hello_responde_200(client):
    response = client.get("/hello?name=TEST")
    assert response.status_code == 200


def test_hello_saluda_con_el_nombre(client):
    response = client.get("/hello?name=TEST")
    assert response.get_data(as_text=True) == "Hello, TEST!"


def test_hello_sin_nombre(client):
    response = client.get("/hello")
    assert response.get_data(as_text=True) == "Hello, None!"


@pytest.mark.xfail(strict=True, reason="Vulnerabilidad conocida: XSS reflejado, la entrada no se escapa")
def test_hello_escapa_html(client):
    payload = "<script>alert(1)</script>"
    response = client.get("/hello", query_string={"name": payload})
    assert payload not in response.get_data(as_text=True)
