#!/usr/bin/env python3
"""
Inicia o worker RQ que processa tarefas de scraping (Nível 2) e de pedido (Nível 3).
Execute a partir da raiz do projeto. Requer Redis em execução.

  python run_worker.py
  python run_worker.py --queues scraping,pedido --redis-url redis://localhost:6379/0
"""
import os
import sys


def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument(
        "--queues",
        default=os.environ.get("RQ_QUEUES", "scraping,pedido"),
        help="Filas separadas por vírgula (ex: scraping,pedido)",
    )
    p.add_argument("--redis-url", default=os.environ.get("REDIS_URL", "redis://localhost:6379/0"))
    args = p.parse_args()

    # RQ worker precisa encontrar os módulos do projeto
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    os.environ.setdefault("REDIS_URL", args.redis_url)

    from rq import Worker
    from redis import Redis

    queue_names = [q.strip() for q in args.queues.split(",") if q.strip()]
    if not queue_names:
        queue_names = ["scraping", "pedido"]

    redis_conn = Redis.from_url(args.redis_url)
    worker = Worker(queue_names, connection=redis_conn)
    worker.work()


if __name__ == "__main__":
    main()
