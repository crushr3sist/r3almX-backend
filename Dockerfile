FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# Install the project into `/app`
WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy from the cache instead of linking since it's a mounted volume
ENV UV_LINK_MODE=copy

# Copy dependency files for installation
COPY uv.lock pyproject.toml ./

RUN uv sync --no-dev

COPY . .

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8080

# Command that allows for hot reloading with the mounted volume
CMD ["uv", "run", "fastapi", "dev", "r3almX_backend", "--reload", "--port=8080", "--host=0.0.0.0"]
