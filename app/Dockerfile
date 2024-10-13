FROM python:3.11.0

RUN apt-get update
    
RUN pip install --upgrade pip

COPY requirements.txt requirements.txt

RUN pip install keyring==23.8.2 \
    && pip install keyrings.google-artifactregistry-auth==1.0.0 \
    && pip install --trusted-host pypi.python.org -r requirements.txt 

COPY . /app

WORKDIR /app

ENV SERVICE=api-bot-ssp
ENV PROJECT=annular-weaver-428312-s3

ENV HOST=0.0.0.0
ENV WORKERS=4

EXPOSE 8080

ENTRYPOINT ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
