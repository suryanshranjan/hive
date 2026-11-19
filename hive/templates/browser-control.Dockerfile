FROM hive-browser:1
USER root
RUN apt-get update && apt-get install -y --no-install-recommends xvfb openbox x11vnc novnc && rm -rf /var/lib/apt/lists/*
USER pwuser
ENV DISPLAY=:97
