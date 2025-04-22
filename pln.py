from bs4 import BeautifulSoup
import pandas as pd
import re
from io import StringIO

# 1. Extrai texto limpo do XML
def extrair_texto_xml(xml_str):
    soup = BeautifulSoup(xml_str, 'xml')
    return soup.get_text(separator='\n').strip()

# 2. Converte texto em DataFrame bruto (heurística simples)
def texto_para_dataframe_bruto(texto):
    linhas = texto.split("\n")
    linhas = [linha.strip() for linha in linhas if linha.strip()]
    linhas_limpas = [re.split(r'\s{2,}|;|\t', linha) for linha in linhas]
    return pd.DataFrame(linhas_limpas)

# 3. Prompt para padronizar a tabela com LLM
from langchain_core.prompts import PromptTemplate

prompt_padroniza_tabela = PromptTemplate.from_template("""
Você é um especialista em transformar dados bagunçados em tabelas coerentes.
Abaixo está uma tabela extraída de um texto desorganizado (como de um XML do Diário Oficial).
Corrija os dados, organize colunas e responda com uma tabela usando ponto e vírgula (;) como separador.
Inclua a linha de cabeçalho correta.

TEXTO DA TABELA:
{tabela_bruta}
""")

# 4. Função principal de correção via LLM
def corrigir_tabela_de_texto(texto_xml, llm):
    texto_limpo = extrair_texto_xml(texto_xml)
    texto_limpo = re.sub(r'\n{2,}', '\n', texto_limpo)
    df_bruto = texto_para_dataframe_bruto(texto_limpo)
    tabela_txt = df_bruto.to_csv(index=False, sep=";")

    prompt = prompt_padroniza_tabela.format(tabela_bruta=tabela_txt)
    try:
        tabela_corrigida = llm.invoke(prompt)  
        return pd.read_csv(StringIO(tabela_corrigida), sep=";")
    except Exception as e:
        print(f"Erro ao converter a tabela da LLM: {e}")
        return pd.DataFrame()  