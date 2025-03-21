import re
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