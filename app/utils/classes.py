from langchain_core.pydantic_v1 import BaseModel, Field
from datetime import date


class Documento(BaseModel):
    tipo: str = Field(description='Tipo do documento (por exemplo, RG, CPF, CNH)')
    instituicao: str = Field(description='Instituição onde o documento foi emitido')
    titular: str = Field(description='Nome completo do titular do documento')
    numero: str = Field(description='Numeração do documento (opcional, pode ter sido esquecido)')


class ItemRoubadoFurtado(BaseModel):
    tipo: str = Field(description='Tipo do item (por exemplo, celular, carteira, etc.)')
    descricao: str = Field(description='Descrição detalhada do item')
    imei: str = Field(description='IMEI do celular (se aplicável, pode ter sido esquecido)')
    documento_relacionado: Documento = Field(description='Informações do documento relacionado, se houver')


class PerdaExtravio(BaseModel):
    documento: Documento = Field(description='Documento perdido/extraviado')


class Roubo(BaseModel):
    objeto: ItemRoubadoFurtado = Field(description='Item roubado, individualmente descrito')
    suspeito: str = Field(description='Nome do suspeito de ter realizado o roubo')
    descricao_suspeito: str = Field(description='Descrição do suspeito (opcional)')


class Furto(BaseModel):
    objeto: ItemRoubadoFurtado = Field(description='Item furtado, individualmente descrito')


class Natureza(BaseModel):
    perda_extravio: PerdaExtravio = Field(description='Perda ou extravio de documentos')
    roubo: Roubo = Field(description='Roubo de objetos')
    furto: Furto = Field(description='Furto de objetos')


class Pessoa(BaseModel):
    status_extensao: bool = False
    nome_completo: str = Field(description='Nome completo do cidadão')
    nome_mae: str = Field(description='Nome completo da mãe do cidadão')
    naturalidade: str = Field(description='Naturalidade do cidadão')
    nacionalidade: str = Field(description='Nacionalidade do cidadão')
    data_nascimento: date = Field(description='Data de nascimento do cidadão')
    envolvido: bool = Field(description='O cidadão é o envolvido na ocorrência?')

    descricao_fato: str = Field(description='Descrição do fato(relato do cidadão)')
    data: date = Field(description='Data do ocorrido')
    local: str = Field(description='Local do ocorrido')

    cpf: str = Field(description='CPF do cidadão')
    cep_cidadao: str = Field(description='CEP do cidadão')

    telefone_contato: str = Field(description='Telefone de contato para atualizações.')
    email_contato: str = Field(description='E-mail de contato para atualizações.')

    natureza: Natureza = Field(description='Natureza do ocorrido')
    mensagem: str = Field(description='Última mensagem enviada pelo cidadão')
