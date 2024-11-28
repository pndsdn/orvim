FROM python:3.12

WORKDIR /app
COPY docker/connector.requirements r.txt
RUN --mount=type=cache,target=/root/.cache/pip pip install -r r.txt

WORKDIR /app/src
COPY src/common common
COPY src/connector_service connector_service

CMD [ "python", "-m", "connector_service.main" ]