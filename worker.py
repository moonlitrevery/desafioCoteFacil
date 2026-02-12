"""
Worker Nível 2 e 3: processa tarefas de scraping e de pedido (RQ + Redis).
- Nível 2: scraping + POST /produto.
- Nível 3: pedido no site + PATCH /pedido/:id com código de confirmação.
"""
import os
import logging

from api_client import get_token, patch_pedido, post_pedido, post_produtos
from order_runner import run_order
from scraper_runner import run_scraper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Nomes das filas (configuráveis por env)
QUEUE_NAME = os.environ.get("RQ_QUEUE_NAME", "scraping")
QUEUE_PEDIDO_NAME = os.environ.get("RQ_QUEUE_PEDIDO_NAME", "pedido")


def process_scraping_task(payload: dict) -> dict:
    """
    Job executado pelo worker RQ.

    payload: {"usuario": "fornecedor_user", "senha": "fornecedor_pass"}

    Fluxo:
    1. Executa o scraping com as credenciais do payload.
    2. Autentica na API (oauth/token) com credenciais de env.
    3. Envia os produtos para POST /produto.

    Retorna dict com quantidade de produtos enviados e resposta da API.
    """
    usuario = payload.get("usuario") or payload.get("user")
    senha = payload.get("senha") or payload.get("password")
    if not usuario or not senha:
        raise ValueError("Payload deve conter 'usuario' e 'senha'")

    logger.info("Iniciando scraping para usuario=%s", usuario)
    produtos = run_scraper(usuario=usuario, senha=senha)
    logger.info("Scraping concluído: %d produtos", len(produtos))

    if not produtos:
        return {"produtos_enviados": 0, "mensagem": "Nenhum produto extraído"}

    api_user = os.environ.get("DESAFIO_API_USER")
    api_password = os.environ.get("DESAFIO_API_PASSWORD")
    if not api_user or not api_password:
        raise ValueError(
            "Configure DESAFIO_API_USER e DESAFIO_API_PASSWORD para enviar à API"
        )

    token = get_token(username=api_user, password=api_password)
    response = post_produtos(produtos=produtos, token=token)
    logger.info("Produtos enviados à API: %d", len(produtos))

    return {
        "produtos_enviados": len(produtos),
        "resposta_api": response,
    }


def process_pedido_task(payload: dict) -> dict:
    """
    Job Nível 3: processa uma tarefa de pedido.

    payload: {
        "usuario": "fornecedor_user",
        "senha": "fornecedor_pass",
        "id_pedido": "1234",
        "produtos": [{"gtin": "...", "codigo": "A123", "quantidade": 1}, ...]
    }

    Fluxo:
    1. Executa o pedido no site (formulário Servimed) via order_runner.
    2. Obtém codigo_confirmacao e status.
    3. Autentica na API do desafio (DESAFIO_API_USER / DESAFIO_API_PASSWORD).
    4. Envia PATCH /pedido/:id com codigo_confirmacao e status.

    Retorna dict com resultado do pedido e resposta do PATCH.
    """
    usuario = payload.get("usuario") or payload.get("user")
    senha = payload.get("senha") or payload.get("password")
    id_pedido = payload.get("id_pedido")
    produtos = payload.get("produtos") or []

    if not usuario or not senha:
        raise ValueError("Payload deve conter 'usuario' e 'senha'")
    if id_pedido is None or id_pedido == "":
        raise ValueError("Payload deve conter 'id_pedido'")

    id_pedido_str = str(id_pedido)
    try:
        id_pedido_int = int(id_pedido)
    except (TypeError, ValueError):
        id_pedido_int = None

    logger.info("Processando pedido id_pedido=%s, %d itens", id_pedido_str, len(produtos))

    # Normalizar produtos para lista de dicts com gtin, codigo, quantidade
    itens = []
    for p in produtos:
        itens.append({
            "gtin": str(p.get("gtin", "")),
            "codigo": str(p.get("codigo", "")),
            "quantidade": int(p.get("quantidade", 1)) or 1,
        })

    # 1. Realizar pedido no site (simulação de formulário)
    order_result = run_order(
        usuario=usuario,
        senha=senha,
        id_pedido=id_pedido_str,
        produtos=itens,
    )
    codigo_confirmacao = order_result.get("codigo_confirmacao", f"SERV-{id_pedido_str}")
    status = order_result.get("status", "pedido_realizado")

    logger.info("Pedido no site: codigo_confirmacao=%s, status=%s", codigo_confirmacao, status)

    # 2. Callback na API do desafio (PATCH /pedido/:id)
    api_user = os.environ.get("DESAFIO_API_USER")
    api_password = os.environ.get("DESAFIO_API_PASSWORD")
    if not api_user or not api_password:
        raise ValueError(
            "Configure DESAFIO_API_USER e DESAFIO_API_PASSWORD para enviar callback à API"
        )
    if id_pedido_int is None:
        logger.warning("id_pedido não é inteiro; PATCH pode falhar. Payload: %s", id_pedido_str)

    token = get_token(username=api_user, password=api_password)
    response = patch_pedido(
        id_pedido=id_pedido_int if id_pedido_int is not None else int(id_pedido_str),
        codigo_confirmacao=codigo_confirmacao,
        status=status,
        token=token,
    )
    logger.info("Callback PATCH /pedido/%s concluído", id_pedido_str)

    return {
        "id_pedido": id_pedido_str,
        "codigo_confirmacao": codigo_confirmacao,
        "status": status,
        "resposta_api": response,
    }
