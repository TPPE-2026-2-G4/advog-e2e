"""Configuração dos testes, lida do arquivo .env (veja .env.example)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parent.parent
load_dotenv(RAIZ / ".env")

AMBIENTES = ("local", "producao")
ARTEFATOS = RAIZ / "artefatos"


def _texto(nome: str, padrao: str = "") -> str:
    return os.getenv(nome, padrao).strip()


def _booleano(nome: str, padrao: bool) -> bool:
    valor = _texto(nome)
    if not valor:
        return padrao
    return valor.lower() in {"1", "true", "sim", "yes", "on"}


def _numero(nome: str, padrao: float) -> float:
    valor = _texto(nome)
    try:
        return float(valor.replace(",", ".")) if valor else padrao
    except ValueError as erro:
        raise ValueError(f"{nome} deve ser um número, mas está '{valor}'.") from erro


# Ritmo da demonstração ------------------------------------------------------
DELAY = _numero("E2E_DELAY", 1.5)
DELAY_DIGITACAO = _numero("E2E_DELAY_DIGITACAO", 0.05)
DESTACAR = _booleano("E2E_DESTACAR", True)
HEADLESS = _booleano("E2E_HEADLESS", False)

PERMITIR_ESCRITA_PRODUCAO = _booleano("E2E_PERMITIR_ESCRITA_PRODUCAO", False)
EXIGIR_TODAS_AS_PAGINAS = _booleano("E2E_EXIGIR_TODAS_AS_PAGINAS", True)


@dataclass(frozen=True)
class Ambiente:
    nome: str
    url: str
    api_url: str
    email: str
    senha: str
    timeout: float

    @property
    def eh_producao(self) -> bool:
        return self.nome == "producao"


def ambiente_padrao() -> str:
    nome = _texto("E2E_AMBIENTE", "local").lower()
    if nome not in AMBIENTES:
        raise ValueError(f"E2E_AMBIENTE deve ser um de {AMBIENTES}, mas está '{nome}'.")
    return nome


def _url_valida(url: str) -> bool:
    return url.startswith(("http://", "https://")) and "PREENCHER" not in url.upper()


def obter_ambiente(nome: str) -> Ambiente:
    """Monta o ambiente ('local' ou 'producao') e avisa claramente o que falta no .env."""
    sufixo = nome.upper()
    url = _texto(f"URL_{sufixo}").rstrip("/")
    if not _url_valida(url):
        raise ValueError(
            f"Preencha URL_{sufixo} no arquivo .env (ex.: https://meu-site.com). "
            f"Valor atual: '{url or 'vazio'}'."
        )

    timeout_padrao = _numero("E2E_TIMEOUT", 20)
    timeout = _numero("E2E_TIMEOUT_PRODUCAO", 60) if nome == "producao" else timeout_padrao

    return Ambiente(
        nome=nome,
        url=url,
        api_url=_texto(f"API_URL_{sufixo}").rstrip("/"),
        email=_texto(f"EMAIL_{sufixo}"),
        senha=_texto(f"SENHA_{sufixo}"),
        timeout=timeout,
    )
