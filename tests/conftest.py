"""Fixtures compartilhadas para os testes."""
import os

import pytest


@pytest.fixture(autouse=True)
def reset_env_api(monkeypatch):
    """Garante DESAFIO_API_URL definida nos testes que chamam a API."""
    monkeypatch.setenv("DESAFIO_API_URL", "https://desafio.cotefacil.net")


@pytest.fixture
def api_base():
    return "https://desafio.cotefacil.net"
