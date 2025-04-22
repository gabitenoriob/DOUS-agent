from io import BytesIO, StringIO
import os

import pandas as pd
from flask import Flask, make_response, render_template, request, jsonify
import spacy
import re
from send import execute_query
from pln import corrigir_tabela_de_texto
from utils import clean_data, extract_portaria_info, extract_tables_from_xml, standardize_dataframe
from llm import format_response, generate_query
from llm import llm_local


app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/extrair-portarias', methods=['GET'])
def extrair_portarias():
    try:
        print("Iniciando a função '/extrair-portarias'...")

        query = """
        SELECT id, texto, pubName, pubDate, artType, artCategory, Ementa
        FROM dous
        WHERE 
            artType = 'Portaria' AND
            artCategory LIKE 'Ministério da Saúde%' AND
            (
                texto LIKE '%incremento temporário%' OR
                texto LIKE '%rateio dos recursos de transferência%' OR
                texto LIKE '%emendas parlamentares%' OR
                texto LIKE '%aplicação de emenda%' OR
                texto LIKE '%atenção especializada à saúde%' OR
                texto LIKE '%relatório anual de gestão RAG%' OR
                texto LIKE '%Bloco de Manutenção das Ações e Serviços Públicos de Saúde%'
            )
        """
        print("Executando consulta SQL...")
        portarias = execute_query(query)

        print(f"Portarias retornadas: {len(portarias) if portarias else 0}")

        with open('portarias.txt', 'w', encoding='utf-8') as f:
            for portaria in portarias:
                f.write(f"{portaria}\n")
        print("Arquivo 'portarias.txt' criado com sucesso.")

        if not portarias:
            return jsonify({"message": "Nenhuma portaria encontrada com os critérios especificados"}), 404

        all_data = []
        csv_filename = 'portarias.csv'
        excel_filename = 'portarias.xlsx'

        for idx, portaria in enumerate(portarias):
            try:
                print(f"\n🔍 Processando portaria {idx + 1} de {len(portarias)}...")
                texto_portaria = portaria[1]
                portaria_info = extract_portaria_info(texto_portaria)

                print(f"Portaria Nº {portaria_info.get('numero_portaria')} - Data: {portaria_info.get('data_portaria')}")

                tables = extract_tables_from_xml(texto_portaria)
                print(f"Tabelas extraídas: {len(tables)}")

                for table_df in tables:
                    try:
                        # Etapa 1: padronizar
                        standardized_df = standardize_dataframe(table_df, portaria_info)

                        # Etapa 2: corrigir com LLM (se disponível)
                        if llm_local:
                            standardized_df = corrigir_tabela_de_texto(texto_portaria, llm_local)

                        # Adicionar metadados
                        standardized_df['numero da portaria'] = portaria_info.get('numero_portaria', '')
                        standardized_df['data'] = portaria_info.get('data_portaria', '')

                        # Limpeza final
                        standardized_df = clean_data(standardized_df)

                        # Salvar CSV e Excel
                        standardized_df.to_csv(csv_filename, mode='a', index=False, encoding='utf-8-sig', sep=';', header=not os.path.exists(csv_filename))
                        standardized_df.to_excel(excel_filename, index=False, header=not os.path.exists(excel_filename))

                        all_data.append(standardized_df)

                    except Exception as e:
                        print(f"⚠️ Erro ao processar tabela: {str(e)}")
                        continue

            except Exception as e:
                print(f"⚠️ Erro ao processar portaria {idx + 1}: {str(e)}")
                continue

        if not all_data:
            return jsonify({"message": "Nenhuma tabela válida encontrada"}), 404

        final_df = pd.concat(all_data, ignore_index=True)
        final_df = clean_data(final_df)

        final_df.to_csv('tabelas_unificadas.csv', index=False, encoding='utf-8-sig', sep=';')
        final_df.to_excel('tabelas_unificadas.xlsx', index=False)

        print("\n✅ Tabela unificada salva com sucesso.")

        return jsonify({
            "data": final_df.to_dict(orient='records'),
            "count": len(final_df),
            "status": "success"
        })

    except Exception as e:
        print(f"❌ Erro no endpoint '/extrair-portarias': {str(e)}")
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
