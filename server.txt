const express = require('express');
const bodyParser = require('body-parser');
const fetch = require('node-fetch');
const FormData = require('form-data');

const app = express();
app.use(bodyParser.json());

const TELEGRAM_API_URL = 'https://api.telegram.org/bot<YOUR_BOT_TOKEN>/';
const API_KEY = "dc0b54078720445e94cb7eaaa33bb9e7";
const AZURE_API_KEY = "dc0b54078720445e94cb7eaaa33bb9e7";
const ENDPOINT = "https://avyukt.openai.azure.com/";
const API_VERSION = "2024-05-01-preview";

const OpenAI = require('openai');
const openai = new OpenAI({ apiKey: AZURE_API_KEY });

app.post('/generate_image', async (req, res) => {
    const { query, chat_id } = req.body;

    if (query === '/status') {
        await fetch(TELEGRAM_API_URL + 'sendMessage', {
            method: 'POST',
            body: new URLSearchParams({ chat_id, text: 'Bot is working. Dev @DhanRakShak' }),
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
        });
        return res.json({ status: 'success' });
    }

    try {
        const result = await openai.images.generate({
            model: "Dalle3",
            prompt: query,
            n: 1,
            apiVersion: API_VERSION,
            azureEndpoint: ENDPOINT,
            apiKey: AZURE_API_KEY
        });

        const imageUrl = result.data[0].url;
        const imgResponse = await fetch(imageUrl);
        const imgBuffer = await imgResponse.buffer();

        const form = new FormData();
        form.append('photo', imgBuffer, { filename: 'image.png', contentType: 'image/png' });
        form.append('chat_id', chat_id);

        await fetch(TELEGRAM_API_URL + 'sendPhoto', {
            method: 'POST',
            body: form
        });

        res.json({ status: 'success' });
    } catch (error) {
        console.error('Error:', error);
        res.json({ status: 'error', message: 'Failed to generate image' });
    }
});

app.post('/ask', async (req, res) => {
    const { question, chat_id } = req.body;

    const headers = {
        "Content-Type": "application/json",
        "api-key": API_KEY,
    };

    const payload = {
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
    };

    try {
        const response = await fetch(`${ENDPOINT}/openai/deployments/avyuktgpt/chat/completions?api-version=2024-02-15-preview`, {
            method: 'POST',
            headers: headers,
            body: JSON.stringify(payload)
        });

        const responseJson = await response.json();
        const answer = responseJson.choices[0]?.text || 'No answer';

        await fetch(TELEGRAM_API_URL + 'sendMessage', {
            method: 'POST',
            body: new URLSearchParams({ chat_id, text: answer }),
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
        });

        res.json({ status: 'success' });
    } catch (error) {
        console.error('Error:', error);
        await fetch(TELEGRAM_API_URL + 'sendMessage', {
            method: 'POST',
            body: new URLSearchParams({ chat_id, text: `Failed to make the request. Error: ${error.message}` }),
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
        });
        res.json({ status: 'error' });
    }
});

app.listen(3000, () => {
    console.log('Server running on port 3000');
});
