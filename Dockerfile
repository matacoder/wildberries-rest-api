FROM python:3.9-slim

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE 1
# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED 1

ENV POETRY_HOME=/opt/poetry

ENV PATH="$POETRY_HOME/bin:$PATH"

# Install essential tools
RUN apt-get -y update && apt-get install -y \
    wget \
    gnupg \
    lsb-release

# Install and setup poetry
RUN pip install -U pip \
    && apt install -y curl netcat \
    && curl -sSL https://install.python-poetry.org | python3 -


WORKDIR /code
COPY . /code


# Run poetry
RUN poetry config virtualenvs.create false \
  && poetry install --no-interaction --no-ansi


ENTRYPOINT ["/code/entrypoint.sh"]