"""Cria uma entrada e uma saída, confere no calendário e apaga as duas.

Em produção só roda com E2E_PERMITIR_ESCRITA_PRODUCAO=true. Os lançamentos levam o prefixo
"E2E" no título e são apagados mesmo se o teste falhar no meio.
"""

from datetime import date

import pytest

from e2e.telas.cadastros import gerar_marca
from e2e.telas.financeiro import Calendario, Lancamentos, NovoLancamento

pytestmark = [pytest.mark.local, pytest.mark.producao, pytest.mark.escrita]


def test_cria_entrada_e_saida_confere_no_calendario_e_exclui(sistema):
    financas = Lancamentos(sistema.driver, sistema.ambiente)
    calendario = Calendario(sistema.driver, sistema.ambiente)

    marca = gerar_marca()
    hoje = date.today()
    entrada = NovoLancamento(
        "Entrada", f"E2E Entrada {marca}", "Honorários (teste automatizado)", "150,00", hoje
    )
    saida = NovoLancamento(
        "Saída", f"E2E Saída {marca}", "Despesa (teste automatizado)", "80,50", hoje
    )

    criados: list[str] = []
    try:
        # 1. Cria os dois lançamentos em Finanças.
        financas.abrir_pela_pagina()
        for lancamento in (entrada, saida):
            financas.criar(lancamento)
            criados.append(lancamento.titulo)
        financas.filtrar_por_dia(hoje)
        for lancamento in (entrada, saida):
            assert financas.localizar(lancamento.titulo), f"{lancamento.titulo} não apareceu"

        # 2. Antes de apagar, confere os dois no Calendário.
        calendario.abrir_pela_pagina()
        calendario.ir_para_o_mes(hoje)
        calendario.selecionar_dia(hoje)

        card_entrada = calendario.card_do_lancamento(entrada.titulo)
        assert card_entrada is not None, "A entrada não apareceu no calendário"
        assert "150,00" in card_entrada.text and "Entrada" in card_entrada.text
        calendario.rolar_ate(card_entrada)
        calendario.pausa(2)

        card_saida = calendario.card_do_lancamento(saida.titulo)
        assert card_saida is not None, "A saída não apareceu no calendário"
        assert "80,50" in card_saida.text and "Saída" in card_saida.text
        calendario.rolar_ate(card_saida)
        calendario.pausa(2)
    finally:
        # 3. Apaga o que foi criado (mesmo que algo acima tenha falhado).
        if criados:
            financas.abrir_pela_pagina()
            financas.filtrar_por_dia(hoje)
            for titulo in criados:
                financas.excluir(titulo)

    # 4. Confere que saíram do calendário.
    calendario.abrir_pela_pagina()
    calendario.ir_para_o_mes(hoje)
    calendario.selecionar_dia(hoje)
    for titulo in criados:
        assert calendario.sem_lancamento(titulo), f"{titulo} continua no calendário"
