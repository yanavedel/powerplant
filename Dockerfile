FROM python:3.8

WORKDIR /app
COPY pyproject.toml ./app/pyproject.toml

RUN poetry install
COPY .. ./app
EXPOSE 8888