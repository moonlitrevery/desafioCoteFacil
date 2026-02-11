# Desafio Cotefácil – Desenvolvedor Python (Nível 1)

Repositório do desafio técnico: aplicação de web scraping com **Scrapy** no site do fornecedor Servimed (pedido eletrônico), com login, extração da listagem de produtos e armazenamento em JSON local.

## Objetivo (Nível 1 – Básico)

- Fazer login no site do Servimed.
- Acessar a listagem de produtos.
- Extrair de cada produto: **GTIN (EAN)**, **Código**, **Descrição**, **Preço de fábrica**, **Estoque**.
- Utilizar apenas **Scrapy** (sem Selenium, Playwright, etc.).
- Armazenar os dados em **JSON local**.

## Como executar

### 1. Ambiente

Recomendado: Python 3.10+ e ambiente virtual.

```bash
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
# ou: .venv\Scripts\activate   # Windows

pip install -r requirements.txt
```

### 2. Execução com script (recomendado)

Na raiz do projeto (onde está `scrapy.cfg` e `run_scraper.py`):

```bash
python run_scraper.py --user "juliano@farmaprevonline.com.br" --password "a007299A" --output produtos.json
```

Formas equivalentes:

```bash
python run_scraper.py -u "juliano@farmaprevonline.com.br" -p "a007299A" -o produtos.json
```

Usando variáveis de ambiente (evita senha no histórico):

```bash
export SERVIMED_USER="juliano@farmaprevonline.com.br"
export SERVIMED_PASSWORD="a007299A"
python run_scraper.py -o produtos.json
```

### 3. Execução direta com Scrapy

Na mesma raiz do projeto:

```bash
scrapy crawl products \
  -a user="juliano@farmaprevonline.com.br" \
  -a password="a007299A" \
  -o produtos.json
```

O arquivo `produtos.json` (ou o nome informado em `-o`) será gerado na raiz do projeto.

## Visão técnica

- **Scrapy**: projeto padrão (`scrapy.cfg` + pacote `servimed_scraper`). Spider único `products` em `servimed_scraper/spiders/products_spider.py`.
- **Login**: primeira requisição à página de login; o spider localiza o formulário (incluindo campo de senha), descobre os nomes dos campos (Email/Usuario, Senha/Password) e envia um `FormRequest` com as credenciais. Cookies de sessão são reutilizados nas próximas requisições.
- **Produtos**: após o login, é feita uma requisição à URL da listagem. A extração tenta tabelas (`table tbody tr`) e, em seguida, listas/divs; cada linha/card é mapeada para um item com os cinco campos (GTIN, código, descrição, preço de fábrica, estoque). Paginação é seguida quando existem links “Próxima”/“Next”.
- **Itens**: definidos em `servimed_scraper/items.py` (`ProductItem`). A saída é exportada em JSON via `FEEDS` no script ou via `-o` no comando `scrapy crawl`.
- **Script `run_scraper.py`**: usa `CrawlerProcess`, aplica `FEEDS` para o arquivo JSON e repassa usuário/senha (e opcionalmente `login_url`/`products_url`) como argumentos do spider.

Se a estrutura HTML do site (formulário de login ou tabela de produtos) for diferente do esperado, pode ser necessário ajustar os seletores em `products_spider.py` (por exemplo, XPath/CSS da tabela ou dos campos do formulário) após inspecionar a página no navegador.

## Estrutura do repositório

```
.
├── scrapy.cfg
├── run_scraper.py          # Script de execução com parâmetros de login
├── requirements.txt
├── README.md
└── servimed_scraper/
    ├── __init__.py
    ├── settings.py
    ├── items.py            # ProductItem (gtin, codigo, descricao, preco_fabrica, estoque)
    ├── middlewares.py
    ├── pipelines.py
    └── spiders/
        ├── __init__.py
        └── products_spider.py   # Spider de login + listagem de produtos
```

## Credenciais (ambiente de teste)

- **Site**: https://pedidoeletronico.servimed.com.br/
- **Usuário**: juliano@farmaprevonline.com.br
- **Senha**: a007299A

*(Não commitar credenciais reais no repositório.)*
