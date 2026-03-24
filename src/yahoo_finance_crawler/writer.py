import csv
import os


class CSVWriter:
    def __init__(self, output_path: str = "output.csv"):
        self.output_path = output_path

    def write(self, data: list[dict]) -> str:
        """
        Escreve os dados em um arquivo CSV.

        Args:
            data: Lista de dicts com symbol, name, price.

        Returns:
            Caminho do arquivo gerado.
        """
        if not data:
            print("Nenhum dado para salvar.")
            return self.output_path

        fieldnames = ["symbol", "name", "price"]

        with open(self.output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=fieldnames,
                quoting=csv.QUOTE_ALL,
                extrasaction="ignore",
            )
            writer.writeheader()
            writer.writerows(data)

        print(f"Arquivo salvo em: {os.path.abspath(self.output_path)}")
        return self.output_path
