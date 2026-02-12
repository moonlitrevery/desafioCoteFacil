"""
Executa o spider de produtos e retorna a lista de produtos em memória.
Usado pelo worker do Nível 2 para obter os dados sem escrever em disco.
"""
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings


def run_scraper(usuario: str, senha: str) -> list[dict]:
    """
    Executa o spider de produtos com as credenciais do fornecedor e retorna
    uma lista de dicts, cada um com: gtin, codigo, descricao, preco_fabrica, estoque.
    """
    items_list: list[dict] = []
    settings = get_project_settings()
    settings.set("COLLECT_ITEMS_LIST", items_list)
    settings.set("LOG_LEVEL", "WARNING")
    settings.set("ITEM_PIPELINES", {
        "servimed_scraper.pipelines.CollectItemsPipeline": 100,
    })

    process = CrawlerProcess(settings)
    process.crawl(
        "products",
        user=usuario,
        password=senha,
    )
    process.start()
    return items_list
