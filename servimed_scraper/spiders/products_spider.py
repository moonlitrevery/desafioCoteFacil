"""
Spider para login no site Servimed e extração da listagem de produtos.
Nível 1 - Desafio Cotefácil: Scrapy sem Selenium/Playwright.
"""
import re
import scrapy
from scrapy.http import FormRequest
from servimed_scraper.items import ProductItem


class ProductsSpider(scrapy.Spider):
    name = "products"
    allowed_domains = ["pedidoeletronico.servimed.com.br"]
    # URL base do pedido eletrônico Servimed
    base_url = "https://pedidoeletronico.servimed.com.br"

    # Parâmetros configuráveis via -a user= e -a password=
    def __init__(self, user=None, password=None, login_url=None, products_url=None, **kwargs):
        super().__init__(**kwargs)
        self.user = user or ""
        self.password = password or ""
        self.login_url = login_url or f"{self.base_url}/"
        self.products_url = products_url or f"{self.base_url}/"

    def start_requests(self):
        """Primeira requisição: página de login (fallback para Scrapy < 2.13)."""
        yield scrapy.Request(
            self.login_url,
            callback=self.parse_login_page,
            dont_filter=True,
        )

    async def start(self, *args, **kwargs):
        """Scrapy 2.13+: inicia com requisição à página de login."""
        yield scrapy.Request(
            self.login_url,
            callback=self.parse_login_page,
            dont_filter=True,
        )

    def parse_login_page(self, response):
        """
        Localiza o formulário de login, descobre os nomes dos campos e envia o POST.
        Compatível com formulários que usam Email/Usuario/UserName e Senha/Password.
        """
        # Tenta encontrar a URL de ação do formulário (login)
        form = response.xpath("//form[.//input[@type='password']]")
        if not form:
            form = response.xpath("//form")
        if not form:
            self.logger.warning("Nenhum formulário encontrado na página de login. Verifique login_url e a estrutura do site.")
            # Mesmo assim tenta ir para a listagem (site pode não ter login separado)
            yield scrapy.Request(
                self.products_url,
                callback=self.parse_products_list,
                dont_filter=True,
            )
            return

        form = form[0]
        action = form.xpath("@action").get()
        if action and not action.startswith("http"):
            action = response.urljoin(action)
        form_action = action or self.login_url

        # Descobre nomes dos campos: usuário (email/login) e senha
        inputs = form.xpath(".//input[@name]")
        formdata = {}
        user_key = None
        password_key = None

        for inp in inputs:
            name = inp.xpath("@name").get()
            if not name:
                continue
            name_lower = name.lower()
            if inp.xpath("@type").get() == "password":
                password_key = name
            elif "senha" in name_lower or "password" in name_lower:
                password_key = name
            elif "email" in name_lower or "user" in name_lower or "login" in name_lower or "usuario" in name_lower:
                user_key = name
            else:
                # Inclui campos hidden (ex.: __RequestVerificationToken) para o POST
                val = inp.xpath("@value").get()
                if val is not None:
                    formdata[name] = val

        if user_key:
            formdata[user_key] = self.user
        if password_key:
            formdata[password_key] = self.password

        if not formdata.get(user_key or "") and self.user:
            # Fallback: nomes comuns
            formdata["Email"] = self.user
            formdata["UserName"] = self.user
        if not formdata.get(password_key or "") and self.password:
            formdata["Senha"] = self.password
            formdata["Password"] = self.password

        self.logger.info("Enviando login para %s", form_action)
        yield FormRequest(
            url=form_action,
            formdata=formdata,
            callback=self.after_login,
            dont_filter=True,
        )

    def after_login(self, response):
        """Após o login, acessa a listagem de produtos."""
        # Verificação simples: se ainda houver formulário de senha, login pode ter falhado
        if response.xpath("//form[.//input[@type='password']]") and self.user:
            self.logger.warning("Possível falha no login: formulário de senha ainda presente.")
        yield scrapy.Request(
            self.products_url,
            callback=self.parse_products_list,
            dont_filter=True,
        )

    def parse_products_list(self, response):
        """
        Extrai a listagem de produtos.
        Tenta múltiplas estratégias: tabela (tr), listas (.item, .produto, [data-*]).
        """
        # Estratégia 1: linhas de tabela (thead + tbody tr)
        rows = response.xpath("//table[@class='table']//tbody/tr | //table//tbody/tr")
        if not rows:
            rows = response.xpath("//table//tr[position()>1]")
        if not rows:
            rows = response.xpath("//div[contains(@class,'item') or contains(@class,'produto') or contains(@class,'row')]")
        if not rows:
            rows = response.xpath("//tr[.//td[count(*)>=3]]")

        for row in rows:
            item = self._extract_product_from_row(row, response)
            if item and (item.get("gtin") or item.get("codigo") or item.get("descricao")):
                yield item

        # Paginação: links "Próxima", "Next", número da página
        next_page = (
            response.xpath("//a[contains(.,'Próxim') or contains(.,'Next') or contains(.,'»')]/@href").get()
            or response.xpath("//ul[contains(@class,'pagination')]//a[@rel='next']/@href").get()
        )
        if next_page:
            yield response.follow(next_page, callback=self.parse_products_list)

    def _extract_product_from_row(self, row, response):
        """Extrai um ProductItem a partir de uma linha (tr ou div)."""
        # Tabela: geralmente colunas na ordem ou com classes
        cells = row.xpath(".//td")
        if cells:
            return self._item_from_cells(cells)
        # Divs com spans ou pequenos blocos
        texts = row.xpath(".//text()").getall()
        texts = [re.sub(r"\s+", " ", t).strip() for t in texts if t.strip()]
        if len(texts) >= 5:
            return ProductItem(
                gtin=texts[0] if len(texts) > 0 else "",
                codigo=texts[1] if len(texts) > 1 else "",
                descricao=texts[2] if len(texts) > 2 else "",
                preco_fabrica=texts[3] if len(texts) > 3 else "",
                estoque=texts[4] if len(texts) > 4 else "",
            )
        return None

    def _item_from_cells(self, cells):
        """Monta ProductItem a partir de uma lista de células (td)."""
        def cell_text(c, idx):
            if idx < len(cells):
                return " ".join(cells[idx].xpath(".//text()").getall()).strip()
            return ""

        # Ordem típica: GTIN, Código, Descrição, Preço, Estoque (ou similar)
        n = len(cells)
        if n >= 5:
            return ProductItem(
                gtin=cell_text(cells, 0),
                codigo=cell_text(cells, 1),
                descricao=cell_text(cells, 2),
                preco_fabrica=cell_text(cells, 3),
                estoque=cell_text(cells, 4),
            )
        if n >= 1:
            return ProductItem(
                gtin=cell_text(cells, 0),
                codigo=cell_text(cells, 1) if n > 1 else "",
                descricao=cell_text(cells, 2) if n > 2 else "",
                preco_fabrica=cell_text(cells, 3) if n > 3 else "",
                estoque=cell_text(cells, 4) if n > 4 else "",
            )
        return None
