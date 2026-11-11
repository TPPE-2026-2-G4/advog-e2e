"""Páginas que não exigem login: landing page, login e fluxos de senha."""

import pytest
from selenium.webdriver.common.by import By

from e2e.telas.publicas import LandingPagina, LoginPagina, SenhaPagina

pytestmark = [pytest.mark.local, pytest.mark.producao]


def test_landing_page_percorre_as_secoes(driver, ambiente):
    landing = LandingPagina(driver, ambiente)

    landing.abrir_landing()
    secoes = landing.secoes_visiveis()
    landing.formulario_de_atendimento()

    assert "Início" in secoes
    assert "Contato" in secoes


def test_pagina_de_login_mostra_o_formulario(driver, ambiente):
    login = LoginPagina(driver, ambiente)

    login.abrir_login()

    assert login.esperar_visivel((By.ID, "email")).is_displayed()
    assert login.esperar_visivel((By.ID, "senha")).is_displayed()
    login.esperar_visivel(login.link("Esqueci minha senha"))


def test_paginas_de_senha_carregam(driver, ambiente):
    senha = SenhaPagina(driver, ambiente)

    senha.abrir_esqueci_senha()
    senha.abrir_primeiro_acesso()
    senha.abrir_redefinir_senha()
