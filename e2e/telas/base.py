"""Base de todas as telas: ações do navegador com pausa, destaque e espera."""

from __future__ import annotations

import time
from urllib.parse import urljoin

from selenium.common.exceptions import (
    ElementClickInterceptedException,
    MoveTargetOutOfBoundsException,
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from e2e import config
from e2e.config import Ambiente

Localizador = tuple[str, str]

# Define o valor de um <input> do jeito que o React percebe (necessário para type="date").
_JS_DEFINIR_VALOR = """
const el = arguments[0];
const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
setter.call(el, arguments[1]);
el.dispatchEvent(new Event('input', { bubbles: true }));
el.dispatchEvent(new Event('change', { bubbles: true }));
"""


def xpath_texto(texto: str) -> str:
    """Literal XPath seguro para textos com aspas."""
    if "'" not in texto:
        return f"'{texto}'"
    if '"' not in texto:
        return f'"{texto}"'
    partes = texto.split("'")
    return "concat(" + ', "\'", '.join(f"'{parte}'" for parte in partes) + ")"


class Tela:
    def __init__(self, driver: WebDriver, ambiente: Ambiente):
        self.driver = driver
        self.ambiente = ambiente
        self.espera = WebDriverWait(
            driver,
            ambiente.timeout,
            ignored_exceptions=(StaleElementReferenceException,),
        )

    # ── ritmo da demonstração ────────────────────────────────────────────
    def pausa(self, fator: float = 1.0) -> None:
        """Espera E2E_DELAY segundos (multiplicado por `fator`) para a plateia acompanhar."""
        if config.DELAY > 0 and fator > 0:
            time.sleep(config.DELAY * fator)

    def _destacar(self, elemento: WebElement) -> None:
        if not config.DESTACAR:
            return
        try:
            self.driver.execute_script(
                "arguments[0].style.outline='3px solid #e11d48';"
                "arguments[0].style.outlineOffset='2px';",
                elemento,
            )
            self.pausa(0.4)
            self.driver.execute_script(
                "arguments[0].style.outline='';arguments[0].style.outlineOffset='';", elemento
            )
        except StaleElementReferenceException:
            pass  # a página re-renderizou; o destaque é só visual

    def afastar_mouse(self) -> None:
        """Tira o ponteiro de cima da barra lateral.

        A barra lateral do sistema expande quando o mouse passa por cima e, expandida, cobre
        a parte esquerda do conteúdo (botões, abas). Mover o ponteiro para uma área livre da
        página faz a barra recolher, como se alguém clicasse numa área em branco.
        """
        try:
            largura = self.driver.execute_script("return window.innerWidth;")
            altura = self.driver.execute_script("return window.innerHeight;")
            acoes = ActionChains(self.driver)
            acoes.w3c_actions.pointer_action.move_to_location(int(largura * 0.6), int(altura * 0.6))
            acoes.perform()
        except MoveTargetOutOfBoundsException:
            return
        time.sleep(0.5)  # a barra leva 0,3 s para recolher

    # ── navegação ────────────────────────────────────────────────────────
    def abrir(self, caminho: str = "/") -> None:
        self.driver.get(urljoin(self.ambiente.url + "/", caminho.lstrip("/")))
        self.afastar_mouse()
        self.pausa()

    def url_contem(self, trecho: str) -> None:
        self.espera.until(EC.url_contains(trecho))

    @property
    def caminho_atual(self) -> str:
        return self.driver.current_url.replace(self.ambiente.url, "", 1)

    # ── esperas ──────────────────────────────────────────────────────────
    def esperar_visivel(self, localizador: Localizador) -> WebElement:
        return self.espera.until(EC.visibility_of_element_located(localizador))

    def esperar_clicavel(self, localizador: Localizador) -> WebElement:
        return self.espera.until(EC.element_to_be_clickable(localizador))

    def esperar_sumir(self, localizador: Localizador) -> None:
        self.espera.until(EC.invisibility_of_element_located(localizador))

    def existe(self, localizador: Localizador, segundos: float = 3) -> bool:
        try:
            WebDriverWait(self.driver, segundos).until(
                EC.visibility_of_element_located(localizador)
            )
            return True
        except TimeoutException:
            return False

    def esperar_texto(self, texto: str, tag: str = "*") -> WebElement:
        return self.esperar_visivel((By.XPATH, f"//{tag}[contains(., {xpath_texto(texto)})]"))

    def esperar_titulo(self, texto: str) -> WebElement:
        """Espera um <h1> com o texto indicado (confirma que a página carregou)."""
        return self.esperar_visivel(
            (By.XPATH, f"//h1[contains(normalize-space(.), {xpath_texto(texto)})]")
        )

    # ── interações ───────────────────────────────────────────────────────
    def rolar_ate(self, elemento: WebElement) -> None:
        self.driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", elemento
        )
        self.pausa(0.5)

    def clicar(self, alvo: Localizador | WebElement, pausa: float = 1.0) -> None:
        for _ in range(3):
            elemento = self.esperar_clicavel(alvo) if isinstance(alvo, tuple) else alvo
            self.rolar_ate(elemento)
            self._destacar(elemento)
            try:
                elemento.click()
                break
            except (ElementClickInterceptedException, StaleElementReferenceException):
                # Algo cobriu o botão (barra lateral expandida, toast, animação): tira o
                # mouse da frente e tenta de novo.
                self.afastar_mouse()
        else:
            raise ElementClickInterceptedException(f"Não consegui clicar em {alvo}")
        self.pausa(pausa)

    def limpar(self, elemento: WebElement) -> None:
        elemento.send_keys(Keys.CONTROL, "a")
        elemento.send_keys(Keys.DELETE)

    def digitar(self, alvo: Localizador | WebElement, texto: str, limpar: bool = True) -> None:
        """Digita letra por letra (E2E_DELAY_DIGITACAO) para dar para acompanhar."""
        elemento = self.esperar_visivel(alvo) if isinstance(alvo, tuple) else alvo
        self.rolar_ate(elemento)
        self._destacar(elemento)
        if limpar:
            self.limpar(elemento)
        for letra in texto:
            elemento.send_keys(letra)
            if config.DELAY_DIGITACAO > 0:
                time.sleep(config.DELAY_DIGITACAO)
        self.pausa(0.5)

    def definir_valor(self, alvo: Localizador | WebElement, valor: str) -> None:
        """Preenche campos que o send_keys não atende bem (ex.: <input type="date">)."""
        elemento = self.esperar_visivel(alvo) if isinstance(alvo, tuple) else alvo
        self.rolar_ate(elemento)
        self._destacar(elemento)
        self.driver.execute_script(_JS_DEFINIR_VALOR, elemento, valor)
        self.pausa(0.5)

    def fechar_dialogo(self) -> None:
        """Fecha o modal aberto (Esc; se não fechar, clica em Cancelar)."""
        dialogo = (By.CSS_SELECTOR, "[role='dialog']")
        ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
        try:
            WebDriverWait(self.driver, 2).until(EC.invisibility_of_element_located(dialogo))
        except TimeoutException:
            self.clicar((By.XPATH, "//*[@role='dialog']//button[normalize-space(.)='Cancelar']"))
            self.esperar_sumir(dialogo)
        self.pausa(0.5)

    def botao(self, texto: str) -> Localizador:
        return (By.XPATH, f"//button[normalize-space(.)={xpath_texto(texto)}]")

    def link(self, texto: str) -> Localizador:
        return (By.XPATH, f"//a[normalize-space(.)={xpath_texto(texto)}]")

    def por_aria_label(self, rotulo: str, tag: str = "*") -> Localizador:
        return (By.XPATH, f"//{tag}[@aria-label={xpath_texto(rotulo)}]")

    # ── avisos (Toast) ───────────────────────────────────────────────────
    def aviso(self, papel: str = "alert") -> WebElement:
        """Aviso flutuante no topo da tela (role=alert para erros, role=status para sucesso)."""
        return self.esperar_visivel((By.CSS_SELECTOR, f"#toast-viewport [role='{papel}']"))

    def fechar_avisos(self) -> None:
        for botao in self.driver.find_elements(
            By.CSS_SELECTOR, "#toast-viewport button[aria-label='Fechar aviso']"
        ):
            try:
                botao.click()
            except Exception:  # noqa: BLE001 - o aviso pode ter sumido sozinho
                pass
