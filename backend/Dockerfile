FROM python:3.13-slim

WORKDIR /app

# System deps needed for psycopg2 and scientific libs
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run as an unprivileged user. Containers default to root, which violates
# CIS Docker Benchmark 4.1 and the least-privilege principle: a process
# escaping the container would do so with root on the node. UID 1000 is
# chosen explicitly so the Kubernetes securityContext can assert the same
# value (runAsUser: 1000) and fail closed if that ever regresses.
RUN useradd --create-home --uid 1000 appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# No --reload: that is a development file-watcher which spawns an extra
# process and reloads on source change. Immutable container images should
# never hot-reload.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
