from dataclasses import Field
from dotenv import load_dotenv
from langchain.schema.runnable import RunnablePassthrough
from langchain.llms import BaseLLM
import requests
from langchain.schema import LLMResult
import json
from langchain.prompts import PromptTemplate
from huggingface_hub import login
import os


LM_STUDIO_URL = "http://10.2.3.63:1234/v1/completions"

class LocalLLM(BaseLLM):
    model_name: str

    def __init__(self, model_name: str, **kwargs):
        super().__init__(model_name=model_name, **kwargs)  
        self.model_name = model_name

    def _call(self, prompt: str, stop=None) -> str:
        headers = {"Content-Type": "application/json"}
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "max_tokens": 100,
            "temperature": 0.0,
            "top_p": 0.7 #regula quais palavras são consideradas para geração, escolhendo as mais prováveis onde a soma das probabilidades seja ate no max 0.7 por exemplo
        }
        try:
            response = requests.post(LM_STUDIO_URL, headers=headers, json=payload)
            response.raise_for_status()
            text_output = response.json().get('choices', [{}])[0].get('text', '').strip()

            if "```sql" in text_output:
                text_output = text_output.split("```sql")[-1].split("```")[0].strip()

            return text_output
        except requests.RequestException as e:
            raise Exception(f"Erro ao conectar à API do LM Studio: {e}")

    def _generate(self, prompts, stop=None):
        results = []
        for prompt in prompts:
            text = self._call(prompt)
            results.append({"text": text})
        return LLMResult(generations=[[result] for result in results])

    @property
    def _llm_type(self):
        return "local_llm"

llm_local = LocalLLM(model_name="qwq-32b")
llm_local = LocalLLM(model_name="gemma-3-27b-it")

prompt_generate_query = PromptTemplate(
    input_variables=["question"],
    template = (
    "Você é um assistente especialista em SQL. Gere **somente** a query SQL para a tabela 'dous' no banco de dados ativo, não inclua explicação adicional.\n"
    "Você deve responder à pergunta do usuário"
    "com base na seguinte pergunta:\n{question}\n"
    "Os campos disponíveis são: "
    "id, name, idOficio, pubName, artType, pubDate, artClass, artCategory, artSize, artNotes, "
    "numberPage, pdfPage, editionNumber, highlightType, highlightPriority, highlight, "
    "highlightimage, highlightimagename, idMateria, body, Midias, texto, Identifica, Ementa, Titulo,SubTitulo.\n"
    "Responda **exclusivamente** com a query SQL. NÃO inclua explicações, comentários ou formatação extra."
)

)
query_chain = RunnablePassthrough() | prompt_generate_query | llm_local

def generate_query(question):
    return query_chain.invoke({"question": question})  

prompt_format_response = PromptTemplate(
    input_variables=["question", "raw_response"],
    template=(
        "O usuário perguntou: {question}\n"
        "O banco de dados respondeu com: {raw_response}\n"
        "Formule uma resposta clara e objetiva para o usuário com base nesses dados."
    )
)
response_chain = RunnablePassthrough() | prompt_format_response | llm_local

def format_response(question, raw_response):
    response = response_chain.invoke({"question": question, "raw_response": raw_response})

import subprocess
import json

def process_table_with_llm(table_text):
    prompt = f"""
    Tenho uma tabela extraída de um documento, mas os valores estão desalinhados.

    1️⃣ Reestruture os dados para que fiquem corretamente organizados com base nos headers.
    2️⃣ Preencha valores ausentes com "NULL".

    📌 Aqui está a tabela extraída:
    {table_text}

    Retorne a saída em JSON estruturado.
    """

    response = llm_local.invoke(prompt)

    try:
        structured_data = json.loads(response)
        return structured_data
    except json.JSONDecodeError:
        print("Erro ao decodificar JSON. Saída do modelo:", response)
        return None

    
  
