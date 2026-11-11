"""Fluxo completo com escrita: cria cliente e processo, confere, e apaga tudo no fim.

Em produção só roda com E2E_PERMITIR_ESCRITA_PRODUCAO=true. Tudo que o teste cria leva o
prefixo "E2E" e é apagado mesmo se o teste falhar no meio.
"""

import pytest

from e2e.telas.cadastros import Clientes, Processos, gerar_cnj, gerar_marca

pytestmark = [pytest.mark.local, pytest.mark.producao, pytest.mark.escrita]


def test_cadastra_confere_e_exclui_cliente_e_processo(sistema):
    clientes = Clientes(sistema.driver, sistema.ambiente)
    processos = Processos(sistema.driver, sistema.ambiente)

    marca = gerar_marca()
    nome = f"E2E Cliente {marca}"
    email = f"e2e.{marca}@example.com"
    cnj_digitos, cnj = gerar_cnj(marca)
    titulo = f"E2E Processo {marca}"

    cliente_criado = processo_criado = False
    try:
        # 1. Cliente
        clientes.abrir_pela_pagina()
        clientes.cadastrar(nome, email)
        cliente_criado = True
        clientes.buscar(nome)
        assert clientes.aparece_na_lista(nome)
        clientes.abrir_detalhes(nome)
        clientes.limpar_busca()

        # 2. Processo do cliente
        processos.abrir_pela_pagina()
        processos.cadastrar(cnj_digitos=cnj_digitos, titulo=titulo, cliente=nome)
        processo_criado = True
        processos.buscar(cnj)
        assert processos.aparece_na_lista(cnj)
        processos.abrir_detalhes(cnj)
    finally:
        # Limpeza: primeiro o processo (depende do cliente), depois o cliente.
        if processo_criado:
            processos.abrir_pela_pagina()
            processos.excluir(cnj)
        if cliente_criado:
            clientes.abrir_pela_pagina()
            clientes.excluir(nome)
