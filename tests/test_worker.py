"""Testes para worker (process_scraping_task, process_pedido_task)."""
import os

import pytest

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_process_scraping_task_raises_without_usuario_senha():
    from worker import process_scraping_task
    with pytest.raises(ValueError, match="usuario e senha"):
        process_scraping_task({})
    with pytest.raises(ValueError, match="usuario e senha"):
        process_scraping_task({"usuario": "u"})
    with pytest.raises(ValueError, match="usuario e senha"):
        process_scraping_task({"senha": "s"})


def test_process_pedido_task_raises_without_usuario_senha():
    from worker import process_pedido_task
    with pytest.raises(ValueError, match="usuario e senha"):
        process_pedido_task({})
    with pytest.raises(ValueError, match="usuario e senha"):
        process_pedido_task({"usuario": "u", "senha": "s"})  # falta id_pedido


def test_process_pedido_task_raises_without_id_pedido():
    from worker import process_pedido_task
    with pytest.raises(ValueError, match="id_pedido"):
        process_pedido_task({"usuario": "u", "senha": "s", "produtos": []})


def test_process_pedido_task_raises_without_api_creds(monkeypatch):
    monkeypatch.delenv("DESAFIO_API_USER", raising=False)
    monkeypatch.delenv("DESAFIO_API_PASSWORD", raising=False)
    from worker import process_pedido_task
    # O worker chama run_order (spider) e depois get_token; sem API creds dá erro
    # após o run_order. Para não depender do spider real, mockamos run_order
    from unittest.mock import patch
    with patch("worker.run_order") as mock_order:
        mock_order.return_value = {"codigo_confirmacao": "SERV-1", "status": "pedido_realizado"}
        with pytest.raises(ValueError, match="DESAFIO_API_USER"):
            process_pedido_task({
                "usuario": "u",
                "senha": "s",
                "id_pedido": "1",
                "produtos": [{"gtin": "1", "codigo": "A", "quantidade": 1}],
            })


def test_process_pedido_task_full_flow_mocked(monkeypatch):
    monkeypatch.setenv("DESAFIO_API_USER", "api_user")
    monkeypatch.setenv("DESAFIO_API_PASSWORD", "api_pass")
    from unittest.mock import patch, MagicMock
    from worker import process_pedido_task

    with patch("worker.run_order") as mock_order:
        mock_order.return_value = {"codigo_confirmacao": "ABC987", "status": "pedido_realizado"}
        with patch("worker.get_token") as mock_token:
            mock_token.return_value = "token123"
            with patch("worker.patch_pedido") as mock_patch:
                mock_patch.return_value = {"id": 1, "status": "pedido_realizado"}

                result = process_pedido_task({
                    "usuario": "fornecedor_user",
                    "senha": "fornecedor_pass",
                    "id_pedido": "1",
                    "produtos": [{"gtin": "123", "codigo": "A123", "quantidade": 1}],
                })

    assert result["id_pedido"] == "1"
    assert result["codigo_confirmacao"] == "ABC987"
    assert result["status"] == "pedido_realizado"
    mock_patch.assert_called_once()
    call_kw = mock_patch.call_args[1]
    assert call_kw["id_pedido"] == 1
    assert call_kw["codigo_confirmacao"] == "ABC987"
    assert call_kw["status"] == "pedido_realizado"
