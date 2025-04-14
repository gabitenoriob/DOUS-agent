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
            "max_tokens": 131072,
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
llm_local = LocalLLM(model_name="gemma-3-12b-it")

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

import pandas as pd
import os
import requests

def extract_table_using_llm(texto_portaria):
    """
    Usa o LLM (Gemma-3-27b-it) para extrair e estruturar tabelas do texto da portaria.
    Retorna uma lista de DataFrames com as tabelas extraídas.
    """
    prompt = f"""
    Extraia e estruture a tabela contida no seguinte texto XML da portaria:
            
    {texto_portaria}

    Responda apenas com a tabela formatada corretamente em CSV. 
    Use ";" como separador.
    """

    headers = {"Content-Type": "application/json"}
    payload = {
        "model": "gemma-3-12b-it",
        "prompt": prompt,
        "max_tokens":131072,
        "temperature": 0.0,
        "top_p": 0.7
    }

    try:
        response = requests.post("http://10.2.3.63:1234/v1/completions", headers=headers, json=payload)
        response.raise_for_status()
        csv_output = response.json().get('choices', [{}])[0].get('text', '').strip()
        
        # Converter CSV em DataFrame
        from io import StringIO
        df = pd.read_csv(StringIO(csv_output), delimiter=";")
        return df
    except requests.RequestException as e:
        print(f"Erro ao conectar ao LLM para extração de tabela: {e}")
        return None

def process_portarias_with_llm(portarias):
    """
    Percorre as portarias e extrai tabelas via LLM.
    Salva as tabelas extraídas em CSV/XLS unificado.
    """
    all_data = []
    csv_filename = 'tabelas_unificadas.csv'
    excel_filename = 'tabelas_unificadas.xlsx'

    for idx, portaria in enumerate(portarias):
        try:
            texto_portaria = portaria[1]
            tables_df = extract_table_using_llm(texto_portaria)

            if tables_df is not None:
                # Adiciona metadados da portaria no DF
                tables_df['numero da portaria'] = portaria[0]  # ID da portaria
                tables_df['data'] = portaria[3]  # Data da portaria

                # Salvar no CSV e Excel sem sobrescrever
                tables_df.to_csv(csv_filename, mode='a', index=False, encoding='utf-8-sig', sep=';', header=not os.path.exists(csv_filename))
                with pd.ExcelWriter(excel_filename, mode='a', engine='openpyxl', if_sheet_exists='overlay') as writer:
                    tables_df.to_excel(writer, sheet_name='Portarias', index=False, header=not os.path.exists(excel_filename))

                all_data.append(tables_df)
                print(f"Tabela extraída e adicionada: {tables_df.shape[0]} linhas")
            else:
                print(f"Nenhuma tabela válida extraída da portaria {idx + 1}")

        except Exception as e:
            print(f"Erro ao processar portaria {idx + 1}: {str(e)}")
            continue

    # Unir todas as tabelas se houver dados
    if all_data:
        final_df = pd.concat(all_data, ignore_index=True)
        final_df.to_csv(csv_filename, index=False, encoding='utf-8-sig', sep=';')
        final_df.to_excel(excel_filename, index=False)
        print("Tabela unificada salva com sucesso.")
    else:
        print("Nenhuma tabela válida encontrada para unificação.")



    
  
