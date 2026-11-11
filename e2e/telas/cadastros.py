"""Fluxos que criam e apagam dados: clientes e processos."""

from __future__ import annotations

import time

from selenium.webdriver.common.by import By

from e2e.telas.base import Tela, xpath_texto
from e2e.telas.sistema import PAGINAS_DO_MENU, Sistema

PAGINA_CLIENTES = next(p for p in PAGINAS_DO_MENU if p.caminho == "/clientes")
PAGINA_PROCESSOS = next(p for p in PAGINAS_DO_MENU if p.caminho == "/processos")


def gerar_marca() -> str:
    """Identificador único para reconhecer (e limpar) os dados criados pelos testes."""
    return time.strftime("%d%m%H%M%S")


def gerar_cnj(marca: str) -> tuple[str, str]:
    """Retorna (apenas dígitos, formatado) de um número CNJ único e válido."""
    sequencial = int(marca) % 10_000_000
    digitos = f"{sequencial:07d}" + "99" + "2026" + "8" + "07" + "0001"
    formatado = (
        f"{digitos[:7]}-{digitos[7:9]}.{digitos[9:13]}."
        f"{digitos[13]}.{digitos[14:16]}.{digitos[16:]}"
    )
    return digitos, formatado


class _Cadastro(Tela):
    def campo_por_rotulo(self, rotulo: str):
        return (
            By.XPATH,
            f"//input[@id=//label[normalize-space(.)={xpath_texto(rotulo)}]/@for]",
        )

    def fechar_modal(self) -> None:
        self.clicar((By.XPATH, "(//*[@role='dialog']//button[@aria-label='Fechar'])[1]"), pausa=0.5)
        self.esperar_sumir((By.CSS_SELECTOR, "[role='dialog']"))


class Clientes(_Cadastro):
    def __init__(self, driver, ambiente):
        super().__init__(driver, ambiente)
        self.sistema = Sistema(driver, ambiente)

    def abrir_pela_pagina(self) -> None:
        self.sistema.ir_para(PAGINA_CLIENTES)

    def _linha(self, nome: str):
        return (By.XPATH, f"//tr[.//*[normalize-space(.)={xpath_texto(nome)}]]")

    def cadastrar(self, nome: str, email: str, telefone: str = "61999990000") -> None:
        self.clicar(self.botao("Novo Cliente"))
        self.esperar_texto("Cadastrar Novo Cliente", tag="h2")
        self.digitar((By.ID, "add-client-nome"), nome)
        self.digitar((By.ID, "add-client-telefone"), telefone)
        self.digitar((By.ID, "add-client-email"), email)
        self.clicar(self.botao("Salvar Cadastro"), pausa=0.5)
        self.esperar_texto("Cliente cadastrado com sucesso!")
        self.esperar_visivel(self._linha(nome))
        self.pausa()

    def buscar(self, termo: str) -> None:
        campo = self.esperar_visivel(self.por_aria_label("Buscar clientes", "input"))
        self.digitar(campo, termo)
        self.pausa(1.5)  # debounce + requisição

    def limpar_busca(self) -> None:
        campo = self.esperar_visivel(self.por_aria_label("Buscar clientes", "input"))
        self.limpar(campo)
        self.pausa()

    def aparece_na_lista(self, nome: str) -> bool:
        return self.existe(self._linha(nome), segundos=self.ambiente.timeout)

    def abrir_detalhes(self, nome: str) -> None:
        self.clicar(self.por_aria_label(f"Visualizar detalhes de {nome}", "button"))
        self.esperar_texto("Detalhes do Cliente", tag="h2")
        self.pausa(1.5)
        self.fechar_modal()

    def excluir(self, nome: str) -> None:
        self.buscar(nome)
        self.clicar(self.por_aria_label(f"Excluir cliente {nome}", "button"))
        self.esperar_texto("Excluir cliente", tag="h2")
        self.clicar(self.botao("Excluir"), pausa=0.5)
        self.esperar_texto("Cliente excluído com sucesso!")
        self.esperar_sumir(self._linha(nome))
        self.pausa()


class Processos(_Cadastro):
    def __init__(self, driver, ambiente):
        super().__init__(driver, ambiente)
        self.sistema = Sistema(driver, ambiente)

    def abrir_pela_pagina(self) -> None:
        self.sistema.ir_para(PAGINA_PROCESSOS)

    def _linha(self, cnj: str):
        return (By.XPATH, f"//tr[.//*[contains(normalize-space(.), {xpath_texto(cnj)})]]")

    def cadastrar(self, *, cnj_digitos: str, titulo: str, cliente: str) -> None:
        self.clicar(self.botao("Novo Processo"))
        self.esperar_texto("Novo Processo", tag="h2")
        self.digitar(self.campo_por_rotulo("Número do Processo"), cnj_digitos)
        self.digitar(self.campo_por_rotulo("Tribunal"), "TJDFT")
        self.digitar(self.campo_por_rotulo("Título do Caso"), titulo)

        combo = self.esperar_visivel((By.CSS_SELECTOR, "[role='dialog'] [role='combobox']"))
        self.digitar(combo, cliente)
        self.clicar(
            (By.XPATH, f"//li[@role='option'][.//*[normalize-space(.)={xpath_texto(cliente)}]]")
        )

        self.digitar(self.campo_por_rotulo("Área de Atuação"), "Civil")
        self.definir_valor(self.campo_por_rotulo("Próximo Prazo"), "2030-12-31")
        self.clicar(self.botao("Salvar Processo"), pausa=0.5)
        self.esperar_sumir((By.CSS_SELECTOR, "[role='dialog']"))
        self.pausa()

    def buscar(self, termo: str) -> None:
        campo = self.esperar_visivel(
            (By.XPATH, "//input[@placeholder='Buscar por número, cliente ou título...']")
        )
        self.digitar(campo, termo)
        self.pausa(1.5)

    def aparece_na_lista(self, cnj_formatado: str) -> bool:
        return self.existe(self._linha(cnj_formatado), segundos=self.ambiente.timeout)

    def conferir_prazo_obrigatorio(self) -> None:
        """Abre o formulário, tenta salvar sem o prazo e confirma que o navegador bloqueia."""
        self.clicar(self.botao("Novo Processo"))
        self.esperar_texto("Novo Processo", tag="h2")
        prazo = self.esperar_visivel(self.campo_por_rotulo("Próximo Prazo"))
        assert prazo.get_attribute("required"), "Próximo Prazo deveria ser obrigatório"
        self.clicar(self.botao("Salvar Processo"), pausa=1.5)
        invalido = self.driver.execute_script("return arguments[0].validity.valueMissing;", prazo)
        assert invalido, "O formulário deveria ser barrado por falta do Próximo Prazo"
        assert self.existe((By.CSS_SELECTOR, "[role='dialog']"), segundos=1)
        self.clicar(self.botao("Cancelar"), pausa=0.5)

    def abrir_detalhes(self, cnj_formatado: str) -> None:
        self.clicar(self.por_aria_label(f"Visualizar processo {cnj_formatado}", "button"))
        self.esperar_visivel((By.CSS_SELECTOR, "[role='dialog']"))
        self.pausa(2)
        self.fechar_modal()

    def excluir(self, cnj_formatado: str) -> None:
        self.buscar(cnj_formatado)
        self.clicar(self.por_aria_label(f"Excluir processo {cnj_formatado}", "button"))
        self.esperar_texto("Excluir processo?")
        self.clicar(self.botao("Excluir processo"), pausa=0.5)
        self.esperar_sumir(self._linha(cnj_formatado))
        self.pausa()
