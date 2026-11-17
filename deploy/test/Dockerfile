# Build the normal builder image first: docker build -t hive-builder:3 deploy/builder
# This adds test dependencies only. Personal credentials are never copied into it.
FROM hive-builder:3
USER root
RUN python3 -m pip install --no-cache-dir "cryptography>=43" tzdata "PyYAML>=6" setuptools wheel
USER hive
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 IS_SANDBOX=1 HIVE_EMBED=0 HIVE_TTS=off
WORKDIR /source
CMD ["python3", "tests/container_entry.py", "--all", "--shell"]
