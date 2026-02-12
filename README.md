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

## Nível 3 – Avançado (Pedido)

### Objetivo

- Gerar um pedido aleatório pela API do desafio (POST /pedido, com autenticação).
- Enfileirar tarefa com payload: `usuario`, `senha`, `id_pedido`, `produtos`.
- Worker: realizar o pedido via formulário no site (Servimed) e enviar código de confirmação e status para a API (PATCH /pedido/:id).

### Requisitos atendidos

- **Signup**: criar usuário em /oauth/signup (username/password).
- **Autenticação**: /oauth/token para obter token antes de POST /pedido e PATCH /pedido/:id.
- **Pedido aleatório**: POST /pedido (retorna pedido com id e itens).
- **Fila de pedidos**: tarefas com `{"usuario", "senha", "id_pedido", "produtos": [{"gtin", "codigo", "quantidade"}]}`.
- **Worker de pedido**: `process_pedido_task` — executa pedido no site (order spider) e faz PATCH /pedido/:id com `{"codigo_confirmacao", "status"}`.

### Como executar (Nível 3)

#### 1. Criar usuário na API (uma vez)

```bash
python -c "
from api_client import signup
signup('seu_usuario', 'sua_senha_min_8_chars')
print('Usuário criado. Use DESAFIO_API_USER e DESAFIO_API_PASSWORD.')
"
```

#### 2. Variáveis de ambiente

```bash
export DESAFIO_API_URL="https://desafio.cotefacil.net"
export DESAFIO_API_USER="seu_usuario"
export DESAFIO_API_PASSWORD="sua_senha"
export SERVIMED_USER="juliano@farmaprevonline.com.br"
export SERVIMED_PASSWORD="a007299A"
# Opcional: copie .env.example para .env e ajuste
```

#### 3. Iniciar o worker (filas scraping e pedido)

```bash
python run_worker.py
# ou só fila pedido: python run_worker.py --queues pedido
```

#### 4. Gerar pedido aleatório e enfileirar

Em outro terminal:

```bash
python enqueue_pedido.py
```

Isso irá: obter token → POST /pedido (pedido aleatório) → enfileirar tarefa com usuario/senha do fornecedor e itens do pedido. O worker fará login no site, simulará o pedido e enviará PATCH /pedido/:id com `codigo_confirmacao` e `status: pedido_realizado`.

#### 5. Simulação de ambiente

- O spider de pedido (`order`) faz login no site real; se não encontrar formulário de pedido, retorna código simulado `SERV-{id_pedido}` para integrar com a API.
- Para testes locais sem o site Servimed, use o servidor mock (ver seção **Testes** e **Simulação com API mock**) ou variável `SERVIMED_MOCK=1` em testes.

### Entregáveis Nível 3

| Entregável | Descrição |
|------------|-----------|
| **Lógica de pedido** | `order_runner.py`, spider `order` em `servimed_scraper/spiders/order_spider.py`, job `worker.process_pedido_task`. |
| **API** | `post_pedido()`, `patch_pedido()` em `api_client.py`; signup com username. |
| **Fila** | Fila `pedido`; `enqueue_pedido.py` gera pedido na API e enfileira. |
| **Simulação** | Spider simula envio de formulário; código de confirmação extraído da página ou simulado. |
| **Testes** | pytest em `tests/` (api_client, worker, order_runner, mock server). |

### Visão técnica Nível 3

- **POST /pedido**: gera pedido aleatório (API retorna id e itens). Autenticação Bearer.
- **Payload da tarefa**: `usuario`, `senha`, `id_pedido`, `produtos` (lista com gtin, codigo, quantidade).
- **Worker**: `process_pedido_task` → `order_runner.run_order()` (spider `order`: login + formulário de pedido) → obtém `codigo_confirmacao` e `status` → `patch_pedido(id, codigo_confirmacao, status, token)`.
- **Callback**: PATCH /pedido/:id com JSON `{"codigo_confirmacao": "ABC987", "status": "pedido_realizado"}`.

---

## Testes automatizados

Requer: `pip install -r requirements-dev.txt` (ou `pytest responses`).

```bash
# Na raiz do projeto
pytest
# Com cobertura
pytest --cov=. --cov-report=term-missing
```

Testes: `tests/test_api_client.py` (signup, token, produto, pedido), `tests/test_worker.py` (validação de payload e fluxo mockado), `tests/test_order_runner.py` (run_order).

---

## Simulação com API mock (ambiente local)

Para testar o fluxo de pedido sem a API real do desafio:

```bash
pip install fastapi uvicorn
uvicorn tests_mock_server.app:app --reload --port 8799
```

Em outro terminal:

```bash
export DESAFIO_API_URL=http://127.0.0.1:8799
python -c "from api_client import signup; signup('testuser', 'password123'); print('OK')"
export DESAFIO_API_USER=testuser
export DESAFIO_API_PASSWORD=password123
python enqueue_pedido.py
```

O worker (com Redis e `python run_worker.py`) processará a fila e fará PATCH no mock.

---


## Estrutura do repositório

```
.
├── scrapy.cfg
├── pyproject.toml
├── .env.example
├── run_scraper.py            # Nível 1: execução com parâmetros de login
├── run_worker.py             # Nível 2/3: worker RQ (filas scraping e pedido)
├── enqueue_example.py        # Nível 2: enfileira tarefa de scraping
├── enqueue_pedido.py         # Nível 3: gera pedido na API e enfileira tarefa de pedido
├── worker.py                 # process_scraping_task, process_pedido_task
├── api_client.py             # signup, oauth/token, POST /produto, POST/PATCH /pedido
├── scraper_runner.py         # executa spider de produtos
├── order_runner.py           # Nível 3: executa spider de pedido
├── requirements.txt
├── README.md
├── tests/                    # Testes automatizados (pytest)
│   ├── conftest.py
│   ├── test_api_client.py
│   ├── test_worker.py
│   └── test_order_runner.py
├── tests_mock_server/        # API mock local (uvicorn tests_mock_server.app:app)
│   └── app.py
└── servimed_scraper/
    ├── __init__.py
    ├── settings.py
    ├── items.py
    ├── middlewares.py
    ├── pipelines.py           # CollectItemsPipeline, CollectOrderResultPipeline
    └── spiders/
        ├── __init__.py
        ├── products_spider.py
        └── order_spider.py    # Nível 3: pedido no site
```