FROM python:3-alpine
ENV IS_DOCKER=Yes
LABEL org.opencontainers.image.source https://github.com/au5ton/snood

RUN mkdir /config
RUN mkdir -p /data/noods
RUN apk update && apk upgrade && apk add wget openjdk11-jre-headless fdupes

WORKDIR /src
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

VOLUME [ "/config", "/data" ]
COPY . .
RUN chmod +x /src/entrypoint.sh
RUN chmod +x /src/indexer.py
RUN chmod +x /src/ripper.py
RUN chmod +x /src/snood/youtube-dl
RUN chmod +x /src/snood/ripme.jar

ENTRYPOINT [ "sh", "-c", "/src/entrypoint.sh" ]