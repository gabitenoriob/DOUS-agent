import os
import pandas as pd
import xml.etree.ElementTree as ET
from sqlalchemy import BigInteger, Float, String, create_engine, text
from bs4 import BeautifulSoup

# Configuração do SQL Server
server = 'CGUAL42872042\\SQLEXPRESS01'
database = 'dou'
driver = 'ODBC Driver 17 for SQL Server'

# Criar conexão com SQL Server
conn_str = "mssql+pyodbc://@CGUAL42872042\\SQLEXPRESS01/dou?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes"
engine = create_engine(conn_str)

def execute_query(query):
    """
    Executa uma consulta SQL e retorna os resultados.
    """
    with engine.connect() as conn:
        result = conn.execute(text(query))
        return [row for row in result]

def parse_body(xml_file):
    """
    Função para extrair campos dentro de <body> no XML.
    """
    tree = ET.parse(xml_file)
    root = tree.getroot()

    body_data = {
        "Identifica": "",
        "Data": "",
        "Ementa": "",
        "Titulo": "",
        "SubTitulo": "",
        "Texto": ""
    }

    # Procurando a tag <body>
    body_tag = root.find(".//body")
    if body_tag is not None:
        for key in body_data.keys():
            element = body_tag.find(key)
            if element is not None and element.text:
                body_data[key] = element.text.strip()

    return body_data

def clean_html(text):
    """Função para limpar HTML do texto"""
    if not text:
        return text
    soup = BeautifulSoup(text, "html.parser")
    return soup.get_text(separator=" ")

# Processamento dos arquivos XML
path_folder = "./dados/S01052024"
files = os.listdir(path_folder)

# Limpeza da tabela antes de inserir dados
with engine.connect() as conn:
    conn.execute(text("DELETE FROM dous"))
    conn.commit()

batch_size = 1000  # Defina o tamanho do lote
data_list = []
for file in files:
    if file.endswith(".xml"):
        file_path = f"{path_folder}/{file}"
        df = pd.read_xml(file_path)
        body_values = parse_body(file_path)

        for key, value in body_values.items():
            df[key] = value

        # Conversão de tipos
        df['id'] = df['id'].fillna(0).astype(int)
        df['idOficio'] = df['idOficio'].fillna(0).astype(int)
        df['artSize'] = pd.to_numeric(df['artSize'], errors='coerce').fillna(0).astype(int)
        df['numberPage'] = df['numberPage'].fillna(0).astype(int)
        df['idMateria'] = df['idMateria'].fillna(0).astype(int)

        float_cols = ["artNotes", "highlightType", "highlightPriority", "highlight", "highlightimage", "highlightimagename", "Midias"]
        for col in float_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        df['pubDate'] = df['pubDate'].astype(str)

        # Preenchendo nulos corretamente
        for col in df.columns:
            if df[col].dtype == "object":  # Strings
                df[col] = df[col].fillna("")
            else:  # Números
                df[col] = df[col].fillna(0)

        # Limpeza do HTML
        df["Texto"] = df["Texto"].apply(clean_html)
        df = df.drop_duplicates()

        data_list.append(df)

        # Inserção em lotes para evitar sobrecarga de memória
        if len(data_list) >= batch_size:
            batch_df = pd.concat(data_list, ignore_index=True)
            batch_df.to_sql(
                "dous",
                engine,
                if_exists="append",
                index=False,
                dtype={
                    "id": BigInteger(),
                    "name": String(255),
                    "idOficio": BigInteger(),
                    "pubName": String(50),
                    "artType": String(255),
                    "pubDate": String(50),
                    "artClass": String(255),
                    "artCategory": String(500),
                    "artSize": BigInteger(),
                    "artNotes": Float(),
                    "numberPage": BigInteger(),
                    "pdfPage": String(500),
                    "editionNumber": String(),
                    "highlightType": Float(),
                    "highlightPriority": Float(),
                    "highlight": Float(),
                    "highlightimage": Float(),
                    "highlightimagename": Float(),
                    "idMateria": BigInteger(),
                    "Midias": Float(),
                    "Identifica": String(2000),
                    "Data": String(255),
                    "Ementa": String(2000),
                    "Titulo": String(1000),
                    "SubTitulo": String(1000),
                    "Texto": String(),
                }
            )
            data_list = []  # Limpa a lista após o lote ser inserido

# Inserção final dos dados restantes, se houver
if data_list:
    final_df = pd.concat(data_list, ignore_index=True)
    final_df.to_sql(
        "dous",
        engine,
        if_exists="append",
        index=False,
        dtype={
            "id": BigInteger(),
            "name": String(255),
            "idOficio": BigInteger(),
            "pubName": String(50),
            "artType": String(255),
            "pubDate": String(50),
            "artClass": String(255),
            "artCategory": String(500),
            "artSize": BigInteger(),
            "artNotes": Float(),
            "numberPage": BigInteger(),
            "pdfPage": String(500),
            "editionNumber": String(),
            "highlightType": Float(),
            "highlightPriority": Float(),
            "highlight": Float(),
            "highlightimage": Float(),
            "highlightimagename": Float(),
            "idMateria": BigInteger(),
            "Midias": Float(),
            "Identifica": String(2000),
            "Data": String(255),
            "Ementa": String(2000),
            "Titulo": String(1000),
            "SubTitulo": String(1000),
            "Texto": String(),
        }
    )
