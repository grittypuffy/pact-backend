FROM python:3.13-slim-bookworm

RUN pip install poetry

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

WORKDIR /pact-backend

RUN mkdir uploads

RUN apt-get update

RUN apt-get install build-essential ca-certificates libasound2-dev libssl-dev wget

COPY pyproject.toml poetry.lock ./

RUN touch README.md

RUN poetry env use python3.13

COPY pact_backend/ ./pact_backend/

RUN poetry install

RUN poetry add gunicorn

EXPOSE 80

EXPOSE 443

EXPOSE 8000

ENTRYPOINT ["poetry", "run", "python", "-m", "gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker","-b", "0.0.0.0:8000","pact_backend.server:app"]
