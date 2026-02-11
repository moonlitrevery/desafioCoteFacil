# Scrapy settings for servimed_scraper project

BOT_NAME = "servimed_scraper"
SPIDER_MODULES = ["servimed_scraper.spiders"]
NEWSPIDER_MODULE = "servimed_scraper.spiders"

# Obey robots.txt (desative em ambiente controlado se necessário)
ROBOTSTXT_OBEY = False

# Configurações de requisição
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"

# User-Agent para evitar bloqueio básico
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

# Autothrottle (opcional, para ser gentil com o servidor)
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1
AUTOTHROTTLE_MAX_DELAY = 5

# Log level (INFO para execução normal)
LOG_LEVEL = "INFO"

# Pipelines (exportação JSON pode ser feita via FEED no comando/script)
# ITEM_PIPELINES = {}
