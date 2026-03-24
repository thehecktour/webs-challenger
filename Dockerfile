FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    curl \
    --no-install-recommends \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN curl -sSL https://install.python-poetry.org | python3 - \
    && ln -s /root/.local/bin/poetry /usr/local/bin/poetry

WORKDIR /app

COPY . .

RUN pip install -e ".[dev]" --no-cache-dir

VOLUME ["/app/output"]

ENTRYPOINT ["python3", "-m", "yahoo_finance_crawler.main"]
CMD ["--help"]