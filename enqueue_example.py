#!/usr/bin/env python3
"""
Exemplo de chamada à fila (Nível 2).

Enfileira uma tarefa de scraping com usuario e senha do fornecedor.
Requer Redis em execução e o worker rodando (rq worker).

Uso:
  python enqueue_example.py
  python enqueue_example.py --usuario "email@exemplo.com" --senha "minhasenha"
"""
import argparse
import os
import sys


def main():
    parser = argparse.ArgumentParser(description="Enfileira uma tarefa de scraping")
    parser.add_argument(
        "--usuario", "-u",
        default=os.environ.get("SERVIMED_USER", "juliano@farmaprevonline.com.br"),
        help="Usuário para login no site do fornecedor",
    )
    parser.add_argument(
        "--senha", "-p",
        default=os.environ.get("SERVIMED_PASSWORD", "a007299A"),
        help="Senha para login no site do fornecedor",
    )
    parser.add_argument(
        "--redis-url",
        default=os.environ.get("REDIS_URL", "redis://localhost:6379/0"),
        help="URL do Redis (padrão: redis://localhost:6379/0)",
    )
    parser.add_argument(
        "--queue",
        default=os.environ.get("RQ_QUEUE_NAME", "scraping"),
        help="Nome da fila RQ",
    )
    args = parser.parse_args()

    try:
        from redis import Redis
        from rq import Queue
    except ImportError:
        print("Instale as dependências: pip install redis rq", file=sys.stderr)
        sys.exit(1)

    payload = {
        "usuario": args.usuario,
        "senha": args.senha,
    }

    try:
        redis_conn = Redis.from_url(args.redis_url)
        queue = Queue(args.queue, connection=redis_conn)
        job = queue.enqueue(
            "worker.process_scraping_task",
            payload,
            job_timeout="600",
        )
        print(f"Tarefa enfileirada. Job ID: {job.id}")
        print(f"  Fila: {args.queue}")
        print(f"  Payload: usuario={args.usuario!r}")
        print("Aguarde o worker processar. Verifique com: rq info ou no log do worker.")
    except Exception as e:
        print(f"Erro ao enfileirar: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
