"""Finanças e Calendário: criar lançamentos (entrada e saída), conferir no calendário, apagar."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date

from selenium.webdriver.common.by import By

from e2e.telas.base import xpath_texto
from e2e.telas.cadastros import _Cadastro
from e2e.telas.sistema import PAGINAS_DO_MENU, Sistema

PAGINA_FINANCAS = next(p for p in PAGINAS_DO_MENU if p.caminho == "/financas")
PAGINA_CALENDARIO = next(p for p in PAGINAS_DO_MENU if p.caminho == "/calendario")

MESES = [
    "Janeiro",
    "Fevereiro",
    "Março",
    "Abril",
    "Maio",
    "Junho",
    "Julho",
    "Agosto",
    "Setembro",
    "Outubro",
    "Novembro",
    "Dezembro",
]


@dataclass(frozen=True)
class NovoLancamento:
    tipo: str  # "Entrada" ou "Saída"
    titulo: str
    descricao: str
    valor: str  # como se digita: "150,00"
    data: date


class Lancamentos(_Cadastro):
    def __init__(self, driver, ambiente):
        super().__init__(driver, ambiente)
        self.sistema = Sistema(driver, ambiente)

    def abrir_pela_pagina(self) -> None:
        self.sistema.ir_para(PAGINA_FINANCAS)

    def _linha(self, titulo: str):
        return (By.XPATH, f"//tr[.//*[contains(normalize-space(.), {xpath_texto(titulo)})]]")

    def _escolher_categoria(self) -> None:
        """Usa uma categoria que já existe; só cria a "E2E Teste" se não houver nenhuma."""
        campo = (By.ID, "lancamento-categoria")
        self.clicar(campo, pausa=0.5)
        existentes = self.driver.find_elements(
            By.XPATH, "//input[@id='lancamento-categoria']/following-sibling::ul/li"
        )
        if existentes:
            self.clicar(existentes[0], pausa=0.5)
        else:
            self.digitar(campo, "E2E Teste")

    def criar(self, lancamento: NovoLancamento) -> None:
        self.clicar(self.botao("Novo Lançamento"))
        self.esperar_visivel((By.ID, "lancamento-titulo"))

        grupo = "//*[@role='group'][@aria-label='Tipo de lançamento']"
        self.clicar(
            (By.XPATH, f"{grupo}//button[normalize-space(.)={xpath_texto(lancamento.tipo)}]")
        )
        self.digitar((By.ID, "lancamento-titulo"), lancamento.titulo)
        self.digitar((By.ID, "lancamento-descricao"), lancamento.descricao)
        self.digitar((By.ID, "lancamento-valor"), lancamento.valor)
        self.definir_valor((By.ID, "lancamento-data"), lancamento.data.isoformat())
        self.definir_valor((By.ID, "lancamento-vencimento"), lancamento.data.isoformat())
        self._escolher_categoria()

        self.clicar(self.botao("Salvar Lançamento"), pausa=0.5)
        self.esperar_sumir((By.CSS_SELECTOR, "[role='dialog']"))
        self.pausa()

    def filtrar_por_dia(self, dia: date) -> None:
        """Restringe a tabela ao dia (a lista é paginada de 5 em 5)."""
        self.definir_valor(self.por_aria_label("Data inicial", "input"), dia.isoformat())
        self.definir_valor(self.por_aria_label("Data final", "input"), dia.isoformat())
        self.pausa(1.5)

    def _ir_para_a_primeira_pagina(self) -> None:
        anterior = self.por_aria_label("Página anterior", "button")
        while (
            self.existe(anterior, segundos=1) and self.driver.find_element(*anterior).is_enabled()
        ):
            self.clicar(anterior, pausa=0.3)

    def localizar(self, titulo: str) -> bool:
        """Procura o lançamento pelo título, passando pelas páginas da tabela."""
        self._ir_para_a_primeira_pagina()
        proxima = self.por_aria_label("Próxima página", "button")
        for _ in range(30):
            if self.existe(self._linha(titulo), segundos=3):
                return True
            botoes = self.driver.find_elements(*proxima)
            if not botoes or not botoes[0].is_enabled():
                return False
            self.clicar(botoes[0], pausa=0.4)
        return False

    def excluir(self, titulo: str) -> None:
        assert self.localizar(titulo), f"Lançamento '{titulo}' não encontrado para excluir"
        linha = self.driver.find_element(*self._linha(titulo))
        self.clicar(linha.find_element(By.XPATH, ".//button[@aria-label='Excluir lançamento']"))
        self.esperar_texto("Excluir lançamento?", tag="h2")
        self.clicar(self.botao("Excluir lançamento"), pausa=0.5)
        self.esperar_sumir((By.CSS_SELECTOR, "[role='dialog']"))
        self.pausa()


class Calendario(_Cadastro):
    def __init__(self, driver, ambiente):
        super().__init__(driver, ambiente)
        self.sistema = Sistema(driver, ambiente)

    _TITULO_DO_MES = (By.XPATH, "//button[@aria-label='Mês anterior']/following::h2[1]")

    def abrir_pela_pagina(self) -> None:
        self.sistema.ir_para(PAGINA_CALENDARIO)

    def ir_para_o_mes(self, dia: date) -> None:
        """Navega pelos botões "Mês anterior/Próximo mês" até o mês do dia informado."""
        alvo = dia.year * 12 + dia.month
        for _ in range(36):
            texto = self.esperar_visivel(self._TITULO_DO_MES).text.strip()
            mes, ano = re.match(r"(\D+)\s+(\d{4})", texto).groups()
            atual = int(ano) * 12 + MESES.index(mes.strip()) + 1
            if atual == alvo:
                return
            rotulo = "Próximo mês" if atual < alvo else "Mês anterior"
            self.clicar(self.por_aria_label(rotulo, "button"), pausa=0.6)
        raise AssertionError(f"Não consegui chegar ao mês de {dia:%m/%Y} no calendário")

    def selecionar_dia(self, dia: date) -> None:
        self.clicar(self.por_aria_label(f"Dia {dia.day} de {MESES[dia.month - 1]}", "button"))
        self.esperar_visivel(
            (By.XPATH, f"//h3[contains(., '{dia.day:02d}/{dia.month:02d}/{dia.year}')]")
        )
        self.pausa()

    def card_do_lancamento(self, titulo: str):
        """Cartão do lançamento no painel de detalhes do dia (None se não estiver lá)."""
        localizador = (
            By.XPATH,
            f"//p[normalize-space(.)={xpath_texto(titulo)}]"
            "/ancestor::div[.//span[contains(., 'R$')]][1]",
        )
        if not self.existe(localizador, segundos=self.ambiente.timeout):
            return None
        return self.driver.find_element(*localizador)

    def sem_lancamento(self, titulo: str) -> bool:
        return not self.existe(
            (By.XPATH, f"//p[normalize-space(.)={xpath_texto(titulo)}]"), segundos=3
        )
