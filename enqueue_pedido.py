#!/usr/bin/env python3
"""
Nível 3: Gera um pedido aleatório na API do desafio (POST /pedido),
autentica (oauth/token) e enfileira a tarefa para o worker processar.

O worker fará o pedido no site (formulário Servimed) e enviará
o código de confirmação e status via PATCH /pedido/:id.

Uso:
  python enqueue_pedido.py
  python enqueue_pedido.py --usuario "email@fornecedor.com" --senha "senha"
  python enqueue_pedido.py --api-user meu_user --api-password minha_senha
"""
import argparse
import os
import sys


def main():
    parser = argparse.ArgumentParser(
        description="Gera pedido aleatório na API e enfileira tarefa de pedido (Nível 3)"
    )
    parser.add_argument(
        "--usuario", "-u",
        default=os.environ.get("SERVIMED_USER", "juliano@farmaprevonline.com.br"),
        help="Usuário para login no site do fornecedor (Servimed)",
    )
    parser.add_argument(
        "--senha", "-p",
        default=os.environ.get("SERVIMED_PASSWORD", "a007299A"),
        help="Senha para login no site do fornecedor",
    )
    parser.add_argument(
        "--api-user",
        default=os.environ.get("DESAFIO_API_USER"),
        help="Usuário da API do desafio (oauth/token)",
    )
    parser.add_argument(
        "--api-password",
        default=os.environ.get("DESAFIO_API_PASSWORD"),
        help="Senha da API do desafio",
    )
    parser.add_argument(
        "--redis-url",
        default=os.environ.get("REDIS_URL", "redis://localhost:6379/0"),
        help="URL do Redis",
    )
    parser.add_argument(
        "--queue",
        default=os.environ.get("RQ_QUEUE_PEDIDO_NAME", "pedido"),
        help="Nome da fila de pedidos",
    )
    args = parser.parse_args()

    if not args.api_user or not args.api_password:
        print(
            "Erro: configure DESAFIO_API_USER e DESAFIO_API_PASSWORD "
            "(ou --api-user e --api-password).",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        from api_client import get_token, post_pedido
        from redis import Redis
        from rq import Queue
    except ImportError as e:
        print(f"Erro de dependência: {e}", file=sys.stderr)
        sys.exit(1)

    # 1. Obter token e criar pedido aleatório na API
    try:
        token = get_token(username=args.api_user, password=args.api_password)
        pedido = post_pedido(token=token)
    except Exception as e:
        print(f"Erro ao criar pedido na API: {e}", file=sys.stderr)
        sys.exit(1)

    id_pedido = pedido.get("id")
    itens = pedido.get("itens") or []
    if id_pedido is None:
        print("Erro: API não retornou id do pedido.", file=sys.stderr)
        sys.exit(1)

    # 2. Montar payload para a fila (formato do desafio)
    produtos = [
        {"gtin": str(i.get("gtin", "")), "codigo": str(i.get("codigo", "")), "quantidade": i.get("quantidade", 1)}
        for i in itens
    ]
    payload = {
        "usuario": args.usuario,
        "senha": args.senha,
        "id_pedido": str(id_pedido),
        "produtos": produtos,
    }

    # 3. Enfileirar
    try:
        redis_conn = Redis.from_url(args.redis_url)
        queue = Queue(args.queue, connection=redis_conn)
        job = queue.enqueue(
            "worker.process_pedido_task",
            payload,
            job_timeout="600",
        )
        print(f"Pedido criado na API: id={id_pedido}, itens={len(produtos)}")
        print(f"Tarefa enfileirada. Job ID: {job.id}")
        print(f"  Fila: {args.queue}")
        print("Aguarde o worker processar (pedido no site + PATCH /pedido/:id).")
    except Exception as e:
        print(f"Erro ao enfileirar: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
