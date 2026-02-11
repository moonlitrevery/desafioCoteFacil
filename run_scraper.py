#!/usr/bin/env python3
"""
Script de execução do spider de produtos Servimed (Nível 1 - Desafio Cotefácil).
Permite informar usuário e senha por parâmetros e grava o resultado em JSON local.
Uso:
  python run_scraper.py --user EMAIL --password SENHA [--output produtos.json]
  python run_scraper.py -u EMAIL -p SENHA [-o produtos.json]
"""
import argparse
import os
import sys


def main():
    parser = argparse.ArgumentParser(
        description="Executa o spider de produtos do Servimed com login."
    )
    parser.add_argument(
        "-u", "--user",
        default=os.environ.get("SERVIMED_USER", ""),
        help="Usuário/email para login (ou variável SERVIMED_USER)",
    )
    parser.add_argument(
        "-p", "--password",
        default=os.environ.get("SERVIMED_PASSWORD", ""),
        help="Senha para login (ou variável SERVIMED_PASSWORD)",
    )
    parser.add_argument(
        "-o", "--output",
        default="produtos.json",
        help="Arquivo JSON de saída (padrão: produtos.json)",
    )
    parser.add_argument(
        "--login-url",
        default="",
        help="URL da página de login (opcional)",
    )
    parser.add_argument(
        "--products-url",
        default="",
        help="URL da listagem de produtos (opcional)",
    )
    args = parser.parse_args()

    if not args.user or not args.password:
        print("Erro: informe usuário e senha com -u/--user e -p/--password (ou variáveis SERVIMED_USER e SERVIMED_PASSWORD).", file=sys.stderr)
        sys.exit(1)

    # Scrapy é executado via CrawlerProcess para ter controle do feed
    from scrapy.crawler import CrawlerProcess
    from scrapy.utils.project import get_project_settings

    settings = get_project_settings()
    settings.set("FEEDS", {
        args.output: {
            "format": "json",
            "encoding": "utf-8",
            "overwrite": True,
        }
    })

    process = CrawlerProcess(settings)
    process.crawl(
        "products",
        user=args.user,
        password=args.password,
        login_url=args.login_url or None,
        products_url=args.products_url or None,
    )
    process.start()


if __name__ == "__main__":
    main()
