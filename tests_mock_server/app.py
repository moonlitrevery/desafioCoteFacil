"""
Servidor mock da API do desafio (Nível 3 – simulação local).
Simula /oauth/signup, /oauth/token, /pedido (GET/POST/PATCH), /produto (POST).

Uso:
  pip install fastapi uvicorn
  uvicorn tests_mock_server.app:app --reload --port 8799

Depois:
  export DESAFIO_API_URL=http://127.0.0.1:8799
  python enqueue_pedido.py
"""
import random
import string
from typing import Any

from fastapi import FastAPI, Form, HTTPException, Depends
from fastapi.responses import Response
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

app = FastAPI(title="Mock API Desafio Cotefácil", version="0.1.0")

# Armazenamento em memória
users: dict[str, str] = {}  # username -> password
tokens: dict[str, str] = {}  # token -> username
pedidos: dict[int, dict] = {}
_next_id = 1

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/oauth/token", auto_error=False)


# ---------- Schemas ----------
class CreateUser(BaseModel):
    username: str
    password: str


class TokenForm(BaseModel):
    grant_type: str | None = "password"
    username: str
    password: str


class PedidoItem(BaseModel):
    gtin: str
    codigo: str
    quantidade: int


class Pedido(BaseModel):
    id: int
    codigo_fornecedor: str | None
    status: str | None
    itens: list[PedidoItem]


class UpdatePedido(BaseModel):
    codigo_confirmacao: str
    status: str


# ---------- Auth ----------
def fake_token():
    return "mock_" + "".join(random.choices(string.ascii_letters + string.digits, k=20))


def get_current_user(token: str = Depends(oauth2_scheme)):
    if not token or token not in tokens:
        raise HTTPException(status_code=401, detail="Invalid token")
    return tokens[token]


# ---------- Routes ----------
@app.post("/oauth/signup")
def signup(body: CreateUser):
    if len(body.username) < 3 or len(body.username) > 50:
        raise HTTPException(422, "username length")
    if len(body.password) < 8 or len(body.password) > 64:
        raise HTTPException(422, "password length")
    users[body.username] = body.password
    return {"message": "User created"}


@app.post("/oauth/token")
def login(
    username: str = Form(...),
    password: str = Form(...),
    grant_type: str = Form(None),
):
    if username not in users or users[username] != password:
        raise HTTPException(401, "Invalid credentials")
    token = fake_token()
    tokens[token] = username
    return {"access_token": token, "token_type": "bearer", "expires_in": 3600}


@app.get("/pedido")
def listar_pedidos(_: str = Depends(get_current_user)):
    return list(pedidos.values())


@app.post("/pedido")
def criar_pedido(_: str = Depends(get_current_user)):
    global _next_id
    id_pedido = _next_id
    _next_id += 1
    itens = [
        {"gtin": "1234567890123", "codigo": f"A{i}", "quantidade": random.randint(1, 5)}
        for i in range(random.randint(1, 4))
    ]
    pedido = {
        "id": id_pedido,
        "codigo_fornecedor": None,
        "status": None,
        "itens": itens,
    }
    pedidos[id_pedido] = pedido
    return pedido


@app.get("/pedido/{id_pedido}")
def mostrar_pedido(id_pedido: int, _: str = Depends(get_current_user)):
    if id_pedido not in pedidos:
        raise HTTPException(404)
    return pedidos[id_pedido]


@app.patch("/pedido/{id_pedido}")
def atualizar_pedido(id_pedido: int, body: UpdatePedido, _: str = Depends(get_current_user)):
    if id_pedido not in pedidos:
        raise HTTPException(404)
    pedidos[id_pedido]["codigo_fornecedor"] = body.codigo_confirmacao
    pedidos[id_pedido]["status"] = body.status
    return pedidos[id_pedido]


@app.get("/healthcheck")
def healthcheck():
    return Response(status_code=204)
