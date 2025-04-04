import re

import pandas as pd
from bs4 import BeautifulSoup
import spacy

nlp = spacy.load("pt_core_news_sm")

FIELD_MAPPING = {
    "idOficio": ["ofício", "oficio", "idOficio", "número do ofício", "numero do oficio"],
    "pubDate": ["data", "publicado", "data de publicação", "pubDate", "data de publicacao", "data de publicado"],
    "artCategory": ["categoria", "artCategory", "categoria do ofício", "categoria do oficio"],
    "artType": ["tipo", "tipo do ofício", "tipo do oficio", "artType"],
    "name": ["nome", "name"],
    "pubName": ["nome da publicação", "pubName"],
    "artClass": ["classe", "artClass"],
    "artSize": ["tamanho", "artSize"],
    "artNotes": ["notas", "artNotes"],
    "numberPage": ["página", "numberPage"],
    "pdfPage": ["pdf", "link", "pdfPage"],
    "editionNumber": ["edição", "editionNumber"],
    "highlightType": ["tipo de destaque", "highlightType"],
    "highlightPriority": ["prioridade do destaque", "highlightPriority"],
    "highlight": ["destaque", "highlight"],
    "highlightimage": ["imagem do destaque", "highlightimage"],
    "highlightimagename": ["nome da imagem do destaque", "highlightimagename"],
    "idMateria": ["id da matéria", "idMateria"],
    "body": ["corpo", "body"],
    "Midias": ["mídias", "Midias"],
    "texto": ["texto", "Texto", "conteúdo", "conteudo", "o que trata", "o que fala"],
    "Identifica": ["identifica", "Identifica", "identificação", "Identificação"],
    "Ementa": ["ementa", "Ementa", "resumo", "Ementa"],
    "Titulo": ["titulo", "Titulo"],
    "SubTitulo": ["subtitulo", "SubTitulo"]
}
import re
from datetime import datetime

def extract_portaria_info(texto):
    """
    Extrai número e data da portaria usando regex avançado e tratamento de variações
    """
    # Padrão regex flexível para capturar todas as variações
    portaria_pattern = r"""
        (PORTARIA)                # Palavra 'PORTARIA'
        \s+                       # Espaços
        (?:GM/MS\s+)?             # Opcional: 'GM/MS' 
        (?:N[º°]|NUMERO?|N\.?)\s*  # Variantes de número (Nº, N°, NUMERO, N)
        \s*                       # Espaços opcionais
        ([\d.,]+)                 # Número (permite pontos e vírgulas)
        \s*                       # Espaços opcionais
        (?:,?\s*DE\s+)?           # Opcional: ' DE ' ou ', DE '
        (\d{1,2}\s+DE\s+          # Dia + ' DE '
        (?:JANEIRO|FEVEREIRO|MAR[ÇC]O|ABRIL|MAIO|JUNHO|  # Mês
           JULHO|AGOSTO|SETEMBRO|OUTUBRO|NOVEMBRO|DEZEMBRO)
        \s+DE\s+\d{4})            # ' DE ' + ano
    """
    
    info = {'numero_portaria': None, 'data_portaria': None}
    
    # Busca no texto completo primeiro
    match = re.search(portaria_pattern, texto, re.IGNORECASE | re.VERBOSE)
    
    # Se não encontrou, tenta em tags específicas
    if not match:
        soup = BeautifulSoup(texto, 'html.parser')
        for tag in ['p.identifica', 'div.identificacao', 'span.numero-portaria']:
            element = soup.select_one(tag)
            if element:
                match = re.search(portaria_pattern, element.get_text(), 
                                re.IGNORECASE | re.VERBOSE)
                if match:
                    break
    
    if match:
        # Tratamento do número
        numero = match.group(3).replace('.', '').replace(',', '.')
        info['numero_portaria'] = numero
        
        # Tratamento da data
        meses = {
            'JANEIRO': '01', 'FEVEREIRO': '02', 'MARÇO': '03', 'MARCO': '03',
            'ABRIL': '04', 'MAIO': '05', 'JUNHO': '06',
            'JULHO': '07', 'AGOSTO': '08', 'SETEMBRO': '09',
            'OUTUBRO': '10', 'NOVEMBRO': '11', 'DEZEMBRO': '12'
        }
        
        data_texto = match.group(4)
        try:
            dia, _, mes, _, ano = data_texto.split()
            mes_num = meses[mes.upper()]
            info['data_portaria'] = f"{int(dia):02d}/{mes_num}/{ano}"
        except:
            pass
    
    return info
def extract_tables_from_xml(xml_text):
    """Extrai tabelas de texto HTML e retorna como DataFrames"""
    soup = BeautifulSoup(xml_text, 'html.parser')
    tables = soup.find_all('table')
    
    results = []
    for table in tables:
        # Extrair linhas da tabela
        rows = table.find_all('tr')
        if len(rows) < 2:  # Pelo menos cabeçalho + 1 linha de dados
            continue
            
        # Extrair cabeçalhos - considerar th ou a primeira linha de td
        header_cells = rows[0].find_all(['th', 'td'])
        if not header_cells:
            header_cells = rows[1].find_all(['th', 'td'])
            
        headers = [cell.get_text(strip=True) for cell in header_cells]
        
        # Determinar linha inicial de dados (pular cabeçalhos)
        data_start = 1 if rows[0].find('th') else 0
        
        # Extrair dados
        data = []
        for row in rows[data_start:]:
            cells = row.find_all(['td', 'th'])
            row_data = [cell.get_text(strip=True) for cell in cells]
            if row_data and len(row_data) == len(headers):
                data.append(row_data)
        
        if headers and data:
            try:
                df = pd.DataFrame(data, columns=headers)
                results.append(df)
            except Exception as e:
                print(f"Erro ao criar DataFrame: {e}")
                continue
                
    return results
def extract_info_from_text(texto):
    """
    Extrai informações relevantes do texto HTML da portaria
    """
    info = {
        'numero_portaria': None,
        'data_portaria': None,
        'outros_dados': {}
    }
    
    # Usar BeautifulSoup para parsear o HTML
    soup = BeautifulSoup(texto, 'html.parser')
    
    identifica = soup.find('p', class_='identifica')
    if identifica:
        identifica_text = identifica.get_text()
        portaria_pattern = r'PORTARIA\s+(?:GM/MS\s+)?N[º°]\s*([\d.,]+),\s*DE\s*(\d{1,2}\s+DE\s+[A-Z]+\s+DE\s+\d{4})'
        match = re.search(portaria_pattern, identifica_text, re.IGNORECASE)
        if match:
            info['numero_portaria'] = match.group(1).replace('.', '').replace(',', '.')
            data_text = match.group(2)  
            
            try:
                meses = {
                    'JANEIRO': '01', 'FEVEREIRO': '02', 'MARÇO': '03', 'MARCO': '03',
                    'ABRIL': '04', 'MAIO': '05', 'JUNHO': '06',
                    'JULHO': '07', 'AGOSTO': '08', 'SETEMBRO': '09',
                    'OUTUBRO': '10', 'NOVEMBRO': '11', 'DEZEMBRO': '12'
                }
                dia, _, mes, _, ano = data_text.split()
                mes_num = meses[mes.upper()]
                info['data_portaria'] = f"{dia.zfill(2)}/{mes_num}/{ano}"
            except:
                pass
    
    return info

def parse_brazilian_date(date_str):
    """Converte datas no formato brasileiro para datetime"""
    try:
        return datetime.strptime(date_str, '%d/%m/%Y')
    except:
        try:
            # Tenta converter do texto por extenso
            meses = {'janeiro':1, 'fevereiro':2, 'março':3, 'abril':4,
                    'maio':5, 'junho':6, 'julho':7, 'agosto':8,
                    'setembro':9, 'outubro':10, 'novembro':11, 'dezembro':12}
            
            parts = date_str.lower().split(' de ')
            if len(parts) == 3:
                dia = int(parts[0])
                mes = meses.get(parts[1], 1)
                ano = int(parts[2])
                return datetime(ano, mes, dia)
        except:
            return None
    return None
def standardize_dataframe(df, portaria_info):
    """Padroniza o DataFrame para o formato desejado"""
    # Mapeamento de colunas com regex para capturar variações
    column_mapping = {
        r'UF|ESTADO': 'UF',
        r'MUNIC[IÍ]PIO': 'município',
        r'COD(IGO)?\s*IBGE|IBGE': 'código IBGE do município',
        r'ENTIDADE|FUNDO|RAZÃO SOCIAL': 'nome do fundo',
        r'CNPJ': 'CNPJ',
        r'ESTABELECIMENTO|NOME FANTASIA': 'nome do estabelecimento',
        r'CNES': 'código CNES',
        r'CNPJ\s*DO\s*ESTABELECIMENTO': 'CNPJ do estabelecimento',
        r'C[ÓO]D(\.|IGO)?\s*EMENDA': 'código da emenda parlamentar',
        r'VALOR\s*POR\s*EMENDA\s*\(R\$\)': 'valor por emenda',
        r'VALOR\s*POR\s*PARLAMENTAR\s*\(R\$\)': 'valor por parlamentar',
        r'VALOR\s*(TOTAL)?\s*(DA\s*PROPOSTA)?\s*\(?R\$\)?': 'valor',
        r'FUNCIONAL\s*PROGRAM[ÁA]TICA': 'funcional programático',
        r'N[º°]\s*DA\s*PROPOSTA|PROPOSTA\s*SAIPS': 'numero da proposta',
        r'N[ÚU]MERO\s*DA\s*PORTARIA': 'numero da portaria',
        r'DATA': 'data'
    }
    
    # Renomear colunas com base em regex
    for pattern, new_name in column_mapping.items():
        for col in df.columns:
            if re.search(pattern, col, re.IGNORECASE):
                df.rename(columns={col: new_name}, inplace=True)
    
    # Garantir colunas esperadas
    expected_columns = [
        'UF', 'município', 'código IBGE do município', 'nome do fundo', 'CNPJ',
        'nome do estabelecimento', 'código CNES', 'CNPJ do estabelecimento',
        'código da emenda parlamentar', 'valor por emenda', 'valor por parlamentar', 
        'valor', 'funcional programático', 'numero da proposta',
        'numero da portaria', 'data'
    ]
    
    for col in expected_columns:
        if col not in df.columns:
            df[col] = None
    
    # Preenchimento inteligente dos metadados
    df['numero da portaria'] = (portaria_info.get('numero_correto') or 
                              df.get('numero da portaria') or 
                              portaria_info.get('pubName'))
    
    df['data'] = (portaria_info.get('data_correta') or 
                 df.get('data') or 
                 portaria_info.get('pubDate'))
    
    # Conversão de datas para formato padrão
    if 'data' in df.columns:
        df['data'] = df['data'].apply(lambda x: parse_brazilian_date(x).strftime('%d/%m/%Y') 
                                  if parse_brazilian_date(x) else x)
    
    return df[expected_columns]

def clean_data(df):
    """Limpa e padroniza os dados"""
    # Limpeza de valores monetários
    money_cols = ['valor', 'valor por emenda', 'valor por parlamentar']
    for col in money_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(r'[R$\s.]', '', regex=True)
            df[col] = df[col].str.replace(',', '.').str.strip()
            df[col] = pd.to_numeric(df[col], errors='coerce')
    return df

def extract_info(user_input):
    """
    Extrai informações da pergunta do usuário e as separa entre SELECT e WHERE.
    """
    extracted_data = {"select": [], "where": {}}
    
    print(f"Pergunta recebida: {user_input}")
    doc = nlp(user_input.lower())
    
    # Extrai o idOficio (se presente)
    match_id_oficio = re.search(r"(?:ofício|oficio)\s*(?:número\s*)?(\d+)", user_input, re.IGNORECASE)
    if match_id_oficio:
        extracted_data["where"]["idOficio"] = match_id_oficio.group(1)
        print(f"Número de ofício extraído: {extracted_data['where']['idOficio']}")
    
    # Extrai o nome (se presente)
    match_name = re.search(r"(?:nome\s*do\s*ofício|nome)\s*(?:de)?\s*([\w\-\_\s]+)", user_input, re.IGNORECASE)
    if match_name:
        extracted_data["where"]["name"] = match_name.group(1).strip()
        print(f"Nome extraído: {extracted_data['where']['name']}")
    
    # Identifica colunas para SELECT
    for word in doc:
        for field, keywords in FIELD_MAPPING.items():
            if word.text in keywords and field not in extracted_data["select"]:
                extracted_data["select"].append(field)
                print(f"Palavra-chave identificada: {word.text} -> Campo mapeado: {field}")
    
    return extracted_data

def build_query(extracted_data):
    """
    Gera a melhor query SQL baseada nos campos extraídos.
    """
    if not extracted_data["select"]:
        extracted_data["select"].append("*")  
    
    columns_str = ", ".join(extracted_data["select"])
    query = f"SELECT {columns_str} FROM dous"
    
    where_clauses = []
    for field, value in extracted_data["where"].items():
        if isinstance(value, str) and not value.isnumeric():
            where_clauses.append(f"{field} = '{value}'")
        else:
            where_clauses.append(f"{field} = {value}")
    
    if where_clauses:
        query += " WHERE " + " AND ".join(where_clauses)
    
    print(f"Query gerada: {query}")
    return query