"""
Cliente da API do desafio Cotefácil (Nível 2).
Autenticação OAuth e envio de produtos para /produto.
"""
import os
import requests


def get_base_url():
    """URL base da API (variável de ambiente DESAFIO_API_URL)."""
    url = os.environ.get("DESAFIO_API_URL", "https://api.desafio.cotefacil.com.br").rstrip("/")
    return url


def signup(email: str, password: str, base_url: str | None = None) -> dict:
    """
    Cria um usuário na API (POST /oauth/signup).
    Retorna o JSON da resposta. Faça isso uma vez antes de usar o worker.
    """
    base_url = base_url or get_base_url()
    r = requests.post(
        f"{base_url}/oauth/signup",
        json={"email": email, "password": password},
        headers={"Content-Type": "application/json"},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()


def get_token(username: str, password: str, base_url: str | None = None) -> str:
    """
    Obtém token de acesso (POST /oauth/token).
    Retorna o access_token para usar em Authorization: Bearer <token>.
    """
    base_url = base_url or get_base_url()
    # Formato comum OAuth2 password grant
    r = requests.post(
        f"{base_url}/oauth/token",
        data={
            "grant_type": "password",
            "username": username,
            "password": password,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=30,
    )
    r.raise_for_status()
    data = r.json()
    token = data.get("access_token") or data.get("token")
    if not token:
        raise ValueError("Resposta da API sem access_token: %s" % data)
    return token


def post_produtos(produtos: list[dict], token: str, base_url: str | None = None) -> dict:
    """
    Envia a lista de produtos para a API (POST /produto).
    produtos: lista de dicts com gtin, codigo, descricao, preco_fabrica (número), estoque (número).
    Retorna o JSON da resposta.
    """
    base_url = base_url or get_base_url()
    payload = _normalize_produtos(produtos)
    r = requests.post(
        f"{base_url}/produto",
        json=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        },
        timeout=60,
    )
    r.raise_for_status()
    return r.json()


def _normalize_produtos(produtos: list[dict]) -> list[dict]:
    """Garante gtin/codigo/descricao como string e preco_fabrica/estoque como número."""
    out = []
    for p in produtos:
        out.append({
            "gtin": str(p.get("gtin", "")),
            "codigo": str(p.get("codigo", "")),
            "descricao": str(p.get("descricao", "")),
            "preco_fabrica": _to_number(p.get("preco_fabrica"), 0.0),
            "estoque": _to_number(p.get("estoque"), 0),
        })
    return out


def _to_number(val, default):
    if val is None:
        return default
    if isinstance(val, (int, float)):
        return val
    s = str(val).strip().replace(",", ".")
    if not s:
        return default
    try:
        return float(s) if "." in s else int(s)
    except ValueError:
        return default
