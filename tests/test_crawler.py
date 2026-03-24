import csv
import os
import tempfile
import pytest
from unittest.mock import MagicMock, patch
from selenium.common.exceptions import NoSuchElementException, TimeoutException

from yahoo_finance_crawler.crawler import YahooFinanceCrawler
from yahoo_finance_crawler.writer import CSVWriter


SAMPLE_HTML = """
<html><body>
<table>
  <thead>
    <tr>
      <th>Symbol</th>
      <th>Name</th>
      <th>Price (Intraday)</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>AMX.BA</td>
      <td>América Móvil, S.A.B. de C.V.</td>
      <td>2089.00</td>
    </tr>
    <tr>
      <td>NOKA.BA</td>
      <td>Nokia Corporation</td>
      <td>557.50</td>
    </tr>
  </tbody>
</table>
</body></html>
"""

EMPTY_HTML = "<html><body><p>No data</p></body></html>"

SAMPLE_DATA = [
    {"symbol": "AMX.BA", "name": "América Móvil, S.A.B. de C.V.", "price": "2089.00"},
    {"symbol": "NOKA.BA", "name": "Nokia Corporation", "price": "557.50"},
]


class TestParseTable:
    def setup_method(self):
        self.crawler = YahooFinanceCrawler()

    def test_parse_returns_correct_number_of_rows(self):
        assert len(self.crawler._parse_table(SAMPLE_HTML)) == 2

    def test_parse_returns_correct_symbol(self):
        result = self.crawler._parse_table(SAMPLE_HTML)
        assert result[0]["symbol"] == "AMX.BA"
        assert result[1]["symbol"] == "NOKA.BA"

    def test_parse_returns_correct_name(self):
        assert self.crawler._parse_table(SAMPLE_HTML)[0]["name"] == "América Móvil, S.A.B. de C.V."

    def test_parse_returns_correct_price(self):
        result = self.crawler._parse_table(SAMPLE_HTML)
        assert result[0]["price"] == "2089.00"
        assert result[1]["price"] == "557.50"

    def test_parse_empty_html_returns_empty_list(self):
        assert self.crawler._parse_table(EMPTY_HTML) == []

    def test_parse_html_without_tbody_returns_empty_list(self):
        assert self.crawler._parse_table("<table><thead><tr><th>Symbol</th></tr></thead></table>") == []

    def test_parse_result_has_expected_keys(self):
        for row in self.crawler._parse_table(SAMPLE_HTML):
            assert {"symbol", "name", "price"} <= row.keys()


class TestScrape:
    def _make_mock_driver(self, mock_chrome):
        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver
        mock_driver.page_source = SAMPLE_HTML
        # find_element raises NoSuchElementException (Selenium exception, handled gracefully)
        mock_driver.find_element.side_effect = NoSuchElementException("not found")
        mock_driver.find_elements.return_value = []
        return mock_driver

    @patch("yahoo_finance_crawler.crawler.webdriver.Chrome")
    @patch("yahoo_finance_crawler.crawler.time.sleep", return_value=None)
    def test_scrape_returns_data(self, mock_sleep, mock_chrome):
        mock_driver = self._make_mock_driver(mock_chrome)
        with patch("yahoo_finance_crawler.crawler.WebDriverWait") as mock_wait:
            mock_wait.return_value.until.return_value = MagicMock()
            mock_wait.return_value.__enter__ = lambda s: s
            result = YahooFinanceCrawler(headless=True).scrape("Argentina")
        assert len(result) == 2
        assert result[0]["symbol"] == "AMX.BA"

    @patch("yahoo_finance_crawler.crawler.webdriver.Chrome")
    @patch("yahoo_finance_crawler.crawler.time.sleep", return_value=None)
    def test_scrape_closes_driver_on_success(self, mock_sleep, mock_chrome):
        mock_driver = self._make_mock_driver(mock_chrome)
        with patch("yahoo_finance_crawler.crawler.WebDriverWait") as mock_wait:
            mock_wait.return_value.until.return_value = MagicMock()
            YahooFinanceCrawler(headless=True).scrape("Argentina")
        mock_driver.quit.assert_called_once()

    @patch("yahoo_finance_crawler.crawler.webdriver.Chrome")
    @patch("yahoo_finance_crawler.crawler.time.sleep", return_value=None)
    def test_scrape_closes_driver_on_exception(self, mock_sleep, mock_chrome):
        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver
        mock_driver.get.side_effect = RuntimeError("Connection error")
        with patch("yahoo_finance_crawler.crawler.WebDriverWait"):
            with pytest.raises(RuntimeError):
                YahooFinanceCrawler(headless=True).scrape("Argentina")
        mock_driver.quit.assert_called_once()


class TestCSVWriter:
    def test_write_creates_file(self):
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            path = f.name
        try:
            CSVWriter(output_path=path).write(SAMPLE_DATA)
            assert os.path.exists(path)
        finally:
            os.unlink(path)

    def test_write_correct_header(self):
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
            path = f.name
        try:
            CSVWriter(output_path=path).write(SAMPLE_DATA)
            with open(path, newline="", encoding="utf-8") as f:
                assert csv.DictReader(f).fieldnames == ["symbol", "name", "price"]
        finally:
            os.unlink(path)

    def test_write_correct_rows(self):
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
            path = f.name
        try:
            CSVWriter(output_path=path).write(SAMPLE_DATA)
            with open(path, newline="", encoding="utf-8") as f:
                rows = list(csv.DictReader(f))
            assert len(rows) == 2
            assert rows[0]["symbol"] == "AMX.BA"
        finally:
            os.unlink(path)

    def test_write_empty_data_does_not_crash(self):
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
            path = f.name
        try:
            CSVWriter(output_path=path).write([])
            assert os.path.exists(path)
        finally:
            os.unlink(path)

    def test_write_returns_output_path(self):
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
            path = f.name
        try:
            assert CSVWriter(output_path=path).write(SAMPLE_DATA) == path
        finally:
            os.unlink(path)
