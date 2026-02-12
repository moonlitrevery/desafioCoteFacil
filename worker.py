"""
Worker Nível 2: processa tarefas de scraping da fila (RQ + Redis),
executa o spider e envia os produtos para a API do desafio.
"""
import os
import logging

from api_client import get_token, post_produtos
from scraper_runner import run_scraper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Nome da fila (configurável por env)
QUEUE_NAME = os.environ.get("RQ_QUEUE_NAME", "scraping")


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
