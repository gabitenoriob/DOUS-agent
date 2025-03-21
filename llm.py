from dataclasses import Field
from dotenv import load_dotenv
# from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
# from langchain.llms import HuggingFacePipeline
from langchain.llms import BaseLLM
import requests
import json
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
# import pydantic
# import torch
from huggingface_hub import login
import os
# load_dotenv()

# login(token=os.getenv('HUGGINGFACE_TOKEN'))
# model_name = "meta-llama/Llama-3.2-1B"
# tokenizer = AutoTokenizer.from_pretrained(model_name)
# model = AutoModelForCausalLM.from_pretrained(model_name)

# generator = pipeline(
#     "text-generation",
#     model=model,
#     tokenizer=tokenizer,
#     max_new_tokens=1000,  
#     temperature=0.0,  
#     top_p=0.9
# )
# llm = HuggingFacePipeline(pipeline=generator)


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
            "max_tokens": 1000,
            "temperature": 0.0,
            "top_p": 0.9
        }
        response = requests.post(LM_STUDIO_URL, headers=headers, data=json.dumps(payload))
        if response.status_code == 200:
            return response.json()['choices'][0]['text'].strip()
        else:
            raise Exception(f"Erro na API do LM Studio: {response.status_code} - {response.text}")

    def _generate(self, prompts, stop=None):
        return [{"text": self._call(prompt)} for prompt in prompts]

    @property
    def _llm_type(self):
        return "local_llm"

llm_local = LocalLLM(model_name="meta-llama-3.1-8b-instruct")


# **Prompt para gerar a query SQL corretamente**
prompt_generate_query = PromptTemplate(
    input_variables=["question"],
    template=(
        "Você é um assistente especialista em SQL. Gere uma query para um banco chamado 'dous' "
        "com base na seguinte pergunta:\n{question}\n"
        "Considere que os campos do banco incluem: "
        "id, name, idOficio, pubName, artType, pubDate, artClass, artCategory, artSize, artNotes, "
        "numberPage, pdfPage, editionNumber, highlightType, highlightPriority, highlight, "
        "highlightimage, highlightimagename, idMateria, body, Midias ,texto, Identifica, Ementa,TituloSubTitulo.\n"
        "Se a pergunta envolver 'resumo' ou 'texto', retorne o campo 'texto'.\n"
        "Não adicione colunas desnecessárias. Responda apenas com a query SQL, sem explicações adicionais."
    )
)
query_chain = LLMChain(llm=llm_local, prompt=prompt_generate_query) #ALTERAR P LLM LOCAL SE FOR USAR LOCAL OU LLM SE FOR USAR HUGGINGFACE

def generate_query(question):
    return query_chain.run(question)

# **Prompt para reformular a resposta**
prompt_format_response = PromptTemplate(
    input_variables=["question", "raw_response"],
    template=(
        "O usuário perguntou: {question}\n"
        "O banco de dados respondeu com: {raw_response}\n"
        "Formule uma resposta clara e objetiva para o usuário com base nesses dados."
    )
)
response_chain = LLMChain(llm=llm_local, prompt=prompt_format_response) # ALTERAR P LLM LOCAL SE FOR USAR LOCAL OU LLM SE FOR USAR HUGGINGFACE

def format_response(question, raw_response):
    return response_chain.run(question=question, raw_response=raw_response)
