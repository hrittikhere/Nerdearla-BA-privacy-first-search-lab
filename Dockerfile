FROM ghcr.io/astral-sh/uv:0.8.22 AS uv
FROM python:3.12.11-slim-bookworm
COPY --from=uv /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy PATH="/app/.venv/bin:$PATH"
WORKDIR /app
COPY pyproject.toml uv.lock README.md ./
COPY src ./src
RUN uv sync --frozen --no-dev --no-editable
RUN useradd --uid 10001 --create-home lab && mkdir /state && chown lab:lab /state
USER lab
ENV LAB_INDEX_DIR=/state
ENTRYPOINT ["privacy-lab"]
CMD ["serve"]
