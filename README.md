# advog-e2e

Testes de ponta a ponta (Selenium + pytest) do frontend do Advog. O navegador abre de verdade,
navega pelo site e confere o que aparece na tela, com pausas para dar para acompanhar.

## 1. Instalação

Requisitos: [uv](https://docs.astral.sh/uv/) e Python 3.11+. O Chrome e o driver são baixados
sozinhos pelo Selenium na primeira execução (se o Chrome já estiver instalado, ele é usado).

```bash
cd advog-e2e
uv sync
cp .env.example .env     # depois preencha o .env (próximo passo)
```

## 2. Preencher o `.env`

O `.env` não vai para o git (tem senhas). Os campos principais:

| Variável | O que colocar |
|---|---|
| `URL_LOCAL` | URL do frontend rodando na sua máquina (ex.: `http://localhost:3000`) |
| `URL_PRODUCAO` | **URL do frontend em produção** (ex.: `https://advog-web.vercel.app`). Sem barra no final |
| `API_URL_LOCAL` / `API_URL_PRODUCAO` | URL da API (opcional). Em produção serve para "acordar" o Render antes dos testes |
| `EMAIL_LOCAL` / `SENHA_LOCAL` | Usuário de teste do ambiente local |
| `EMAIL_PRODUCAO` / `SENHA_PRODUCAO` | Usuário de teste de produção |

Use um usuário **dedicado aos testes**. Para a tour passar por todas as páginas, ele precisa
ter acesso a todas (administrador). Se faltar alguma URL ou credencial, o teste para dizendo
exatamente o que preencher.

## 3. Rodando

```bash
uv run pytest                          # ambiente definido em E2E_AMBIENTE (padrão: local)
uv run pytest --ambiente local         # contra URL_LOCAL
uv run pytest --ambiente producao      # contra URL_PRODUCAO
uv run pytest -m producao              # filtra pela tag
uv run pytest tests/test_03_tour_pelo_sistema.py   # só a tour pelas páginas
```

### Tags (`local` e `producao`)

Cada teste declara onde pode rodar com `pytest.mark`:

```python
pytestmark = [pytest.mark.local, pytest.mark.producao]  # roda nos dois ambientes
```

- Um teste com as duas tags roda **uma vez por ambiente**, e o ambiente aparece no nome:
  `test_landing_page_percorre_as_secoes[producao]`.
- `--ambiente` escolhe qual dos dois executar; o outro é ignorado.
- A tag `escrita` marca testes que **criam e apagam dados**. Em produção eles são pulados a
  menos que `E2E_PERMITIR_ESCRITA_PRODUCAO=true` (veja "Cuidados com produção").

## 4. Ritmo da demonstração (delay)

Tudo é controlado no `.env`:

| Variável | Efeito | Padrão |
|---|---|---|
| `E2E_DELAY` | Pausa (segundos) depois de cada clique, navegação e preenchimento | `1.5` |
| `E2E_DELAY_DIGITACAO` | Pausa (segundos) entre cada letra digitada | `0.05` |
| `E2E_DESTACAR` | Contorna em vermelho o elemento que o teste vai usar | `true` |
| `E2E_HEADLESS` | `false` mostra o navegador; `true` roda sem janela | `false` |

Para apresentar, `E2E_DELAY=2` e `E2E_DELAY_DIGITACAO=0.08` ficam bons. Para rodar rápido
(ex.: em CI), use `E2E_DELAY=0`, `E2E_DELAY_DIGITACAO=0` e `E2E_HEADLESS=true`. Também dá para
mudar só numa execução:

```bash
E2E_DELAY=3 uv run pytest tests/test_03_tour_pelo_sistema.py
```

## 5. O que é testado

| Arquivo | O que faz |
|---|---|
| `test_01_paginas_publicas.py` | Landing page (percorre o menu: Início, Áreas, Sobre, Equipe, Contato), login, esqueci a senha, primeiro acesso, redefinir senha |
| `test_02_autenticacao.py` | Rota protegida redireciona ao login, login inválido mostra aviso, login válido e saída |
| `test_03_tour_pelo_sistema.py` | **Passa por todas as páginas do menu e pelo Perfil**, conferindo o conteúdo de cada uma (somente leitura, ver tabela abaixo). Não para na primeira falha: segue até o fim e lista todas as páginas com problema. Confere também que "Próximo Prazo" é obrigatório no processo |
| `test_04_cadastros.py` | Cria um cliente, busca, abre os detalhes, cria um processo para ele, e **apaga os dois** no fim |
| `test_05_lancamentos.py` | Cria um lançamento de **entrada** e um de **saída** em Finanças, abre o **Calendário** no mês e no dia deles e confere título, tipo e valor de cada um; depois **apaga os dois** e confere que sumiram do calendário |
| `test_06_atividades.py` | No Quadro de Atividades: cria uma **atividade** e uma **etapa**, **arrasta** a atividade para a etapa nova (e confere que o movimento foi salvo, recarregando a página), confere que o sistema **barra a exclusão** de etapa com atividade, e então **apaga a atividade e a etapa** |

### O que o tour confere em cada página

| Página | Conferido |
|---|---|
| Início | Resumo de processos carrega |
| Processos | Lista, busca, abre e fecha "Novo Processo" |
| Atividades | Abre e fecha "Nova Atividade" |
| Finanças | Cards (Receita, Despesas, Saldo, A Receber), gráficos e lista de lançamentos; troca o período do fluxo de caixa; abre e fecha "Novo Lançamento" |
| Calendário | Indicadores; "Próximo mês" e "Mês anterior" mudam o mês exibido |
| Clientes | Busca; abre e fecha "Novo Cliente" |
| Equipe | Totais de usuários, tabelas de membros, cargos e produtividade; abre e fecha "Adicionar Usuário" |
| Site | Percorre todas as abas |
| Ajustes | Seções de notificações e preferências, e os seletores de configuração |
| Perfil | Nome preenchido, **e-mail igual ao do usuário logado**, campos de senha |

Os modais são fechados sem salvar. Para ver a lista na tela, rode com `-s`
(`uv run pytest tests/test_03_tour_pelo_sistema.py -s`): cada página concluída imprime um ✔.

### Barra lateral

A barra lateral do sistema expande quando o mouse passa por cima e, aberta, cobre o começo do
conteúdo. Por isso o teste tira o ponteiro de cima dela (move para uma área livre da página)
depois de cada navegação e sempre que um clique é bloqueado, e só então segue. Em modo headless
o Chrome é configurado para se comportar como um desktop com mouse, para o resultado ser o
mesmo com e sem janela.

## 6. Cuidados com produção

- **Dados reais:** o teste `escrita` cria dados de verdade no banco. Tudo que ele cria tem o
  prefixo `E2E` e é apagado mesmo se o teste falhar no meio. Única exceção: o lançamento usa uma categoria que já existe; só se não houver nenhuma é criada a categoria "E2E Teste", que fica cadastrada. Mesmo assim, só ligue
  `E2E_PERMITIR_ESCRITA_PRODUCAO=true` quando for realmente necessário.
- **Render dormindo:** com `API_URL_PRODUCAO` preenchida, o teste chama `/health` e espera a API
  acordar (pode levar cerca de 1 minuto). `E2E_TIMEOUT_PRODUCAO` controla a espera por elemento.
- **Limite de requisições:** a API limita algumas rotas (ex.: 5 cadastros de cliente por
  minuto). Não rode os testes em paralelo.

## 7. Quando um teste falha

Um screenshot e o HTML da página ficam em `artefatos/` (ignorado pelo git), com a data e o
nome do teste.

## Estrutura

```
advog-e2e/
  conftest.py            # --ambiente, tags local/producao, navegador, screenshot em falha
  pyproject.toml
  .env.example           # modelo do .env (URLs, credenciais, delay)
  e2e/
    config.py            # lê o .env
    telas/
      base.py            # cliques, digitação e esperas com pausa/destaque
      publicas.py        # landing, login, senhas
      sistema.py         # menu lateral, perfil, sair
      cadastros.py       # clientes e processos (criar/excluir)
  tests/
```

## Padrões usados

- Localizadores por texto visível, `aria-label` e `id` (não por classe CSS, que muda a cada build).
- Esperas explícitas (`WebDriverWait`), nunca `sleep` para esperar a página; as únicas pausas
  fixas são o `E2E_DELAY` da demonstração.
- Lint: `uv run ruff check .` e `uv run ruff format .`.
