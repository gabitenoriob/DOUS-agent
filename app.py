from flask import Flask, render_template, request, jsonify
import spacy
import re
from send import execute_query
from query import extract_info, build_query
from llm import format_response, generate_query


app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask_question():
    user_question = request.json.get("question")
    
    if not user_question:
        return jsonify({"response": "Por favor, faça uma pergunta válida."})

    # #Gera query com PLN
    # extracted_data = extract_info(refine_question)
    # query = build_query(extracted_data)

    # A LLM gera a query correta
    query = generate_query(user_question)
    print(f"Query gerada pela LLM: {query}")

    if not query:
        return jsonify({"response": "Não foi possível entender a pergunta."})

    result = execute_query(query)
    
    if not result:
        return jsonify({"response": "Nenhum resultado encontrado."})

    # Remove duplicatas
    result = list(set(result))
    
    #Formata a resposta com PLN
    # if len(result) == 1 and len(result[0]) == 1:
    #     return jsonify({"response": result[0][0]})
    
    # return jsonify({"response": [list(row) for row in result]})

    # Formata a resposta com a LLM
    formatted_response = format_response(user_question, result)

    return jsonify({"response": formatted_response})

if __name__ == '__main__':
    app.run(debug=True)
