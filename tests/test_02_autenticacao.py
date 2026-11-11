"""Proteção de rotas, login inválido, login válido e saída."""

import pytest

from e2e.telas.publicas import LoginPagina
from e2e.telas.sistema import Sistema

pytestmark = [pytest.mark.local, pytest.mark.producao]


def test_rota_protegida_redireciona_para_o_login(tela):
    tela.abrir("/clientes")

    tela.url_contem("/login")


def test_login_com_senha_errada_mostra_aviso(driver, ambiente):
    login = LoginPagina(driver, ambiente)
    login.abrir_login()

    login.entrar("e2e.inexistente@example.com", "senha-incorreta-123")

    assert login.aviso("alert").text  # aviso amigável no topo da tela
    assert "/dashboard" not in driver.current_url


def test_login_valido_e_saida(driver, exigir_credenciais):
    login = LoginPagina(driver, exigir_credenciais)
    login.entrar_e_aguardar_painel(exigir_credenciais.email, exigir_credenciais.senha)

    Sistema(driver, exigir_credenciais).sair()

    assert "/login" in driver.current_url
