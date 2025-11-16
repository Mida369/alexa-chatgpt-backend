from flask import Flask, request, jsonify
import os
import json
import openai

app = Flask(__name__)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

openai.api_key = OPENROUTER_API_KEY
openai.api_base = "https://openrouter.ai/api/v1"

AURA_MODEL = "deepseek/deepseek-chat-v3.1"


def chat_response(text):
    try:
        resp = openai.ChatCompletion.create(
            model=AURA_MODEL,
            messages=[
                {"role": "system", "content": "Sei Aura, assistente chiara, gentile e utile."},
                {"role": "user", "content": text},
            ],
        )
        return resp.choices[0].message["content"][:7900]
    except Exception as e:
        print("AI ERROR:", e)
        return "Mi dispiace, c'è stato un errore interno."


@app.get("/")
def health():
    return "Aura Online", 200


@app.post("/")
def alexa():
    data = request.get_json(force=True, silent=True) or {}
    print("📥 Alexa request:", json.dumps(data, indent=2, ensure_ascii=False))

    if "request" not in data:
        return _reply("Non ho capito, puoi ripetere?")

    r = data["request"]
    r_type = r.get("type")

    if r_type == "LaunchRequest":
        return _reply("Ciao, sono Aura. Come posso aiutarti?")

    if r_type == "IntentRequest":
        intent = r.get("intent", {})
        name = intent.get("name")

        if name in ("AMAZON.StopIntent", "AMAZON.CancelIntent"):
            return _reply("A presto!", end=True)

        if name == "AMAZON.HelpIntent":
            return _reply("Puoi parlarmi come ad una persona. Dimmi pure cosa vuoi.")

        if name == "AMAZON.FallbackIntent":
            slots = intent.get("slots", {})
            text = ""
            if slots:
                try:
                    text = next(iter(slots.values())).get("value", "")
                except:
                    pass
            if not text:
                text = "Cosa volevi dirmi?"

            ai = chat_response(text)
            return _reply(ai)

    return _reply("Non ho capito bene. Puoi ripetere?")


def _reply(text, end=False):
    return jsonify({
        "version": "1.0",
        "response": {
            "outputSpeech": {"type": "PlainText", "text": text},
            "shouldEndSession": end,
        },
    })
