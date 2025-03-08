# Agente 190 - Servi�o de Atendimento via WhatsApp

Este projeto implementa um servi�o de atendimento automatizado para o n�mero 190 (pol�cia) via WhatsApp, utilizando intelig�ncia artificial para processar e responder mensagens de texto, �udio, imagens e localiza��es.

## Integra��es de WhatsApp

O sistema suporta duas integra��es diferentes para o WhatsApp:

### 1. Twilio (Original)

A integra��o original utilizando a API da Twilio est� dispon�vel em:
```
/api/v1/agent_twilio_190/predict_twilio_190
```

### 2. ZAPI (Nova implementa��o)

Uma nova implementa��o utilizando a API do ZAPI est� dispon�vel em:
```
/api/v1/agent_zapi_190/webhook_zapi
```

### Compara��o das Integra��es

| Recurso | Twilio | ZAPI |
|---------|--------|------|
| Mensagens de Texto |  |  |
| �udio |  |  |
| Imagem |  |  |
| Localiza��o |  |  |
| Customiza��o | Limitada | Avan�ada |
| Webhook | Precisa de URL p�blica | Precisa de URL p�blica |

## Configura��o

### Vari�veis de Ambiente

Para usar o ZAPI, configure as seguintes vari�veis de ambiente:

```env
# Vari�veis para ZAPI
ZAPI_API_KEY=sua_chave_api
ZAPI_INSTANCE_ID=seu_id_de_instancia
ZAPI_BASE_URL=https://api.z-api.io/instances

# Vari�veis para os modelos de IA
OPENAI_API_KEY=sua_chave_api_openai
ANTHROPIC_API_KEY=sua_chave_api_anthropic
```

### Configura��o do Webhook ZAPI

1. Acesse o painel do ZAPI
2. Configure um webhook para apontar para sua URL: `https://seu-dominio.com/api/v1/agent_zapi_190/webhook_zapi`
3. Certifique-se de que os eventos de mensagens est�o habilitados

## Funcionalidades

- **Processamento de texto**: Responde a mensagens de texto usando modelos de LLM (Claude, GPT, etc.)
- **Processamento de �udio**: Transcreve �udios para texto usando reconhecimento de fala
- **Processamento de imagens**: Interpreta o conte�do de imagens usando Gemini Vision
- **Processamento de localiza��o**: Converte coordenadas em endere�os usando geocodifica��o reversa

## Executando o Projeto

```bash
# Instalar depend�ncias
pip install -r requirements.txt

# Executar o servidor
uvicorn app.main:app --reload
```