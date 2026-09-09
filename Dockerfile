FROM eclipse-temurin:17-jre-jammy
RUN apt-get update && apt-get install -y python3 python3-pip osmium-tool && rm -rf /var/lib/apt/lists/*
WORKDIR /app
RUN wget -q https://josm.openstreetmap.de/josm-tested.jar -O josm-tested.jar && \
    wget -q https://repo1.maven.org/maven2/org/python/jython-standalone/2.7.3/jython-standalone-2.7.3.jar -O jython.jar
COPY bot.py orchestrator.py ./
ENTRYPOINT ["python3", "orchestrator.py"]