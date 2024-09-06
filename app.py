from flask import Flask, request, jsonify, send_from_directory
import requests
import os

app = Flask(__name__)

# Configuration for API and Telegram Bot
API_KEY = "8790dce6c8ea45cdb0bed5e8bfe784c9"
ENDPOINT = "https://questionai.openai.azure.com/openai/deployments/gpt-4o/chat/completions?api-version=2024-02-15-preview"
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/"

# Ensure environment variables are loaded
if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    raise ValueError("Telegram bot token and chat ID must be set as environment variables.")

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    if 'message' in data and 'chat' in data['message']:
        chat_id = data['message']['chat']['id']
        text = data['message']['text']

        if text == '/start':
            send_message(chat_id, 'Bot is working')
        else:
            send_message(chat_id, 'Unsupported command')
    else:
        return jsonify({"error": "Invalid webhook data"}), 400
    
    return jsonify(status="ok")

@app.route('/ask', methods=['GET'])
def ask():
    query = request.args.get('query')
    if not query:
        return jsonify({"error": "No query parameter provided"}), 400

    user_ip = request.remote_addr
    telegram_username = request.args.get('username', 'unknown')
    telegram_name = request.args.get('name', 'unknown')
    telegram_user_id = request.args.get('user_id', 'unknown')

    # Log user details to Telegram chat
    log_message = (
        f"IP Address: {user_ip}\n"
        f"Telegram Username: {telegram_username}\n"
        f"Telegram Name: {telegram_name}\n"
        f"Telegram User ID: {telegram_user_id}"
    )
    send_message(TELEGRAM_CHAT_ID, log_message)
    
    # Get response from API
    response = get_response_from_api(query)
    
    if 'error' in response:
        return jsonify({"error": response['error']}), 500
    else:
        answer = response.get('choices', [{}])[0].get('message', {}).get('content', 'No response content')
        return jsonify({"response": answer})

def get_response_from_api(question):
    payload = {
        "messages": [
            {
                "role": "system",
                "content": [
                    {
                        "type": "text",
                        "text": "You are an AI assistant that helps people find information."
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": question
                    }
                ]
            }
        ],
        "temperature": 0.7,
        "top_p": 0.95,
        "max_tokens": 800
    }

    try:
        response = requests.post(ENDPOINT, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        return {"error": f"Failed to make the request. Error: {e}"}

def send_message(chat_id, text):
    url = TELEGRAM_API_URL + 'sendMessage'
    payload = {'chat_id': chat_id, 'text': text}
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Failed to send message to Telegram. Error: {e}")

if __name__ == '__main__':
    app.run(debug=True)
