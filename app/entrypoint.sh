#!/bin/sh

echo "Iniciando o servidor Ollama..."
ollama serve &

sleep 5

if ! ollama list | grep -q "llama3.1"; then
    echo "Modelo llama3.1 não encontrado. Baixando..."
    ollama pull llama3.1
else
    echo "Modelo llama3.1 já está disponível."
fi

echo "Iniciando o servidor FastAPI..."
uvicorn main:app --host 0.0.0.0 --port 8080