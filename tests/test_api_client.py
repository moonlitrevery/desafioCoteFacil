"""Testes para api_client (signup, token, produto, pedido)."""
import os

import pytest
import responses

# Importar após eventual ajuste de path
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api_client import (
    get_base_url,
    get_token,
    patch_pedido,
    post_pedido,
    post_produtos,
    signup,
)


def test_get_base_url_from_env(monkeypatch):
    monkeypatch.delenv("DESAFIO_API_URL", raising=False)
    assert "desafio.cotefacil.net" in get_base_url()
    monkeypatch.setenv("DESAFIO_API_URL", "https://api.test.com/")
    assert get_base_url() == "https://api.test.com"


@responses.activate
def test_signup(api_base):
    responses.add(
        responses.POST,
        f"{api_base}/oauth/signup",
        json={"message": "ok"},
        status=200,
    )
    result = signup("user1", "password123", base_url=api_base)
    assert result == {"message": "ok"}
    req = responses.calls[0].request
    assert req.headers["Content-Type"] == "application/json"
    import json
    body = json.loads(req.body)
    assert body["username"] == "user1"
    assert body["password"] == "password123"


@responses.activate
def test_get_token(api_base):
    responses.add(
        responses.POST,
        f"{api_base}/oauth/token",
        json={"access_token": "abc123", "token_type": "bearer", "expires_in": 3600},
        status=200,
    )
    token = get_token("user1", "pass1", base_url=api_base)
    assert token == "abc123"


@responses.activate
def test_post_produtos(api_base):
    responses.add(
        responses.POST,
        f"{api_base}/produto",
        json=[{"gtin": "123", "codigo": "A1"}],
        status=201,
    )
    result = post_produtos(
        [{"gtin": "123", "codigo": "A1", "descricao": "Prod", "preco_fabrica": 10.5, "estoque": 2}],
        token="abc",
        base_url=api_base,
    )
    assert len(result) == 1
    assert result[0]["gtin"] == "123"
    req = responses.calls[0].request
    assert "Bearer abc" in req.headers.get("Authorization", "")


@responses.activate
def test_post_pedido(api_base):
    responses.add(
        responses.POST,
        f"{api_base}/pedido",
        json={
            "id": 42,
            "codigo_fornecedor": None,
            "status": None,
            "itens": [
                {"gtin": "1234567890123", "codigo": "A123", "quantidade": 1},
            ],
        },
        status=201,
    )
    result = post_pedido(token="xyz", base_url=api_base)
    assert result["id"] == 42
    assert len(result["itens"]) == 1
    assert result["itens"][0]["codigo"] == "A123"


@responses.activate
def test_patch_pedido(api_base):
    responses.add(
        responses.PATCH,
        f"{api_base}/pedido/42",
        json={
            "id": 42,
            "codigo_fornecedor": "ABC987",
            "status": "pedido_realizado",
            "itens": [],
        },
        status=200,
    )
    result = patch_pedido(
        id_pedido=42,
        codigo_confirmacao="ABC987",
        status="pedido_realizado",
        token="tok",
        base_url=api_base,
    )
    assert result["codigo_fornecedor"] == "ABC987"
    assert result["status"] == "pedido_realizado"
    req = responses.calls[0].request
    import json
    body = json.loads(req.body)
    assert body["codigo_confirmacao"] == "ABC987"
    assert body["status"] == "pedido_realizado"
