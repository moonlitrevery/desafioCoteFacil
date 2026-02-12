#!/usr/bin/env python3
"""
Inicia o worker RQ que processa tarefas de scraping (Nível 2).
Execute a partir da raiz do projeto. Requer Redis em execução.

  python run_worker.py
  python run_worker.py --queue scraping --redis-url redis://localhost:6379/0
"""
import os
import sys


def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--queue", default=os.environ.get("RQ_QUEUE_NAME", "scraping"))
    p.add_argument("--redis-url", default=os.environ.get("REDIS_URL", "redis://localhost:6379/0"))
    args = p.parse_args()

    # RQ worker precisa encontrar os módulos do projeto
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    os.environ.setdefault("RQ_QUEUE_NAME", args.queue)
    os.environ.setdefault("REDIS_URL", args.redis_url)

    from rq import Worker
    from redis import Redis
    from rq import Queue

    redis_conn = Redis.from_url(args.redis_url)
    queue = Queue(args.queue, connection=redis_conn)
    worker = Worker([queue], connection=redis_conn)
    worker.work()


if __name__ == "__main__":
    main()
