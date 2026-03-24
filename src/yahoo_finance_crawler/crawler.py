import os
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException


CHROME_BINARY_PATHS = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/usr/bin/google-chrome",
    "/usr/bin/google-chrome-stable",
    "/usr/bin/chromium-browser",
    "/usr/bin/chromium",
    "/usr/lib/chromium/chromium",
]

CHROMEDRIVER_PATHS = [
    "/usr/bin/chromedriver",
    "/usr/lib/chromium/chromedriver",
]


@dataclass
class Stock:
    symbol: str
    name: str
    price: str

    def to_dict(self) -> dict:
        return {"symbol": self.symbol, "name": self.name, "price": self.price}


class ScreenerFilter(ABC):
    @abstractmethod
    def apply(self, driver, wait: WebDriverWait) -> None:
        pass


class RegionFilter(ScreenerFilter):
    def __init__(self, region: str):
        self._region = region

    def apply(self, driver, wait: WebDriverWait) -> None:
        self._open_dropdown(driver)
        self._type_region(driver, wait)
        self._select_option(driver, wait)
        self._confirm(driver, wait)

    def _open_dropdown(self, driver) -> None:
        try:
            driver.find_element(By.XPATH, "//button[contains(., 'Region')]").click()
            time.sleep(1)
        except NoSuchElementException:
            raise RuntimeError("Botão 'Region' não encontrado na página.")

    def _type_region(self, driver, wait: WebDriverWait) -> None:
        try:
            field = wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, "//input[@placeholder='Search' or @type='search']")
                )
            )
            field.clear()
            field.send_keys(self._region)
            time.sleep(1)
        except TimeoutException:
            pass

    def _select_option(self, driver, wait: WebDriverWait) -> None:
        xpath = (
            f"//label[contains(., '{self._region}')] | "
            f"//li[contains(., '{self._region}')] | "
            f"//span[contains(., '{self._region}')]"
        )
        try:
            wait.until(EC.element_to_be_clickable((By.XPATH, xpath))).click()
            time.sleep(1)
        except TimeoutException:
            raise RuntimeError(f"Região '{self._region}' não encontrada no dropdown.")

    def _confirm(self, driver, wait: WebDriverWait) -> None:
        try:
            wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[contains(., 'Apply') or contains(., 'Done')]")
                )
            ).click()
            time.sleep(2)
        except TimeoutException:
            pass


class TableParser:
    def parse(self, html: str) -> list[Stock]:
        soup = BeautifulSoup(html, "html.parser")
        table = soup.find("table")
        if not table:
            return []

        indices = self._resolve_column_indices(table)
        if not all(v is not None for v in indices.values()):
            return []

        return self._extract_rows(table, indices)

    def _resolve_column_indices(self, table) -> dict:
        headers = [th.get_text(strip=True).lower() for th in table.find_all("th")]
        indices = {"symbol": None, "name": None, "price": None}
        for i, h in enumerate(headers):
            if h == "symbol":
                indices["symbol"] = i
            elif h == "name":
                indices["name"] = i
            elif "price" in h:
                indices["price"] = i
        return indices

    def _extract_rows(self, table, indices: dict) -> list[Stock]:
        results = []
        tbody = table.find("tbody")
        if not tbody:
            return results

        for row in tbody.find_all("tr"):
            cells = row.find_all("td")
            try:
                symbol = cells[indices["symbol"]].get_text(strip=True)
                name = cells[indices["name"]].get_text(strip=True)
                price = cells[indices["price"]].get_text(strip=True) if indices["price"] is not None else ""
                if symbol and name:
                    results.append(Stock(symbol=symbol, name=name, price=price))
            except (IndexError, AttributeError):
                continue

        return results


class ChromeDriverFactory:
    def create(self, headless: bool) -> webdriver.Chrome:
        options = self._build_options(headless)
        service = self._build_service()
        if service:
            return webdriver.Chrome(service=service, options=options)
        return webdriver.Chrome(options=options)

    def _build_options(self, headless: bool) -> Options:
        options = Options()
        if headless:
            options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument(
            "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        binary = next((p for p in CHROME_BINARY_PATHS if os.path.exists(p)), None)
        if binary:
            options.binary_location = binary
        return options

    def _build_service(self) -> Service | None:
        driver = next((p for p in CHROMEDRIVER_PATHS if os.path.exists(p)), None)
        return Service(driver) if driver else None


class YahooFinanceCrawler:
    BASE_URL = "https://finance.yahoo.com/research-hub/screener/equity/"
    _DEFAULT_TIMEOUT = 30

    def __init__(self, headless: bool = True, driver_factory: ChromeDriverFactory = None):
        self._headless = headless
        self._driver_factory = driver_factory or ChromeDriverFactory()
        self._driver = None

    def scrape(self, screener_filter: ScreenerFilter) -> list[dict]:
        try:
            self._driver = self._driver_factory.create(self._headless)
            self._driver.get(self.BASE_URL)

            wait = WebDriverWait(self._driver, self._DEFAULT_TIMEOUT)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
            time.sleep(3)

            self._dismiss_consent_banner(wait)
            screener_filter.apply(self._driver, wait)

            time.sleep(3)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
            self._load_remaining_rows()

            stocks = TableParser().parse(self._driver.page_source)
            return [s.to_dict() for s in stocks]
        finally:
            if self._driver:
                self._driver.quit()
                self._driver = None

    def _dismiss_consent_banner(self, wait: WebDriverWait) -> None:
        try:
            WebDriverWait(self._driver, 5).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[contains(., 'Accept') or contains(., 'Agree') or contains(., 'Reject')]")
                )
            ).click()
            time.sleep(1)
        except TimeoutException:
            pass

    def _load_remaining_rows(self) -> None:
        while True:
            try:
                btn = self._driver.find_element(
                    By.XPATH, "//button[contains(., 'Show') and contains(., 'more')]"
                )
                self._driver.execute_script("arguments[0].click();", btn)
                time.sleep(2)
            except (NoSuchElementException, Exception):
                break