"""Percorre todas as páginas da área logada, conferindo o que cada uma mostra.

Somente leitura: os modais abertos são fechados sem salvar. O tour NÃO para na primeira
página com problema: ele segue até o fim e, no final, lista todas as que falharam.
"""

import pytest

from e2e import config
from e2e.telas.cadastros import Processos
from e2e.telas.sistema import PAGINAS_DO_MENU
from e2e.telas.verificacoes import POR_CAMINHO

pytestmark = [pytest.mark.local, pytest.mark.producao]


def _registrar_falha(sistema, falhas: list[str], nome: str, erro: Exception) -> None:
    config.ARTEFATOS.mkdir(exist_ok=True)
    arquivo = config.ARTEFATOS / f"tour-{nome.replace('/', '-')}.png"
    try:
        sistema.driver.save_screenshot(str(arquivo))
    except Exception:  # noqa: BLE001 - o navegador pode ter caído
        pass
    resumo = (str(erro).strip().splitlines() or [type(erro).__name__])[0][:200]
    falhas.append(f"{nome}: {type(erro).__name__}: {resumo} (screenshot: {arquivo.name})")
    # Volta para um ponto conhecido antes da próxima página.
    try:
        sistema.abrir("/dashboard")
    except Exception:  # noqa: BLE001
        pass


def test_tour_por_todas_as_paginas_do_menu(sistema):
    ausentes, falhas = [], []

    for pagina in PAGINAS_DO_MENU:
        if not sistema.tem_item(pagina.rotulo):
            ausentes.append(pagina.rotulo)
            continue
        try:
            sistema.ir_para(pagina)
            POR_CAMINHO[pagina.caminho](sistema)
            print(f"\n  ✔ {pagina.rotulo}", end="")
        except Exception as erro:  # noqa: BLE001 - registra e segue para a próxima página
            _registrar_falha(sistema, falhas, pagina.rotulo, erro)

    try:
        sistema.abrir_perfil()
        POR_CAMINHO["/perfil"](sistema)
        print("\n  ✔ Perfil", end="")
    except Exception as erro:  # noqa: BLE001
        _registrar_falha(sistema, falhas, "Perfil", erro)

    assert not falhas, "Páginas com problema:\n  - " + "\n  - ".join(falhas)
    if config.EXIGIR_TODAS_AS_PAGINAS:
        assert not ausentes, (
            f"Itens do menu ausentes para este usuário: {ausentes}. "
            "Use um usuário administrador ou E2E_EXIGIR_TODAS_AS_PAGINAS=false."
        )


def test_processo_exige_proximo_prazo(sistema):
    processos = Processos(sistema.driver, sistema.ambiente)
    processos.abrir_pela_pagina()

    processos.conferir_prazo_obrigatorio()
