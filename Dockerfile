FROM eclipse-temurin:17-jre-jammy

RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 python3-pip osmium-tool wget \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN python3 -m pip install --no-cache-dir shapely
# Pin the JOSM build used by the QA instrument. Do not silently follow josm-tested.jar updates.
RUN wget -q https://josm.openstreetmap.de/download/josm-snapshot-19613.jar -O /app/josm-tested.jar
RUN wget -q https://repo1.maven.org/maven2/org/python/jython-standalone/2.7.3/jython-standalone-2.7.3.jar -O /app/jython.jar

COPY bot.py orchestrator.py preflight.py report.py /app/

ENV QABOT_WORK_DIR=/data/work
RUN mkdir -p /data/work

ENTRYPOINT ["python3", "/app/orchestrator.py"]
