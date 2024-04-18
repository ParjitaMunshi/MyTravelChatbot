from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import sqlite3

app = Flask(__name__)
CORS(app)

# OpenAI API key
openai.api_key = 'OpenAI API Key'

# SQLite travel database connection
conn = sqlite3.connect('travel_database.db', check_same_thread=False)

# Function to classify a query based on database schema
def classify_query(user_query):
    user_query_lower = user_query.lower()

    # Check for specific keywords related to tables or columns
    if 'holidaypackages' in user_query_lower or 'flights' in user_query_lower or 'locations' in user_query_lower:
        return 'database_query'
    elif 'attractions' in user_query_lower or 'accommodations' in user_query_lower or 'packageattractions' in user_query_lower:
        return 'database_query'
    else:
        return 'chatgpt_query'

def combine_database_prompts(query_prompt):
    return f"### A query to answer: {query_prompt}\nSELECT"

# Function to handle ChatGPT queries
def handle_chatgpt_query(user_query):
    print("User Query:", user_query)

    # Call OpenAI to generate a response using ChatGPT
    response = openai.Completion.create(
        engine="davinci-002",
        prompt=user_query,
        max_tokens=150,
        stop=["#", ";"]
    )

    print("ChatGPT Response:", response)

    # Extract the generated text from the response
    generated_text = response["choices"][0]["text"]

    return generated_text

# Function to handle the OpenAI response
def handle_response(response):
    query = response["choices"][0]["text"]
    if query.startswith("SELECT"):
        return query
    return f"SELECT {query}"

# Route to handle queries
@app.route('/query', methods=['POST'])
def handle_query():
    try:
        data = request.get_json()
        user_query = data.get('query', '').lower()

        # Classify query
        query_type = classify_query(user_query)

        if query_type == 'database_query':
            prompt = combine_database_prompts(user_query)

            # Call OpenAI to generate an SQL query from the prompt
            response = openai.Completion.create(
                engine="davinci-002",
                prompt=prompt,
                max_tokens=150,
                stop=["#", ";"]
            )

            sql_query = handle_response(response)

            cursor = conn.cursor()
            cursor.execute(sql_query)
            result = cursor.fetchall()

            return jsonify({'response': result})
        
        elif query_type == 'chatgpt_query':
            chatgpt_response = handle_chatgpt_query(user_query)
            return jsonify({'response': chatgpt_response})
        
        else:
            return jsonify({'error': 'Invalid query type'}), 400
    
    except Exception as e:
        print(f"Error: {str(e)}")  
        return jsonify({'error': f"Internal Server Error: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
