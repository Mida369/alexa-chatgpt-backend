from flask import Flask, request, jsonify
import openai
import os

app = Flask(__name__)

# OPENAI API KEY
openai.api_key = os.getenv("OPENAI_API_KEY")

def chatgpt_response(text):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini", 
            messages=[
                {"role": "system", "content": "Sei Aura, un'assistente femminile gentile, chiara e concisa."},
                {"role": "user", "content": text}
            ]
        )
        return response["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Errore nel contattare l'intelligenza artificiale: {str(e)}"

def alexa_speak(text):
    return {
        "version": "1.0",
        "response": {
            "shouldEndSession": False,
            "outputSpeech": {
                "type": "PlainText",
                "text": text
            }
        }
    }

@app.route("/", methods=["POST"])
def alexa_webhook():
    data = request.json
    req_type = data["request"]["type"]

    # Quando l’utente dice: “Alexa, apri Aura”
    if req_type == "LaunchRequest":
        return jsonify(alexa_speak("Ciao, sono Aura. Come posso aiutarti?"))

    # Quando l’utente parla con Aura
    if req_type == "IntentRequest":
        intent = data["request"]["intent"]["name"]

        # aura Intent (non usato, placeholder)
        if intent == "AuraIntent":
            spoken = data["request"]["intent"]["slots"]
            return jsonify(alexa_speak("Dimmi pure."))

        # FallbackIntent → cattura TUTTE le frasi
        if intent == "AMAZON.FallbackIntent":
            try:
                user_text = data["request"]["intent"]["slots"]  # Nessuno slot, prendiamo da history
            except:
                user_text = data["request"]["intent"].get("name", "non capito")

            # Test: prendiamo la frase da "request['intent']['name']" (fallback)
            spoken_text = data["request"]["intent"].get("slots", None)
            user_utterance = data["request"]["intent"].get("name", "non capito")

            # PROVA: prendiamo il testo reale dal campo 'request' se c'è
            try:
                user_text = data["request"]["intent"]["slots"]["phrase"]["value"]
            except:
                user_text = "Fammi una domanda."

            ai_reply = chatgpt_response(user_text)
            return jsonify(alexa_speak(ai_reply))

    # Se non riconosciamo nulla
    return jsonify(alexa_speak("Non ho capito ma sono qui per te."))

@app.route("/ping")
def ping():
    return "OK"

if __name__ == '__main__':
    app.run(debug=True)


