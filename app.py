from flask import Flask, request, jsonify
import openai
import os

app = Flask(__name__)

# OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

def chatgpt_response(text):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Sei Aura, un'assistente femminile gentile e chiara."},
                {"role": "user", "content": text}
            ]
        )
        return response.choices[0].message["content"]
    except Exception as e:
        return f"Errore nel contattare Aura: {str(e)}"

@app.route("/", methods=["GET"])
def health_check():
    return "Aura Online", 200

@app.route("/", methods=["POST"])
def alexa_handler():
    data = request.json

    request_type = data["request"]["type"]

    # Skill open
    if request_type == "LaunchRequest":
        return jsonify({
            "version": "1.0",
            "response": {
                "shouldEndSession": False,
                "outputSpeech": {
                    "type": "PlainText",
                    "text": "Ciao, sono Aura. Come posso aiutarti?"
                }
            }
        })

    # User speaks
    if request_type == "IntentRequest":
        intent = data["request"]["intent"]["name"]

        # Fallback catches EVERYTHING
        if intent == "AMAZON.FallbackIntent":
            user_text = data["request"]["intent"].get("slots", {}).get("phrase", {}).get("value", "")
            if not user_text:
                user_text = data["request"]["intent"]["name"]
            ai_reply = chatgpt_response(user_text)

            return jsonify({
                "version": "1.0",
                "response": {
                    "shouldEndSession": False,
                    "outputSpeech": {
                        "type": "PlainText",
                        "text": ai_reply
                    }
                }
            })

    # If something goes wrong
    return jsonify({
        "version": "1.0",
        "response": {
            "shouldEndSession": False,
            "outputSpeech": {
                "type": "PlainText",
                "text": "Non ho capito, ma sono qui."
            }
        }
    })

@app.route("/ping")
def ping():
    return "OK", 200



