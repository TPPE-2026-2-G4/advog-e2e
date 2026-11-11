"""Quadro de Atividades: cria atividade e etapa, arrasta, e apaga tudo.

Em produção só roda com E2E_PERMITIR_ESCRITA_PRODUCAO=true. A atividade e a etapa levam o
prefixo "E2E" e são apagadas mesmo se o teste falhar no meio.
"""

from datetime import date, timedelta

import pytest

from e2e.telas.atividades import Atividades
from e2e.telas.cadastros import gerar_marca

pytestmark = [pytest.mark.local, pytest.mark.producao, pytest.mark.escrita]


def test_cria_atividade_e_etapa_arrasta_e_exclui(sistema):
    quadro = Atividades(sistema.driver, sistema.ambiente)

    marca = gerar_marca()
    titulo = f"E2E Atividade {marca}"
    etapa_nova = f"E2E Etapa {marca}"
    prazo = date.today() + timedelta(days=7)

    atividade_criada = etapa_criada = False
    try:
        quadro.abrir_pela_pagina()

        # 1. Cria a atividade (ela nasce na primeira etapa do quadro).
        etapa_origem = quadro.criar_atividade(titulo, "Atividade criada pelo Selenium", prazo)
        atividade_criada = True

        # 2. Cria uma etapa nova.
        quadro.criar_etapa(etapa_nova)
        etapa_criada = True

        # 3. Arrasta a atividade para a etapa nova e confere que o movimento foi salvo.
        como = quadro.arrastar(titulo, etapa_nova)
        print(f"\n  arraste feito com: {como}")
        assert quadro.esta_na_etapa(titulo, etapa_nova), "A atividade não foi para a etapa nova"
        assert not quadro.esta_na_etapa(titulo, etapa_origem, segundos=1), (
            "A atividade continua na etapa de origem"
        )
        quadro.recarregar_pagina()
        assert quadro.esta_na_etapa(titulo, etapa_nova), "O movimento não foi salvo no servidor"

        # 4. Uma etapa com atividade não pode ser excluída: o sistema avisa.
        aviso = quadro.tentar_excluir_etapa(etapa_nova)
        assert "Não é possível excluir uma etapa" in aviso, aviso

        # 5. Exclui a atividade e, em seguida, a etapa.
        quadro.excluir_atividade(titulo)
        atividade_criada = False
        quadro.excluir_etapa(etapa_nova)
        etapa_criada = False
    finally:
        # Limpeza do que ainda existir (primeiro a atividade, depois a etapa).
        if atividade_criada or etapa_criada:
            quadro.abrir_pela_pagina()
            quadro.recarregar_pagina()
            if atividade_criada:
                quadro.excluir_atividade(titulo)
            if etapa_criada:
                quadro.excluir_etapa(etapa_nova)
