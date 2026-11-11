"""Páginas públicas: landing page, login e fluxos de senha."""

from __future__ import annotations

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By

from e2e.telas.base import Tela

BOTAO_ENTRAR = (By.XPATH, "//button[normalize-space(.)='Entrar']")
CAMPO_EMAIL = (By.ID, "email")
CAMPO_SENHA = (By.ID, "senha")

# Seções da landing page: (texto do menu, id da seção). Aparecem conforme o conteúdo cadastrado.
SECOES_LANDING = [
    ("Início", "inicio"),
    ("Áreas de Atuação", "areas"),
    ("Sobre", "sobre"),
    ("Equipe", "equipe"),
    ("Contato", "contato"),
]


class LandingPagina(Tela):
    def abrir_landing(self) -> None:
        self.abrir("/")
        self.esperar_visivel((By.CSS_SELECTOR, "[data-testid='hero-section']"))

    def secoes_visiveis(self) -> list[str]:
        """Navega pelo menu da landing page e retorna as seções que existem."""
        visitadas = []
        for texto, _secao in SECOES_LANDING:
            localizador = (
                By.XPATH,
                f"//nav[@aria-label='Navegação Principal']//a[normalize-space(.)='{texto}']",
            )
            if self.existe(localizador, segundos=2):
                self.clicar(localizador, pausa=1.5)
                visitadas.append(texto)
        return visitadas

    def formulario_de_atendimento(self) -> None:
        self.rolar_ate(self.esperar_visivel(self.botao("Enviar Solicitação")))
        self.esperar_visivel((By.XPATH, "//label[contains(., 'Nome completo')]"))
        self.pausa()


class LoginPagina(Tela):
    def abrir_login(self) -> None:
        self.abrir("/login")
        self.esperar_visivel(BOTAO_ENTRAR)

    def entrar(self, email: str, senha: str) -> None:
        self.digitar(CAMPO_EMAIL, email)
        self.digitar(CAMPO_SENHA, senha)
        self.clicar(BOTAO_ENTRAR, pausa=0.5)

    def entrar_e_aguardar_painel(self, email: str, senha: str) -> None:
        self.abrir_login()
        self.entrar(email, senha)
        try:
            self.url_contem("/dashboard")
        except TimeoutException:
            motivo = self.aviso("alert").text if self.existe((By.ID, "toast-viewport"), 1) else ""
            raise AssertionError(
                "O login não levou ao painel. "
                + (f"Aviso na tela: '{motivo}'. " if motivo else "")
                + "Confira EMAIL_/SENHA_ do ambiente no .env."
            ) from None
        self.esperar_titulo("Visão Geral")
        self.afastar_mouse()
        self.pausa()


class SenhaPagina(Tela):
    def abrir_esqueci_senha(self) -> None:
        self.abrir("/esqueci-senha")
        self.esperar_titulo("Recuperar senha")
        self.esperar_visivel(self.botao("Enviar link"))

    def abrir_primeiro_acesso(self) -> None:
        self.abrir("/primeiro-acesso")
        self.esperar_titulo("Primeiro acesso")
        self.esperar_visivel((By.ID, "nome"))

    def abrir_redefinir_senha(self) -> None:
        self.abrir("/redefinir-senha")
        self.esperar_titulo("Redefinir senha")
