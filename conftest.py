"""Fixtures do pytest: ambiente (local/produção), navegador e relatórios de falha.

Como escolher onde rodar
------------------------
Cada teste leva as tags `@pytest.mark.local` e/ou `@pytest.mark.producao`.
Um teste com as duas tags roda uma vez por ambiente permitido.

    pytest                         # ambiente do .env (E2E_AMBIENTE, padrão: local)
    pytest --ambiente producao     # só os testes marcados com "producao", na URL_PRODUCAO
    pytest -m local                # idem, filtrando pela tag
"""

from __future__ import annotations

import time
import urllib.error
import urllib.request
from datetime import datetime

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.remote.webdriver import WebDriver

from e2e import config
from e2e.config import AMBIENTES, Ambiente
from e2e.telas.base import Tela
from e2e.telas.publicas import LoginPagina
from e2e.telas.sistema import Sistema


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--ambiente",
        choices=AMBIENTES,
        default=None,
        help="Ambiente a testar: local ou producao (padrão: E2E_AMBIENTE do .env).",
    )


def _ambiente_escolhido(config_pytest: pytest.Config) -> str:
    return config_pytest.getoption("--ambiente") or config.ambiente_padrao()


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    """Cria uma execução do teste para cada ambiente marcado (local/producao)."""
    if "ambiente_nome" not in metafunc.fixturenames:
        return
    escolhido = _ambiente_escolhido(metafunc.config)
    marcados = [nome for nome in AMBIENTES if metafunc.definition.get_closest_marker(nome)]
    # Teste sem tag nenhuma roda no ambiente escolhido.
    nomes = marcados or [escolhido]
    parametros = [pytest.param(nome, id=nome, marks=getattr(pytest.mark, nome)) for nome in nomes]
    metafunc.parametrize("ambiente_nome", parametros, scope="function")


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    escolhido = _ambiente_escolhido(config)
    selecionados, descartados = [], []
    for item in items:
        callspec = getattr(item, "callspec", None)
        nome = callspec.params.get("ambiente_nome") if callspec else None
        (selecionados if nome in (None, escolhido) else descartados).append(item)
    if descartados:
        config.hook.pytest_deselected(items=descartados)
        items[:] = selecionados


@pytest.fixture
def ambiente(ambiente_nome: str) -> Ambiente:
    """Ambiente do teste atual. Falha com uma mensagem clara se o .env estiver incompleto."""
    try:
        return config.obter_ambiente(ambiente_nome)
    except ValueError as erro:
        pytest.fail(str(erro), pytrace=False)


@pytest.fixture
def exigir_credenciais(ambiente: Ambiente) -> Ambiente:
    if not ambiente.email or not ambiente.senha:
        pytest.fail(
            f"Preencha EMAIL_{ambiente.nome.upper()} e SENHA_{ambiente.nome.upper()} no .env.",
            pytrace=False,
        )
    return ambiente


@pytest.fixture
def permitir_escrita(ambiente: Ambiente) -> None:
    """Testes marcados com `escrita` criam/apagam dados: em produção precisam de autorização."""
    if ambiente.eh_producao and not config.PERMITIR_ESCRITA_PRODUCAO:
        pytest.skip(
            "Teste de escrita não roda em produção. "
            "Defina E2E_PERMITIR_ESCRITA_PRODUCAO=true no .env para liberar."
        )


@pytest.fixture(autouse=True)
def _guarda_de_escrita(request: pytest.FixtureRequest) -> None:
    if request.node.get_closest_marker("escrita"):
        request.getfixturevalue("permitir_escrita")


@pytest.fixture(scope="session")
def _api_acordada() -> set[str]:
    return set()


@pytest.fixture(autouse=True)
def acordar_api(ambiente_nome: str, _api_acordada: set[str]) -> None:
    """Em produção a API (Render) dorme; chama /health até ela responder."""
    if ambiente_nome in _api_acordada:
        return
    try:
        ambiente = config.obter_ambiente(ambiente_nome)
    except ValueError:
        return  # quem reclama é a fixture `ambiente`
    _api_acordada.add(ambiente_nome)
    if not ambiente.api_url:
        return

    alvo = f"{ambiente.api_url}/health"
    limite = datetime.now().timestamp() + ambiente.timeout * 2
    ultimo_erro = ""
    while datetime.now().timestamp() < limite:
        try:
            with urllib.request.urlopen(alvo, timeout=15) as resposta:  # noqa: S310
                if resposta.status < 500:
                    return
        except (urllib.error.URLError, TimeoutError, OSError) as erro:
            ultimo_erro = str(erro)
        time.sleep(3)
    pytest.fail(f"A API não respondeu em {alvo}: {ultimo_erro}", pytrace=False)


def _criar_driver() -> WebDriver:
    opcoes = Options()
    opcoes.add_argument("--lang=pt-BR")
    opcoes.add_argument("--window-size=1440,900")
    opcoes.add_argument("--disable-search-engine-choice-screen")
    opcoes.add_argument("--no-first-run")
    opcoes.add_experimental_option("excludeSwitches", ["enable-automation"])
    opcoes.add_experimental_option(
        "prefs",
        {
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False,
            "profile.default_content_setting_values.notifications": 2,
        },
    )
    if config.HEADLESS:
        opcoes.add_argument("--headless=new")
        # Sem janela o Chrome se diz "sem mouse" e o site muda de comportamento (a barra
        # lateral só expande ao passar o mouse). Isso faz o modo headless agir como desktop.
        opcoes.add_argument(
            "--blink-settings=primaryHoverType=2,availableHoverTypes=2,"
            "primaryPointerType=4,availablePointerTypes=4"
        )
    else:
        opcoes.add_argument("--start-maximized")
    # Selenium Manager baixa o driver (e o Chrome, se faltar) automaticamente.
    return webdriver.Chrome(options=opcoes)


@pytest.fixture
def driver() -> WebDriver:
    navegador = _criar_driver()
    yield navegador
    navegador.quit()


@pytest.fixture
def tela(driver: WebDriver, ambiente: Ambiente) -> Tela:
    return Tela(driver, ambiente)


@pytest.fixture
def sistema(driver: WebDriver, exigir_credenciais: Ambiente) -> Sistema:
    """Navegador já logado no sistema, parado no painel (dashboard)."""
    LoginPagina(driver, exigir_credenciais).entrar_e_aguardar_painel(
        exigir_credenciais.email, exigir_credenciais.senha
    )
    return Sistema(driver, exigir_credenciais)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo):
    resultado = yield
    relatorio = resultado.get_result()
    if relatorio.when != "call" or not relatorio.failed:
        return
    navegador = item.funcargs.get("driver") if hasattr(item, "funcargs") else None
    if navegador is None:
        return
    config.ARTEFATOS.mkdir(exist_ok=True)
    base = config.ARTEFATOS / f"{datetime.now():%Y%m%d-%H%M%S}-{item.name.replace('/', '_')}"
    try:
        navegador.save_screenshot(str(base.with_suffix(".png")))
        base.with_suffix(".html").write_text(navegador.page_source, encoding="utf-8")
        relatorio.sections.append(("Artefatos", f"{base}.png / .html"))
    except Exception:  # noqa: BLE001 - o navegador pode já ter caído
        pass
