# The builders' sandbox (hive/sandbox.py): what a builder needs to build and test, and nothing of the owner's.
# Each builder runs in its own container of this image, seeing only its run folder (/hive-run) and Hive's own code
# (/opt/hive, read-only): never ~/.hive (his keys, his chat), his other projects, or the rest of his computer.
# HOME is writable by any user: on Linux a builder runs as the owner's own user, so the files it writes stay his.
# Changing this file? Bump IMAGE in hive/sandbox.py, so a machine with the old image builds the new one.
FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends git curl ca-certificates \
 && curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
 && apt-get install -y --no-install-recommends nodejs \
 && npm install -g @anthropic-ai/claude-code @openai/codex @google/gemini-cli \
 && pip install --no-cache-dir pytest \
 && useradd -m -u 1000 hive && chmod 1777 /home/hive \
 && rm -rf /var/lib/apt/lists/* /root/.npm
RUN pip install --no-cache-dir "cryptography>=43" tzdata
USER hive
ENV HOME=/home/hive PYTHONPATH=/opt/hive PYTHONUNBUFFERED=1 IS_SANDBOX=1
WORKDIR /hive-run
