from flask import Flask, request, jsonify
import openai
import os
import json

app = Flask(__name__)

# ---------- OPENAI API KEY ----------
openai.api_key = os.getenv("OPENAI_API_KEY")


# ---------- HELPER FUNCTION FOR CHATGPT ----------
def chatgpt_response(text):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "Sei Aura, un'assistente femminile chiara, utile e gentile. Rispondi sempre in modo naturale e conversazionale."
                },
                {"role": "user", "content": text}
            ]
        )
        return response.choices[0].message["content"]
    except Exception as e:
        # LOG dall'altra parte, ma non rompere Alexa
        print("❌ Errore OpenAI:", str(e))
        return "Mi dispiace, c'è stato un problema interno con l'intelligenza artificiale."


# ---------- HEALTH CHECK (RENDER) ----------
@app.route("/", methods=["GET"])
def health_check():
    return "Aura Online", 200


# ---------- MAIN ALEXA WEBHOOK ----------
@app.route("/", methods=["POST"])
def alexa_handler():
    try:
        data = request.get_json(force=True, silent=True) or {}
        print("📥 Richiesta Alexa:", json.dumps(data, indent=2, ensure_ascii=False))

        # Se per qualche motivo non c'è "request", rispondiamo comunque
        if "request" not in data:
            return jsonify({
                "version": "1.0",
                "response": {
                    "shouldEndSession": False,
                    "outputSpeech": {
                        "type": "PlainText",
                        "text": "C'è stato un problema nel capire la tua richiesta. Puoi ripetere?"
                    }
                }
            }), 200

        request_type = data["request"]["type"]

        # ---------- SKILL APERTA ----------
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
            }), 200

        # ---------- INTENT ----------
        if request_type == "IntentRequest":
            intent_obj = data["request"].get("intent", {})
            intent_name = intent_obj.get("name", "")

            # Intents base di Alexa da gestire esplicitamente
            if intent_name in ["AMAZON.StopIntent", "AMAZON.CancelIntent"]:
                return jsonify({
                    "version": "1.0",
                    "response": {
                        "shouldEndSession": True,
                        "outputSpeech": {
                            "type": "PlainText",
                            "text": "Va bene, a presto!"
                        }
                    }
                }), 200

            if intent_name == "AMAZON.HelpIntent":
                return jsonify({
                    "version": "1.0",
                    "response": {
                        "shouldEndSession": False,
                        "outputSpeech": {
                            "type": "PlainText",
                            "text": "Puoi parlarmi come parli ad una persona. Fammi una domanda o chiedimi un consiglio."
                        }
                    }
                }), 200

            # ---------- AMAZON.FallbackIntent → usa ChatGPT ----------
            if intent_name == "AMAZON.FallbackIntent":
                spoken_value = ""

                # se in futuro aggiungi slot, qui li leggi
                slots = intent_obj.get("slots", {})
                if slots:
                    try:
                        # prendi il primo slot disponibile
                        spoken_value = next(iter(slots.values())).get("value", "")
                    except StopIteration:
                        spoken_value = ""

                if not spoken_value:
                    # se non riusciamo a capire il testo, usiamo una frase neutra
                    spoken_value = "L'utente ha detto qualcosa, ma non riesco a leggere le parole."

                # Chiamata a ChatGPT
                ai = chatgpt_response(spoken_value)

                # Alexa ha un limite di lunghezza, per sicurezza tagliamo
                ai = ai.strip()
                if len(ai) > 7900:
                    ai = ai[:7900]

                return jsonify({
                    "version": "1.0",
                    "response": {
                        "shouldEndSession": False,
                        "outputSpeech": {
                            "type": "PlainText",
                            "text": ai
                        }
                    }
                }), 200

            # Se arriva un Intent diverso che non abbiamo gestito
            return jsonify({
                "version": "1.0",
                "response": {
                    "shouldEndSession": False,
                    "outputSpeech": {
                        "type": "PlainText",
                        "text": "Ho ricevuto la tua richiesta ma non ho ancora imparato a gestire questo tipo di domanda."
                    }
                }
            }), 200

        # ---------- SESSION ENDED ----------
        if request_type == "SessionEndedRequest":
            return jsonify({
                "version": "1.0",
                "response": {
                    "shouldEndSession": True,
                    "outputSpeech": {
                        "type": "PlainText",
                        "text": "Sessione terminata."
                    }
                }
            }), 200

        # ---------- FALLBACK GENERALE ----------
        return jsonify({
            "version": "1.0",
            "response": {
                "shouldEndSession": False,
                "outputSpeech": {
                    "type": "PlainText",
                    "text": "Non ho capito bene la tua richiesta. Puoi ripetere?"
                }
            }
        }), 200

    except Exception as e:
        # Qui catturiamo QUALSIASI errore per non mandare mai un 500 ad Alexa
        print("🔥 Errore generale nel handler Alexa:", str(e))
        return jsonify({
            "version": "1.0",
            "response": {
                "shouldEndSession": False,
                "outputSpeech": {
                    "type": "PlainText",
                    "text": "Mi dispiace, c'è stato un errore interno del servizio."
                }
            }
        }), 200


# ---------- REQUIRED FOR RENDER: 0.0.0.0 + PORT ----------
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

