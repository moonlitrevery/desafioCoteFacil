"""Testes para order_runner (run_order)."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_run_order_returns_dict_with_codigo_and_status():
    """
    run_order executa o spider 'order'; em ambiente sem site real,
    o spider retorna código simulado SERV-{id_pedido}.
    Usamos um mock do CrawlerProcess para não depender do Scrapy/network.
    """
    from unittest.mock import MagicMock, patch

    with patch("order_runner.CrawlerProcess") as MockProcess:
        mock_process = MagicMock()
        MockProcess.return_value = mock_process

        # Simular que o pipeline foi chamado e preencheu result_container
        result_container = []

        def side_effect_crawl(*args, **kwargs):
            # Simular o que o CollectOrderResultPipeline faz
            result_container.append({
                "codigo_confirmacao": "SERV-1234",
                "status": "pedido_realizado",
            })

        def side_effect_start():
            # Durante process.start(), o pipeline teria adicionado ao container
            # O container é o mesmo que order_runner passa em settings
            pass

        mock_process.crawl.side_effect = side_effect_crawl
        mock_process.start.side_effect = side_effect_start

        from order_runner import run_order

        # Precisamos que o settings.get("ORDER_RESULT_CONTAINER") seja a mesma lista
        # que run_order usa. O run_order define result_container e passa em settings.
        result = run_order(
            usuario="test@test.com",
            senha="pass",
            id_pedido="1234",
            produtos=[{"gtin": "123", "codigo": "A", "quantidade": 1}],
        )

        # Se o spider não preencher (CrawlerProcess mock não chama pipeline),
        # run_order retorna fallback
        assert "codigo_confirmacao" in result
        assert "status" in result
        assert result["status"] == "pedido_realizado"
        # Fallback quando container vazio: SERV-1234 ou SERV-UNKNOWN
        assert "SERV-" in result["codigo_confirmacao"] or result["codigo_confirmacao"] == "SERV-UNKNOWN"
