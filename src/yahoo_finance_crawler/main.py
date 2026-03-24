import argparse
import sys

from yahoo_finance_crawler.crawler import YahooFinanceCrawler, RegionFilter
from yahoo_finance_crawler.writer import CSVWriter


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Yahoo Finance Equity Screener Crawler")
    parser.add_argument("--region", required=True, help="Região para filtrar (ex: Argentina, Brazil)")
    parser.add_argument("--output", default="output.csv", help="Arquivo CSV de saída")
    parser.add_argument("--no-headless", action="store_true", help="Abre o browser visível")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    print(f"Iniciando crawler para região: {args.region}")

    crawler = YahooFinanceCrawler(headless=not args.no_headless)
    screener_filter = RegionFilter(region=args.region)
    data = crawler.scrape(screener_filter)

    if not data:
        print("Nenhum dado encontrado.")
        sys.exit(1)

    print(f"{len(data)} registros encontrados.")
    CSVWriter(output_path=args.output).write(data)


if __name__ == "__main__":
    main()