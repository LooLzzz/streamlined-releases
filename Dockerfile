FROM ghcr.io/astral-sh/uv:python3.12-bookworm

WORKDIR /app
COPY . .

RUN uv pip install --system -e .

ENTRYPOINT ["python3", "-m", "streamlined_releases"]