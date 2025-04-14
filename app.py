from io import BytesIO, StringIO
import os

import pandas as pd
from flask import Flask, make_response, render_template, request, jsonify
import spacy
import re
from send import execute_query
from utils import clean_data, extract_info, build_query, extract_info_from_text, extract_portaria_info, extract_portaria_info_nlp, extract_tables_from_xml, standardize_dataframe
from llm import format_response, generate_query, process_portarias_with_llm


app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/extrair-portarias', methods=['GET'])
def extrair_portarias():
    try:
        print("Iniciando a função 'extrair-portarias'...")

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

        portarias = execute_query(query)
        #criar um txt com tudo que foi retornado da query
        with open('portarias.txt', 'w', encoding='utf-8') as f:
            for portaria in portarias:
                f.write(f"{portaria}\n")
        print("Portarias extraídas com sucesso.")
        print(f"Portarias retornadas: {len(portarias) if portarias else 0}")

        # if portarias:
        #        process_portarias_with_llm(portarias) 

        if not portarias:
            print("Nenhuma portaria encontrada com os critérios especificados.")
            return jsonify({"message": "Nenhuma portaria encontrada com os critérios especificados"}), 404

        all_data = []
        csv_filename = 'dfs.csv'
        excel_filename = 'dfs.xlsx'

        for idx, portaria in enumerate(portarias):
            try:
                texto_portaria = portaria[1]
                portaria_info = extract_portaria_info(texto_portaria)
                portaria_info_nlp = extract_portaria_info_nlp(texto_portaria)

                print(f"Portaria {idx+1}: Nº {portaria_info['numero_portaria']} - Data: {portaria_info['data_portaria']}")
                print(F"Portaria info nlp: {portaria_info_nlp}")
                

                tables = extract_tables_from_xml(texto_portaria)
                print(f"Número de tabelas encontradas: {len(tables)}")

                for table_df in tables:
                    try:
                        standardized_df = standardize_dataframe(table_df, portaria_info)

                        if portaria_info['numero_portaria']:
                            standardized_df['numero da portaria'] = portaria_info['numero_portaria']
                        if portaria_info['data_portaria']:
                            standardized_df['data'] = portaria_info['data_portaria']

                        # Salvar cada iteração no CSV sem sobrescrever (append)
                        standardized_df.to_csv(csv_filename, mode='a', index=False, encoding='utf-8-sig', sep=';', header=not os.path.exists(csv_filename))
                        standardized_df.to_excel(excel_filename, header=not os.path.exists(excel_filename))  

                        all_data.append(standardized_df)
                        #print(f"Tabela processada e adicionada: {standardized_df.head()}")

                    except Exception as e:
                        print(f"Erro ao processar tabela da portaria {idx + 1}: {str(e)}")
                        continue

            except Exception as e:
                print(f"Erro ao processar portaria {idx + 1}: {str(e)}")
                continue

        if not all_data:
            return jsonify({"message": "Nenhuma tabela válida encontrada"}), 404

        # Unir todas as tabelas apenas se houver dados
        if all_data:
            final_df = pd.concat(all_data, ignore_index=True)

            final_df.to_csv('tabelas_unificadas.csv', index=False, encoding='utf-8-sig', sep=';')
            final_df.to_excel('tabelas_unificadas.xlsx')

            print("Tabela unificada salva")
        else:
            print("Nenhuma tabela válida encontrada para unificação.")

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
