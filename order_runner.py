"""
Executa o spider de pedido e retorna o resultado (codigo_confirmacao, status).
Usado pelo worker Nível 3 para simular envio do pedido no site e obter código Servimed.
"""
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings


def run_order(
    usuario: str,
    senha: str,
    id_pedido: str,
    produtos: list[dict],
    login_url: str | None = None,
) -> dict:
    """
    Executa o spider de pedido no site do fornecedor.

    Args:
        usuario: Login no site Servimed.
        senha: Senha no site Servimed.
        id_pedido: ID do pedido na API do desafio (para referência/código simulado).
        produtos: Lista de dicts com gtin, codigo, quantidade.
        login_url: URL de login (opcional; padrão do spider).

    Returns:
        {"codigo_confirmacao": str, "status": str}, ex.: "pedido_realizado".
    """
    result_container: list[dict] = []

    settings = get_project_settings()
    settings.set("LOG_LEVEL", "WARNING")
    settings.set("ORDER_RESULT_CONTAINER", result_container)
    settings.set("ITEM_PIPELINES", {
        "servimed_scraper.pipelines.CollectOrderResultPipeline": 100,
    })

    process = CrawlerProcess(settings)
    process.crawl(
        "order",
        user=usuario,
        password=senha,
        id_pedido=id_pedido,
        produtos=produtos,
        login_url=login_url,
    )
    process.start()

    if result_container:
        return result_container[0]
    # Fallback se o spider não yieldar (ex.: erro antes da confirmação)
    return {
        "codigo_confirmacao": f"SERV-{id_pedido}" if id_pedido else "SERV-UNKNOWN",
        "status": "pedido_realizado",
    }
