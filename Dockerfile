FROM python:3.10.2-slim

ENV LC_ALL="C.UTF-8"
ENV LANG="C.UTF-8"

ENV PYTHONUNBUFFERED="1"
ENV PYTHONFAULTHANDLER="1"
ENV PIP_NO_CACHE_DIR="false"
ENV PIP_DISABLE_PIP_VERSION_CHECK="on"
ENV PIP_DEFAULT_TIMEOUT="100"

ENV POETRY_VERSION=1.1.12
ENV POETRY_HOME="/opt/poetry"
ENV PATH="${POETRY_HOME}/bin:${PATH}"

# System deps:
RUN pip install --upgrade pip
RUN apt-get --allow-releaseinfo-change update && \
    apt-get install curl -y && \
    curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/$POETRY_VERSION/get-poetry.py | python - && \
    apt-get remove curl -y && \
    apt-get autoremove -y && \
    apt-get clean

# RUN pip install "poetry==$POETRY_VERSION"

# Copy only requirements to cache them in docker layer
WORKDIR /app
COPY poetry.lock pyproject.toml ./

# Project initialization:
RUN poetry config virtualenvs.create false \
  && poetry install --no-dev --no-interaction --no-ansi --no-root

# Copy folders, and files for a project:
COPY elastic_log_cli ./elastic_log_cli
COPY README.md ./README.md

RUN poetry config virtualenvs.create false && \
  poetry install --no-dev --no-ansi --no-interaction

# Execute command
ENTRYPOINT ["elastic-logs"]
