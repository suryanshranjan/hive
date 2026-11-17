FROM mcr.microsoft.com/playwright/python:v1.64.1-noble
RUN pip install --no-cache-dir playwright==1.64.1
RUN mkdir /profile && chown pwuser:pwuser /profile
USER pwuser
ENV PYTHONPATH=/opt/hive PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /home/pwuser
ENTRYPOINT ["python", "-m", "hive.browser_worker"]
