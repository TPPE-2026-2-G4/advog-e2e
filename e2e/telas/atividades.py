"""Quadro de Atividades (kanban): criar atividade e etapa, arrastar, excluir."""

from __future__ import annotations

from datetime import date

from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

from e2e.telas.base import xpath_texto
from e2e.telas.cadastros import _Cadastro
from e2e.telas.sistema import PAGINAS_DO_MENU, Sistema

PAGINA_ATIVIDADES = next(p for p in PAGINAS_DO_MENU if p.caminho == "/atividades")

# Simula o arrastar-e-soltar do HTML5 (usado só se o mouse real não conseguir arrastar).
_JS_ARRASTAR = """
const [card, alvo, pronto] = arguments;
const dt = new DataTransfer();
const disparar = (el, tipo) =>
  el.dispatchEvent(new DragEvent(tipo, { bubbles: true, cancelable: true, dataTransfer: dt }));
disparar(card, 'dragstart');
setTimeout(() => {          // dá tempo do React registrar o início do arraste
  disparar(alvo, 'dragenter');
  disparar(alvo, 'dragover');
  disparar(alvo, 'drop');
  disparar(card, 'dragend');
  pronto();
}, 300);
"""


class Atividades(_Cadastro):
    def __init__(self, driver, ambiente):
        super().__init__(driver, ambiente)
        self.sistema = Sistema(driver, ambiente)

    def abrir_pela_pagina(self) -> None:
        self.sistema.ir_para(PAGINA_ATIVIDADES)

    # ── localizadores ────────────────────────────────────────────────────
    @staticmethod
    def _coluna(etapa: str):
        return (
            By.XPATH,
            "//div[starts-with(@data-testid, 'coluna-')]"
            f"[.//*[contains(@class, 'columnTitle') and normalize-space(.)={xpath_texto(etapa)}]]",
        )

    @classmethod
    def _card(cls, titulo: str, etapa: str | None = None):
        card = (
            f"//button[@aria-label={xpath_texto('Editar ' + titulo)}]/ancestor::div[@draggable][1]"
        )
        if etapa is None:
            return (By.XPATH, card)
        coluna = cls._coluna(etapa)[1]
        return (By.XPATH, f"{coluna}{card}")

    def esta_na_etapa(self, titulo: str, etapa: str, segundos: float = 10) -> bool:
        return self.existe(self._card(titulo, etapa), segundos=segundos)

    # ── criar ────────────────────────────────────────────────────────────
    def criar_atividade(self, titulo: str, descricao: str, prazo: date) -> str:
        """Cria a atividade e devolve o nome da etapa onde ela nasceu."""
        self.clicar(self.botao("Nova Atividade"))
        self.esperar_visivel(self.por_aria_label("Título", "input"))
        self.digitar(self.por_aria_label("Título", "input"), titulo)
        self.digitar(self.por_aria_label("Descrição", "textarea"), descricao)
        self.definir_valor(self.por_aria_label("Prazo", "input"), prazo.isoformat())
        etapa = Select(self.driver.find_element(*self.por_aria_label("Status", "select")))
        nome_da_etapa = etapa.first_selected_option.text.strip()
        self.clicar(self.botao("Criar Atividade"), pausa=0.5)
        self.esperar_sumir((By.CSS_SELECTOR, "[role='dialog']"))
        self.esperar_texto("Atividade criada com sucesso.")
        assert self.esta_na_etapa(titulo, nome_da_etapa), "A atividade não apareceu no quadro"
        self.pausa()
        return nome_da_etapa

    def criar_etapa(self, nome: str) -> None:
        self.clicar((By.XPATH, "//header//button[normalize-space(.)='Nova Etapa']"))
        self.esperar_visivel(self.por_aria_label("Nome da etapa", "input"))
        self.digitar(self.por_aria_label("Nome da etapa", "input"), nome)
        self.clicar(self.botao("Criar Etapa"), pausa=0.5)
        self.esperar_sumir((By.CSS_SELECTOR, "[role='dialog']"))
        self.esperar_visivel(self._coluna(nome))
        self.pausa()

    # ── arrastar ─────────────────────────────────────────────────────────
    def arrastar(self, titulo: str, etapa_destino: str) -> str:
        """Arrasta o cartão para a etapa. Devolve "mouse" ou "simulado" (como conseguiu)."""
        card = self.esperar_visivel(self._card(titulo))
        destino = self.esperar_visivel(self._coluna(etapa_destino))
        self.rolar_ate(card)
        self._destacar(card)

        # 1º: arraste de verdade com o mouse (é o que dá para ver na demonstração).
        try:
            acoes = ActionChains(self.driver, duration=400)
            acoes.click_and_hold(card).move_by_offset(10, 10).move_to_element(destino)
            acoes.move_by_offset(5, 5).pause(0.5).release().perform()
        except Exception:  # noqa: BLE001 - o destino pode estar fora da tela; cai no plano B
            pass
        if self.esta_na_etapa(titulo, etapa_destino, segundos=4):
            self.afastar_mouse()
            self.pausa()
            return "mouse"

        # 2º: o navegador não completou o arraste nativo: dispara os eventos do HTML5.
        card = self.esperar_visivel(self._card(titulo))
        destino = self.esperar_visivel(self._coluna(etapa_destino))
        self.driver.set_script_timeout(10)
        self.driver.execute_async_script(_JS_ARRASTAR, card, destino)
        self.afastar_mouse()
        self.pausa()
        return "simulado"

    def recarregar_pagina(self) -> None:
        self.driver.refresh()
        self.esperar_titulo("Quadro de Atividades")
        self.afastar_mouse()
        self.pausa()

    # ── excluir ──────────────────────────────────────────────────────────
    def tentar_excluir_etapa(self, nome: str) -> str:
        """Clica na lixeira da etapa; devolve o aviso mostrado (quando há atividades nela)."""
        self.clicar(self.por_aria_label(f"Excluir etapa {nome}", "button"), pausa=0.3)
        return self.aviso("alert").text

    def excluir_atividade(self, titulo: str) -> None:
        self.clicar(self.por_aria_label(f"Excluir {titulo}", "button"))
        self.esperar_texto("Excluir atividade", tag="h2")
        self.clicar(self.botao("Confirmar exclusão"), pausa=0.5)
        self.esperar_texto("Atividade excluída.")
        self.esperar_sumir(self._card(titulo))
        self.pausa()

    def excluir_etapa(self, nome: str) -> None:
        self.clicar(self.por_aria_label(f"Excluir etapa {nome}", "button"))
        self.esperar_texto("Excluir etapa", tag="h2")
        self.clicar(self.botao("Confirmar exclusão"), pausa=0.5)
        self.esperar_sumir(self._coluna(nome))
        self.pausa()
