from io import BytesIO, StringIO

import pandas as pd
from flask import Flask, make_response, render_template, request, jsonify
import spacy
import re
from send import execute_query
from utils import clean_data, extract_info, build_query, extract_info_from_text, extract_portaria_info, extract_tables_from_xml, standardize_dataframe
from llm import format_response, generate_query


app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/extrair-portarias', methods=['GET'])
def extrair_portarias():
    try:
        print("Iniciando a função 'extrair-portarias'...")

        # Query para buscar as portarias relevantes
        query = """
        SELECT id, texto, pubName, pubDate, artType, artCategory, Ementa
        FROM dous
        WHERE 
            artType = 'Portaria' AND
            artCategory LIKE 'Ministério da Saúde%' AND
            (
                texto LIKE '%incremento temporário%' OR
                texto LIKE '%rateio dos recursos de transferência%' OR
                texto LIKE '%emenda parlamentares%' OR
                texto LIKE '%aplicaçã de emenda%' OR
                texto LIKE '%atenção especializada a saúde%' OR
                texto LIKE '%relatório anual de gestão RAG%' OR
                texto LIKE '%Bloco de Manutenção das Ações e Serviços Públicos de Saúde%'
            )
        """
        print(f"Query executada: {query}")

        # Executar a query
        portarias = execute_query(query)
        print(f"Portarias retornadas: {len(portarias) if portarias else 0}")

        if not portarias:
            print("Nenhuma portaria encontrada com os critérios especificados.")
            return jsonify({"message": "Nenhuma portaria encontrada com os critérios especificados"}), 404

        # Processar cada portaria
        all_data = []
        for idx, portaria in enumerate(portarias):
            try:
                texto_portaria = portaria[1]
                
                # Extrai informações com a nova função
                portaria_info = extract_portaria_info(texto_portaria)
                
                # Cria dicionário com informações consolidadas
                portaria_dict = {
                    'texto': texto_portaria,
                    'pubName': portaria[2] if not portaria_info['numero_portaria'] else portaria_info['numero_portaria'],
                    'pubDate': portaria[3] if not portaria_info['data_portaria'] else portaria_info['data_portaria'],
                    'artType': portaria[4],
                    'artCategory': portaria[5],
                    'ementa': portaria[6],
                    'numero_correto': portaria_info['numero_portaria'],
                    'data_correta': portaria_info['data_portaria']
                }
                
                # Processa tabelas
                tables = extract_tables_from_xml(texto_portaria)
                
                for table_idx, table_df in enumerate(tables):
                    try:
                        standardized_df = standardize_dataframe(table_df, portaria_dict)
                        
                        if portaria_info['numero_portaria']:
                            standardized_df['numero da portaria'] = portaria_info['numero_portaria']
                        if portaria_info['data_portaria']:
                            standardized_df['data'] = portaria_info['data_portaria']
                        
                        all_data.append(standardized_df)
                    except Exception as e:
                        print(f"Erro ao processar tabela {table_idx + 1}: {str(e)}")
                        continue
                        
            except Exception as e:
                print(f"Erro ao processar portaria {idx + 1}: {str(e)}")
                continue

        if not all_data:
            return jsonify({"message": "Nenhuma tabela válida encontrada"}), 404
        
        final_df = pd.concat(all_data, ignore_index=True)
        final_df = clean_data(final_df)
        final_df.sort_values(by=['numero da portaria', 'município'], inplace=True)
        
        return jsonify({
            "data": final_df.to_dict(orient='records'),
            "count": len(final_df),
            "status": "success"
        })
        
    except Exception as e:
        print(f"Erro no endpoint: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/ask', methods=['POST'])
def ask_question():
    user_question = request.json.get("question")
    
    if not user_question:
        return jsonify({"response": "Por favor, faça uma pergunta válida."})

    # A LLM gera a query correta
    query = generate_query(user_question)
    print(f"Query gerada pela LLM: {query}")

    if not query:
        return jsonify({"response": "Não foi possível entender a pergunta."})

    result = execute_query(query)
    print(f"Resultado da query: {result}")
    
    if not result:
        return jsonify({"response": "Nenhum resultado encontrado."})

    # Remove duplicatas
    result = list(set(result))

    # Formata a resposta com a LLM
    formatted_response = format_response(user_question, result)

    return jsonify({"response": formatted_response})
@app.route('/exportar-portarias-csv', methods=['GET'])
def exportar_csv():
    data = extrair_portarias().get_json()
    if 'error' in data:
        return jsonify(data), 500
    
    df = pd.DataFrame(data['data'])
    output = StringIO()
    df.to_csv(output, index=False, encoding='utf-8-sig', sep=';')
    output.seek(0)
    
    response = make_response(output.getvalue())
    response.headers['Content-Disposition'] = 'attachment; filename=portarias.csv'
    response.headers['Content-type'] = 'text/csv; charset=utf-8-sig'
    return response

@app.route('/exportar-portarias-excel', methods=['GET'])
def exportar_excel():
    data = extrair_portarias().get_json()
    if 'error' in data:
        return jsonify(data), 500
    
    df = pd.DataFrame(data['data'])
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Portarias')
    
    output.seek(0)
    
    response = make_response(output.getvalue())
    response.headers['Content-Disposition'] = 'attachment; filename=portarias.xlsx'
    response.headers['Content-type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    return response
if __name__ == '__main__':
    app.run(debug=True)
