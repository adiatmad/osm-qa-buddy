FROM eclipse-temurin:17-jre-jammy

RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 python3-pip osmium-tool wget \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN python3 -m pip install --no-cache-dir shapely
# Use the official current tested JOSM release (the old 19613 snapshot is no longer hosted).
RUN mkdir -p /app/tools \
    && wget -q https://josm.openstreetmap.de/download/josm-tested.jar -O /app/tools/josm-tested.jar \
    && wget -q https://repo1.maven.org/maven2/org/python/jython-standalone/2.7.3/jython-standalone-2.7.3.jar -O /app/tools/jython-2.7.3.jar

COPY bot.py orchestrator.py preflight.py report.py /app/

ENV QABOT_WORK_DIR=/data/work
RUN mkdir -p /data/work

ENTRYPOINT ["python3", "/app/orchestrator.py"]
