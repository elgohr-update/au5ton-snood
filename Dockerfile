FROM python:3-alpine
ENV IS_DOCKER=Yes

RUN mkdir /config
RUN mkdir /data
RUN apk update && apk upgrade && apk add wget openjdk11-jre-headless 

WORKDIR /src
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

VOLUME [ "/config", "/data" ]
COPY . .

ENTRYPOINT [ "sh", "-c", "\"./indexer.py\"" ]