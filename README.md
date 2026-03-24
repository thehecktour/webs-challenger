# Yahoo Finance Crawler

Crawler em Python para coletar **symbol**, **name** e **price (intraday)** do [Yahoo Finance Equity Screener](https://finance.yahoo.com/research-hub/screener/equity/), com filtro por região.

Utiliza **Selenium**, **BeautifulSoup** e **orientação a objetos**.

---

## Exemplo de saída

```csv
"symbol","name","price"
"AMX.BA","América Móvil, S.A.B. de C.V.","2089.00"
"NOKA.BA","Nokia Corporation","557.50"
```

---

## Rodando com Docker (recomendado)

Não precisa instalar Python, Chrome ou nenhuma dependência — tudo roda dentro do container.

**Build:**
```bash
docker build -t yahoo-crawler .
```

**Uso:**
```bash
# Argentina → output.csv na pasta atual
docker run --rm -v "$(pwd)/output:/app/output" yahoo-crawler \
  --region "Argentina" --output /app/output/output.csv

# Brazil → brazil.csv
docker run --rm -v "$(pwd)/output:/app/output" yahoo-crawler \
  --region "Brazil" --output /app/output/brazil.csv
```

O CSV gerado fica na pasta `output/` do seu diretório atual.

---

## Rodando localmente

### Pré-requisitos

- Python 3.12+
- Google Chrome instalado
- [Poetry](https://python-poetry.org/) (opcional)

### Instalação

```bash
git clone https://github.com/seu-usuario/yahoo-finance-crawler.git
cd yahoo-finance-crawler

pip install -e ".[dev]"
```

### Uso

```bash
python3 -m yahoo_finance_crawler.main --region "Argentina"
```

### Parâmetros

| Parâmetro       | Obrigatório | Descrição                                      |
|-----------------|-------------|------------------------------------------------|
| `--region`      | ✅ Sim      | Nome da região (ex: `Argentina`, `Brazil`)     |
| `--output`      | ❌ Não      | Caminho do CSV de saída (padrão: `output.csv`) |
| `--no-headless` | ❌ Não      | Abre o browser visivelmente (útil p/ debug)    |

### Exemplos

```bash
# Argentina → output.csv
python3 -m yahoo_finance_crawler.main --region "Argentina"

# Brazil → brazil.csv
python3 -m yahoo_finance_crawler.main --region "Brazil" --output brazil.csv
```

---

## Estrutura do projeto

```
yahoo-finance-crawler/
├── src/
│   └── yahoo_finance_crawler/
│       ├── __init__.py
│       ├── crawler.py   # Selenium + BeautifulSoup + design patterns
│       ├── writer.py    # Geração do CSV
│       └── main.py      # Entry point (argparse)
├── tests/
│   └── test_crawler.py  # Testes unitários
├── Dockerfile
├── pyproject.toml
└── README.md
```

---

## Testes

```bash
pytest tests/ -v
```

---

## Como funciona

1. **`YahooFinanceCrawler`** orquestra o fluxo via Selenium
2. **`RegionFilter`** (Strategy) aplica o filtro de região na interface do Yahoo Finance
3. O crawler carrega todos os resultados clicando em "Show more"
4. **`TableParser`** usa BeautifulSoup para extrair os dados da tabela
5. **`CSVWriter`** salva os dados em CSV com aspas em todos os campos
