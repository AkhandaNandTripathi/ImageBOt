from flask import Flask, request, jsonify
import openai
import requests
from io import BytesIO

app = Flask(__name__)

# Configuration
TELEGRAM_API_URL = 'https://api.telegram.org/bot7282854458:AAEgIt3OigoszFAFGnrYcnvJbIlRbDN9E4I/'
AZURE_API_KEY = "dc0b54078720445e94cb7eaaa33bb9e7"
AZURE_ENDPOINT = "https://avyukt.openai.azure.com/"
API_VERSION = "2024-05-01-preview"

openai.api_key = AZURE_API_KEY

@app.route('/generate_image', methods=['POST'])
def generate_image():
    data = request.json
    prompt = data.get('query', '')
    chat_id = data.get('chat_id')

    if prompt == '/status':
        send_message_to_telegram(chat_id, 'Bot is working. Dev @DhanRakShak')
        return jsonify({'status': 'success'})

    # Generate image using DALL-E 3
    result = openai.Image.create(
        model="Dalle3",
        prompt=prompt,
        n=1,
        api_version=API_VERSION,
        azure_endpoint=AZURE_ENDPOINT,
        api_key=AZURE_API_KEY
    )

    image_url = result['data'][0]['url']
    img_response = requests.get(image_url)
    img_bytes = BytesIO(img_response.content)

    # Send the image to Telegram
    send_image_to_telegram(chat_id, img_bytes)

    return jsonify({'status': 'success'})

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
        response = requests.post(f"{AZURE_ENDPOINT}/openai/deployments/avyuktgpt/chat/completions?api-version=2024-02-15-preview", headers=headers, json=payload)
        response.raise_for_status()
        answer = response.json().get('choices', [{}])[0].get('text', 'No answer')
    except requests.RequestException as e:
        answer = f"Failed to make the request. Error: {e}"

    # Send the answer to Telegram
    send_message_to_telegram(chat_id, answer)

    return jsonify({'status': 'success'})

def send_image_to_telegram(chat_id, img_bytes):
    files = {'photo': ('image.png', img_bytes, 'image/png')}
    requests.post(TELEGRAM_API_URL + 'sendPhoto', data={'chat_id': chat_id}, files=files)

def send_message_to_telegram(chat_id, text):
    requests.post(TELEGRAM_API_URL + 'sendMessage', data={'chat_id': chat_id, 'text': text})

if __name__ == '__main__':
    app.run(debug=True)
