from flask import Flask, request, jsonify
import openai
import os

app = Flask(__name__)

# LOAD OPENAI API KEY
openai.api_key = os.getenv("OPENAI_API_KEY")


# ---------- HELPER FUNCTION FOR CHATGPT ----------
def chatgpt_response(text):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Sei Aura, un'assistente femminile chiara, utile e gentile."},
                {"role": "user", "content": text}
            ]
        )
        return response.choices[0].message["content"]
    except Exception as e:
        return f"Mi dispiace, si è verificato un errore interno: {str(e)}"


# ---------- HEALTH CHECK (REQUIRED BY RENDER & ALEXA) ----------
@app.route("/", methods=["GET"])
def health_check():
    return "Aura Online", 200


# ---------- MAIN ALEXA WEBHOOK ----------
@app.route("/", methods=["POST"])
def alexa_handler():
    data = request.json

    # --- Extract request type ---
    request_type = data["request"]["type"]

    # --- SKILL OPENED ---
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

    # --- INTENT REQUEST ---
    if request_type == "IntentRequest":
        intent = data["request"]["intent"]["name"]

        # ---- AMAZON.FallbackIntent: catch all user speech ----
        if intent == "AMAZON.FallbackIntent":
            # extract user text if available, otherwise fallback
            spoken_value = ""

            try:
                # If you add slots in the future
                slots = data["request"]["intent"].get("slots", {})
                spoken_value = next(iter(slots.values()))["value"]
            except:
                spoken_value = "Puoi ripetere?"

            if not spoken_value:
                spoken_value = "Puoi ripetere?"

            # Call ChatGPT
            ai = chatgpt_response(spoken_value)

            return jsonify({
                "version": "1.0",
                "response": {
                    "shouldEndSession": False,
                    "outputSpeech": {
                        "type": "PlainText",
                        "text": ai
                    }
                }
            })

    # --- IF NOTHING MATCHES (safe fallback) ---
    return jsonify({
        "version": "1.0",
        "response": {
            "shouldEndSession": False,
            "outputSpeech": {
                "type": "PlainText",
                "text": "Non ho capito bene, puoi ripetere?"
            }
        }
    })


# ---------- REQUIRED FOR RENDER: 0.0.0.0 + PORT ----------
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
