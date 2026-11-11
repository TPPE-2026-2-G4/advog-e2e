"""O que conferir (e usar, sem alterar dados) em cada página da área logada.

Cada função recebe o `Sistema` já posicionado na página. Nada aqui grava dados: os modais
abertos são fechados sem salvar.
"""

from __future__ import annotations

from selenium.webdriver.common.by import By

from e2e.telas.base import xpath_texto
from e2e.telas.sistema import Sistema


def _sem_acesso_negado(s: Sistema) -> None:
    assert not s.existe((By.XPATH, "//h1[contains(., 'Acesso negado')]"), segundos=1), (
        "A página mostrou 'Acesso negado' para o usuário de teste"
    )


def _abrir_e_fechar_modal(s: Sistema, botao: str, titulo_do_modal: str) -> None:
    s.clicar(s.botao(botao), pausa=0.5)
    s.esperar_visivel(
        (By.XPATH, f"//*[@role='dialog']//h2[contains(., {xpath_texto(titulo_do_modal)})]")
    )
    s.pausa(1.5)
    s.fechar_dialogo()


def inicio(s: Sistema) -> None:
    _sem_acesso_negado(s)
    s.esperar_visivel((By.XPATH, "//h2[@id='process-summary-title']"))


def processos(s: Sistema) -> None:
    _sem_acesso_negado(s)
    s.esperar_visivel((By.CSS_SELECTOR, "section[aria-label='Lista de processos']"))
    s.buscar("Buscar por número, cliente ou título...", "a")
    _abrir_e_fechar_modal(s, "Novo Processo", "Novo Processo")


def atividades(s: Sistema) -> None:
    _sem_acesso_negado(s)
    _abrir_e_fechar_modal(s, "Nova Atividade", "Nova Atividade")


def financas(s: Sistema) -> None:
    _sem_acesso_negado(s)
    for rotulo in ("Receita do Mês", "Despesas do Mês", "Saldo Líquido", "A Receber"):
        s.esperar_visivel((By.XPATH, f"//*[starts-with(@aria-label, {xpath_texto(rotulo + ':')})]"))
    for titulo in ("Fluxo de Caixa", "Despesas por Categoria", "Lançamentos Recentes"):
        s.esperar_texto(titulo, tag="h2")

    # Troca o período do gráfico de fluxo de caixa e confirma que o botão ficou ativo.
    periodos = s.driver.find_elements(
        By.XPATH, "//*[@aria-label='Período do fluxo de caixa']//button"
    )
    assert len(periodos) >= 2, "O gráfico deveria ter mais de um período"
    for botao in periodos:
        s.clicar(botao, pausa=0.8)
        assert botao.get_attribute("aria-pressed") == "true"

    _abrir_e_fechar_modal(s, "Novo Lançamento", "Lançamento")


def calendario(s: Sistema) -> None:
    _sem_acesso_negado(s)
    for rotulo in ("Entradas pagas", "Saídas pagas", "A receber", "A pagar", "Em atraso"):
        s.esperar_texto(rotulo, tag="p")

    titulo_do_mes = (By.XPATH, "//button[@aria-label='Mês anterior']/following::h2[1]")
    mes_atual = s.esperar_visivel(titulo_do_mes).text
    s.clicar(s.por_aria_label("Próximo mês", "button"), pausa=1)
    proximo = s.esperar_visivel(titulo_do_mes).text
    assert proximo != mes_atual, "O botão 'Próximo mês' não mudou o mês exibido"
    s.clicar(s.por_aria_label("Mês anterior", "button"), pausa=1)
    assert s.esperar_visivel(titulo_do_mes).text == mes_atual


def clientes(s: Sistema) -> None:
    _sem_acesso_negado(s)
    s.buscar("Buscar clientes", "a")
    _abrir_e_fechar_modal(s, "Novo Cliente", "Cadastrar Novo Cliente")


def equipe(s: Sistema) -> None:
    _sem_acesso_negado(s)
    for titulo in ("Total de Usuários", "Usuários Ativos", "Usuários Pendentes"):
        s.esperar_texto(titulo)
    for titulo in (
        "Membros da Equipe",
        "Referência de Cargos de Acesso (RBAC)",
        "Produtividade da Equipe",
    ):
        s.esperar_texto(titulo, tag="h2")
    _abrir_e_fechar_modal(s, "Adicionar Usuário", "Adicionar Novo Usuário")


def site(s: Sistema) -> None:
    _sem_acesso_negado(s)
    assert s.percorrer_abas() >= 2


def ajustes(s: Sistema) -> None:
    _sem_acesso_negado(s)
    for titulo in ("Notificações por e-mail", "Página inicial padrão"):
        s.esperar_texto(titulo, tag="h2")
    for rotulo in (
        "Selecionar página inicial padrão",
        "Selecionar filtro padrão de processos",
        "Selecionar antecedência de prazos próximos",
        "Dias sem movimentação para processo crítico",
    ):
        s.esperar_visivel(s.por_aria_label(rotulo))


def perfil(s: Sistema) -> None:
    """Confere que o perfil mostra os dados de quem está logado (sem salvar nada)."""
    _sem_acesso_negado(s)
    nome = s.esperar_visivel((By.ID, "profile-name"))
    assert nome.get_attribute("value").strip(), "O nome do perfil está vazio"

    email = s.esperar_visivel((By.ID, "profile-email"))
    assert email.get_attribute("value").lower() == s.ambiente.email.lower(), (
        "O e-mail do perfil não é o do usuário logado"
    )

    for campo in ("current-password", "new-password", "confirm-password"):
        s.esperar_visivel((By.ID, campo))


POR_CAMINHO = {
    "/dashboard": inicio,
    "/processos": processos,
    "/atividades": atividades,
    "/financas": financas,
    "/calendario": calendario,
    "/clientes": clientes,
    "/equipe": equipe,
    "/site": site,
    "/ajustes": ajustes,
    "/perfil": perfil,
}
