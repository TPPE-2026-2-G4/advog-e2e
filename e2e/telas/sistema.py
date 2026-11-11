"""Área logada: menu lateral, páginas, perfil e saída."""

from __future__ import annotations

from dataclasses import dataclass

from selenium.webdriver.common.by import By

from e2e.telas.base import Tela, xpath_texto


@dataclass(frozen=True)
class PaginaDoMenu:
    rotulo: str  # texto do item no menu lateral
    caminho: str
    titulo: str  # <h1> esperado


PAGINAS_DO_MENU = [
    PaginaDoMenu("Início", "/dashboard", "Visão Geral"),
    PaginaDoMenu("Casos/Processos", "/processos", "Gestão de Processos"),
    PaginaDoMenu("Atividades", "/atividades", "Quadro de Atividades"),
    PaginaDoMenu("Finanças", "/financas", "Controle Financeiro"),
    PaginaDoMenu("Calendário", "/calendario", "Calendário de Pagamentos"),
    PaginaDoMenu("Clientes/CRM", "/clientes", "Clientes"),
    PaginaDoMenu("Equipe", "/equipe", "Gestão de Usuários e Permissões"),
    PaginaDoMenu("Site", "/site", "Personalização do Site"),
    PaginaDoMenu("Ajustes", "/ajustes", "Ajustes"),
]


class Sistema(Tela):
    def _item_do_menu(self, rotulo: str):
        return (
            By.XPATH,
            f"//aside//a[.//span[normalize-space(.)={xpath_texto(rotulo)}]]",
        )

    def itens_do_menu(self) -> list[str]:
        itens = self.driver.find_elements(By.XPATH, "//aside//nav//a//span")
        return [item.text.strip() for item in itens if item.text.strip()]

    def tem_item(self, rotulo: str) -> bool:
        return self.existe(self._item_do_menu(rotulo), segundos=2)

    def ir_para(self, pagina: PaginaDoMenu) -> None:
        """Clica no item do menu lateral e confirma o título e a URL da página."""
        self.clicar(self._item_do_menu(pagina.rotulo), pausa=0.5)
        self.afastar_mouse()  # senão a barra lateral continua expandida sobre a página
        self.url_contem(pagina.caminho)
        self.esperar_titulo(pagina.titulo)
        self.pausa()

    # ── menu do usuário ──────────────────────────────────────────────────
    def _abrir_menu_do_usuario(self) -> None:
        self.clicar(
            (By.XPATH, "//header//button[.//*[contains(@class,'lucide-chevron-down')]]"), pausa=0.5
        )

    def abrir_perfil(self) -> None:
        self._abrir_menu_do_usuario()
        self.clicar(self.botao("Meu perfil"), pausa=0.5)
        self.url_contem("/perfil")
        self.esperar_titulo("Meu Perfil")
        self.afastar_mouse()
        self.pausa()

    def sair(self) -> None:
        self._abrir_menu_do_usuario()
        self.clicar(self.botao("Sair"), pausa=0.5)
        self.esperar_texto("Deseja sair da sua conta?")
        self.pausa()
        self.clicar(self.botao("Confirmar e sair"), pausa=0.5)
        self.url_contem("/login")
        self.pausa()

    # ── interações leves (somente leitura) para a demonstração ──────────
    def buscar(self, rotulo_do_campo: str, termo: str) -> None:
        """Digita no campo de busca (por aria-label ou placeholder) e depois limpa."""
        campo = self.esperar_visivel(
            (
                By.XPATH,
                f"//input[@aria-label={xpath_texto(rotulo_do_campo)} "
                f"or @placeholder={xpath_texto(rotulo_do_campo)}]",
            )
        )
        self.digitar(campo, termo)
        self.pausa(1.5)  # deixa o debounce e a requisição terminarem
        self.limpar(campo)
        self.pausa()

    def percorrer_abas(self) -> int:
        abas = self.driver.find_elements(By.CSS_SELECTOR, "[role='tab']")
        for aba in abas:
            self.clicar(aba, pausa=1.2)
        return len(abas)
