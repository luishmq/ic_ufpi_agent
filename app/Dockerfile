FROM python:3.11.0

RUN apt-get update && apt-get install -y \
    curl \
    && curl -fsSL https://ollama.ai/install.sh | bash

RUN pip install --upgrade pip
COPY requirements.txt requirements.txt
RUN pip install --trusted-host pypi.python.org -r requirements.txt

COPY . /app
WORKDIR /app

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENV SERVICE=api-bot-ic
ENV PROJECT=annular-weaver-428312-s3
ENV HOST=0.0.0.0
ENV WORKERS=4

EXPOSE 8080
EXPOSE 11434

CMD ["/entrypoint.sh"]