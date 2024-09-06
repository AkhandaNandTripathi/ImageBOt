from flask import Flask, request, jsonify, render_template_string
import openai
import requests
from io import BytesIO
import os

app = Flask(__name__)

# Configuration from environment variables
TELEGRAM_API_URL = f"https://api.telegram.org/bot{os.getenv('TELEGRAM_BOT_TOKEN')}/"
AZURE_API_KEY = os.getenv('AZURE_API_KEY')
AZURE_ENDPOINT = os.getenv('AZURE_ENDPOINT')
API_VERSION = os.getenv('API_VERSION')

openai.api_key = AZURE_API_KEY

@app.route('/')
def home():
    # Display @DhanRakShak on the deployed HTML page
    return render_template_string('<html><body><h1>@DhanRakShak</h1></body></html>')

@app.route('/generate_image', methods=['POST'])
def generate_image():
    data = request.json
    prompt = data.get('query', '')
    chat_id = data.get('chat_id')

    if prompt == '/start':
        send_message_to_telegram(chat_id, 'Bot is working. Dev @DhanRakShak')
        return jsonify({'status': 'success'})

    try:
        # Generate image using DALL-E 3
        result = openai.Image.create(
            model="Dalle3",
            prompt=prompt,
            n=1
        )

        image_url = result['data'][0]['url']
        img_response = requests.get(image_url)
        img_bytes = BytesIO(img_response.content)

        # Send the image to Telegram
        send_image_to_telegram(chat_id, img_bytes)

        return jsonify({'status': 'success'})
    except Exception as e:
        send_message_to_telegram(chat_id, f"Error occurred: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/ask', methods=['POST'])
def ask():
    data = request.json
    question = data.get('question', '')
    chat_id = data.get('chat_id')

    headers = {
        "Content-Type": "application/json",
        "api-key": AZURE_API_KEY,
    }

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
        response = requests.post(f"{AZURE_ENDPOINT}/openai/deployments/avyuktgpt/chat/completions?api-version={API_VERSION}", headers=headers, json=payload)
        response.raise_for_status()
        answer = response.json().get('choices', [{}])[0].get('text', 'No answer')
    except requests.RequestException as e:
        answer = f"Failed to make the request. Error: {e}"

    # Send the answer to Telegram
    send_message_to_telegram(chat_id, answer)

    return jsonify({'status': 'success'})

def send_image_to_telegram(chat_id, img_bytes):
    try:
        files = {'photo': ('image.png', img_bytes, 'image/png')}
        requests.post(TELEGRAM_API_URL + 'sendPhoto', data={'chat_id': chat_id}, files=files)
    except requests.RequestException as e:
        print(f"Failed to send image to Telegram: {e}")

def send_message_to_telegram(chat_id, text):
    try:
        requests.post(TELEGRAM_API_URL + 'sendMessage', data={'chat_id': chat_id, 'text': text})
    except requests.RequestException as e:
        print(f"Failed to send message to Telegram: {e}")

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    if 'message' in data:
        chat_id = data['message']['chat']['id']
        text = data['message'].get('text', '')

        if text == '/start':
            send_message_to_telegram(chat_id, 'Bot is working. Dev @DhanRakShak')
        else:
            send_message_to_telegram(chat_id, "Unknown command or error.")
        
    return jsonify({'status': 'success'}), 200

if __name__ == '__main__':
    app.run(debug=True)
