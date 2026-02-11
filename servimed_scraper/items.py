# Define here the models for your scraped items
import scrapy


class ProductItem(scrapy.Item):
    """Item com os dados extraídos de cada produto conforme requisito do desafio."""
    gtin = scrapy.Field()       # GTIN (EAN)
    codigo = scrapy.Field()     # Código
    descricao = scrapy.Field()  # Descrição
    preco_fabrica = scrapy.Field()  # Preço de fábrica
    estoque = scrapy.Field()    # Estoque
