# Agente 190 - Serviço de Atendimento via WhatsApp

Este projeto implementa um serviço de atendimento automatizado para o número 190 (polícia) via WhatsApp, utilizando inteligência artificial para processar e responder mensagens de texto, áudio, imagens e localizações.

## Integrações de WhatsApp

O sistema suporta duas integrações diferentes para o WhatsApp:

### 1. Twilio (Original)

A integração original utilizando a API da Twilio está disponível em:
```
/api/v1/agent_twilio_190/predict_twilio_190
```

### 2. ZAPI (Nova implementação)

Uma nova implementação utilizando a API do ZAPI está disponível em:
```
/api/v1/agent_zapi_190/webhook_zapi
```

### Comparação das Integrações

| Recurso | Twilio | ZAPI |
|---------|--------|------|
| Mensagens de Texto |  |  |
| Áudio |  |  |
| Imagem |  |  |
| Localização |  |  |
| Customização | Limitada | Avançada |
| Webhook | Precisa de URL pública | Precisa de URL pública |

## Configuração

### Variáveis de Ambiente

Para usar o ZAPI, configure as seguintes variáveis de ambiente:

```env
# Variáveis para ZAPI
ZAPI_API_KEY=sua_chave_api
ZAPI_INSTANCE_ID=seu_id_de_instancia
ZAPI_BASE_URL=https://api.z-api.io/instances

# Variáveis para os modelos de IA
OPENAI_API_KEY=sua_chave_api_openai
ANTHROPIC_API_KEY=sua_chave_api_anthropic
```

### Configuração do Webhook ZAPI

1. Acesse o painel do ZAPI
2. Configure um webhook para apontar para sua URL: `https://seu-dominio.com/api/v1/agent_zapi_190/webhook_zapi`
3. Certifique-se de que os eventos de mensagens estão habilitados

## Funcionalidades

- **Processamento de texto**: Responde a mensagens de texto usando modelos de LLM (Claude, GPT, etc.)
- **Processamento de áudio**: Transcreve áudios para texto usando reconhecimento de fala
- **Processamento de imagens**: Interpreta o conteúdo de imagens usando Gemini Vision
- **Processamento de localização**: Converte coordenadas em endereços usando geocodificação reversa

## Executando o Projeto

```bash
# Instalar dependências
pip install -r requirements.txt

# Executar o servidor
uvicorn app.main:app --reload
```