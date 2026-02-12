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


---

## Nível 2 – Intermediário (fila + API)

### Objetivo

- Processo assíncrono que recebe tarefas de scraping via **fila** (RQ + Redis).
- Executa o scraping de forma independente para cada solicitação.
- Envia os produtos extraídos para a **API do desafio** (autenticação OAuth e POST /produto).

### Requisitos atendidos

- **Fila**: RQ (Redis Queue) com Redis.
- **Payload da tarefa**: `{"usuario": "fornecedor_user", "senha": "fornecedor_pass"}`.
- **Worker**: processa a tarefa, faz o scraping e envia o JSON de produtos para POST /produto (após obter token em /oauth/token).
- **API**: signup em /oauth/signup; autenticação em /oauth/token; envio em POST /produto.

### Como testar localmente (Nível 2)

#### 1. Dependências e Redis

```bash
pip install -r requirements.txt
```

É necessário ter **Redis** em execução (para a fila). Exemplos:

- **Linux (Arch/Debian)**: `sudo systemctl start redis` ou `redis-server`
- **Docker**: `docker run -d -p 6379:6379 redis:alpine`
- **macOS**: `brew services start redis`

#### 2. Variáveis de ambiente da API

Para o worker enviar os dados à API, configure:

```bash
export DESAFIO_API_URL="https://api.desafio.cotefacil.com.br"   # URL base da API
export DESAFIO_API_USER="seu_usuario"                             # usuário criado no signup
export DESAFIO_API_PASSWORD="sua_senha"                           # senha do usuário
```

#### 3. Criar usuário na API (uma vez)
Antes de rodar o worker, crie um usuário na API (POST /oauth/signup):

```bash
python -c "
from api_client import signup
signup('seu_email@exemplo.com', 'sua_senha')
print('Usuário criado. Use DESAFIO_API_USER e DESAFIO_API_PASSWORD com esse email/senha.')
"
```

Use o mesmo email/senha em `DESAFIO_API_USER` e `DESAFIO_API_PASSWORD`.

#### 4. Iniciar o worker

Na **raiz do projeto** (para os imports encontrarem `worker`, `api_client`, `scraper_runner`):

```bash
# Opção A: script do projeto
python run_worker.py

# Opção B: comando RQ (também na raiz do projeto)
rq worker scraping
```

O worker ficará ouvindo a fila `scraping` (ou o nome em `RQ_QUEUE_NAME`). Deixe este terminal aberto.

#### 5. Enfileirar uma tarefa (exemplo de chamada à fila)

Em **outro terminal**, na raiz do projeto:

```bash
# Usando credenciais de teste do fornecedor (Servimed)
python enqueue_example.py

# Ou informando usuario e senha
python enqueue_example.py --usuario "juliano@farmaprevonline.com.br" --senha "a007299A"
```

O worker processará a tarefa: fará o scraping com o usuario/senha informados e enviará os produtos para a API (usando `DESAFIO_API_USER` / `DESAFIO_API_PASSWORD` para obter o token).
#### 6. Redis em outro host ou fila com outro nome

```bash
export REDIS_URL="redis://localhost:6379/0"
export RQ_QUEUE_NAME="scraping"
python run_worker.py
python enqueue_example.py --redis-url "$REDIS_URL" --queue "$RQ_QUEUE_NAME"
```

### Entregáveis Nível 2

| Entregável | Descrição |
|------------|-----------|
| **Worker + fila** | `worker.py` (job `process_scraping_task`), fila RQ com Redis; `run_worker.py` para subir o worker. |
| **Exemplo de chamada à fila** | `enqueue_example.py` — enfileira uma tarefa com `{"usuario": "...", "senha": "..."}`. |
| **Documentação** | Esta seção do README: como testar localmente (Redis, env, signup, worker, enqueue). |

### Visão técnica Nível 2

- **Fila**: RQ com Redis; fila padrão `scraping`. O job é `worker.process_scraping_task(payload)`.
- **Scraper em memória**: `scraper_runner.run_scraper(usuario, senha)` usa o mesmo spider do Nível 1 e o pipeline `CollectItemsPipeline` para acumular itens em uma lista (sem escrever JSON em disco).
- **API**: `api_client.py` — `signup()`, `get_token()`, `post_produtos()`. Token obtido com `DESAFIO_API_USER`/`DESAFIO_API_PASSWORD`; produtos enviados em POST /produto no formato exigido (gtin, codigo, descricao, preco_fabrica numérico, estoque numérico).

---


## Estrutura do repositório

```
.
├── scrapy.cfg
├── run_scraper.py            # Nível 1: execução com parâmetros de login
├── run_worker.py             # Nível 2: inicia o worker RQ
├── enqueue_example.py        # Nível 2: exemplo de chamada à fila
├── worker.py                 # Nível 2: job process_scraping_task
├── api_client.py             # Nível 2: signup, oauth/token, POST /produto
├── scraper_runner.py         # Nível 2: executa spider e retorna lista em memória
├── requirements.txt
├── README.md
└── servimed_scraper/
    ├── __init__.py
    ├── settings.py
    ├── items.py
    ├── middlewares.py
    ├── pipelines.py           # Inclui CollectItemsPipeline para o worker
    └── spiders/
        ├── __init__.py
        └── products_spider.py   # Spider de login + listagem de produtos
```
