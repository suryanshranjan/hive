# Hive on Render (render.yaml): git, Python, Node.js, Claude Code and Hive in one image. Everything Hive keeps (his chat,
# rules, keys, the project) lives under HOME on the service's disk, so a restart or a redeploy loses nothing.
FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends git curl ca-certificates openssh-client \
 && curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
 && apt-get install -y --no-install-recommends nodejs \
 && npm install -g @anthropic-ai/claude-code \
 && useradd -m -u 1000 hive  && rm -rf /var/lib/apt/lists/* /root/.npm
WORKDIR /opt/hive
COPY . .
RUN pip install --no-cache-dir ".[api,secure,memory,speech]"   # keys encrypted; recall by meaning; voice replies
# HOME on the disk (render.yaml mounts it at /data); HIVE_HOST tells setup it is already always on
ENV HOME=/data/home HIVE_HOST=render PYTHONUNBUFFERED=1 HIVE_MODELS=/data/models
# Render's disk arrives owned by root: the start makes HOME his user's (once), then Hive and its builders run as that
# user, never as root (the audit, Nov 15: everything ran as root, with Claude Code told it was a sandbox).
CMD ["sh", "-c", "mkdir -p \"$HOME\" \"$HIVE_MODELS\" && chown hive:hive \"$HIVE_MODELS\" && { [ \"$(stat -c %U \"$HOME\")\" = hive ] || chown -R hive:hive \"$HOME\"; } && exec runuser -u hive -- env HOME=\"$HOME\" hive boot"]
