# Hive on Render (render.yaml): git, Python, Node.js, Claude Code and Hive in one image. Everything Hive keeps (his chat,
# rules, keys, the project) lives under HOME on the service's disk, so a restart or a redeploy loses nothing.
FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends git curl ca-certificates openssh-client \
 && curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
 && apt-get install -y --no-install-recommends nodejs \
 && npm install -g @anthropic-ai/claude-code \
 && rm -rf /var/lib/apt/lists/* /root/.npm
WORKDIR /opt/hive
COPY . .
RUN pip install --no-cache-dir ".[api]"
# HOME on the disk (render.yaml mounts it at /data); HIVE_HOST tells setup it is already always on
ENV HOME=/data/home HIVE_HOST=render PYTHONUNBUFFERED=1 IS_SANDBOX=1
CMD ["sh", "-c", "mkdir -p \"$HOME\" && exec hive boot"]
