import os
import json
import logging
import openai  # usiamo il client openai ma puntato a OpenRouter

# ---------- CONFIG LOGGING ----------
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# ---------- OPENROUTER API CONFIG ----------
# Imposta questa variabile in Lambda:
#   OPENROUTER_API_KEY = "sk-or-v1-...."
openrouter_api_key = os.getenv("OPENROUTER_API_KEY")

# Configuriamo il client openai per parlare con OpenRouter
openai.api_key = openrouter_api_key
openai.base_url = "https://openrouter.ai/api/v1"

# Scegli il modello che vuoi usare da OpenRouter
# Esempi possibili:
#   "deepseek/deepseek-chat"
#   "meta-llama/llama-3.1-70b-instruct"
#   "openai/gpt-4o-mini"
AURA_MODEL = "openai/gpt-4o-mini"


# ---------- HELPER: CALL AURA VIA OPENROUTER ----------
def chatgpt_response(text: str) -> str:
    """
    Invia il testo utente ad Aura (via OpenRouter) e ritorna la risposta.
    """
    if not openrouter_api_key:
        logger.error("OPENROUTER_API_KEY non impostata")
        return "Mi dispiace, il servizio di intelligenza artificiale non è configurato correttamente."

    try:
        response = openai.ChatCompletion.create(
            model=AURA_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Sei Aura, un'assistente femminile chiara, utile e gentile. "
                        "Rispondi sempre in italiano, con tono naturale e conversazionale."
                    ),
                },
                {"role": "user", "content": text},
            ],
        )
        ai_text = response.choices[0].message["content"]
        return ai_text.strip()[:7900]  # taglio difensivo per Alexa
    except Exception as e:
        logger.exception("Errore durante la chiamata a OpenRouter")
        return "Mi dispiace, c'è stato un errore interno con il motore di intelligenza artificiale."


# ---------- HELPER: COSTRUISCI RISPOSTA ALEXA ----------
def build_speech_response(
    text: str,
    should_end_session: bool = False,
    session_attributes: dict | None = None,
) -> dict:
    if session_attributes is None:
        session_attributes = {}

    if len(text) > 7900:
        text = text[:7900]

    return {
        "version": "1.0",
        "sessionAttributes": session_attributes,
        "response": {
            "outputSpeech": {
                "type": "PlainText",
                "text": text,
            },
            "shouldEndSession": should_end_session,
        },
    }


# ---------- MAIN LAMBDA HANDLER ----------
def lambda_handler(event, context):
    """
    Entry point per Alexa → Lambda.
    """
    logger.info("📥 Alexa event: %s", json.dumps(event, ensure_ascii=False))

    try:
        request = event.get("request", {})
        request_type = request.get("type")
    except Exception:
        logger.exception("Formato evento inatteso")
        return build_speech_response(
            "Mi dispiace, non ho capito la richiesta.",
            should_end_session=False,
        )

    # ---- LaunchRequest (apertura skill) ----
    if request_type == "LaunchRequest":
        return build_speech_response(
            "Ciao, sono Aura. Come posso aiutarti?",
            should_end_session=False,
        )

    # ---- IntentRequest ----
    if request_type == "IntentRequest":
        intent = request.get("intent", {})
        intent_name = intent.get("name", "")

        # Stop / Cancel
        if intent_name in ("AMAZON.StopIntent", "AMAZON.CancelIntent"):
            return build_speech_response(
                "Va bene, a presto!",
                should_end_session=True,
            )

        # Help
        if intent_name == "AMAZON.HelpIntent":
            return build_speech_response(
                "Puoi parlarmi come ad una persona. Fammi una domanda, chiedimi un consiglio, oppure chiedimi di spiegarti qualcosa.",
                should_end_session=False,
            )

        # ---- FallbackIntent → chat libera con Aura ----
        if intent_name == "AMAZON.FallbackIntent":
            slots = intent.get("slots", {})
            spoken_value = ""

            if slots:
                try:
                    first_slot = next(iter(slots.values()))
                    spoken_value = first_slot.get("value", "") or ""
                except StopIteration:
                    spoken_value = ""

            if not spoken_value:
                spoken_value = (
                    "L'utente ha detto qualcosa, ma non riesco a leggere le parole precise."
                )

            ai_reply = chatgpt_response(spoken_value)

            return build_speech_response(
                ai_reply,
                should_end_session=False,
            )

        # Intent non gestiti esplicitamente
        return build_speech_response(
            "Ho ricevuto la tua richiesta, ma non ho ancora imparato a gestire questo tipo di domanda.",
            should_end_session=False,
        )

    # ---- SessionEndedRequest ----
    if request_type == "SessionEndedRequest":
        return build_speech_response(
            "Sessione terminata.",
            should_end_session=True,
        )

    # ---- Default fallback ----
    return build_speech_response(
        "Non ho capito bene la tua richiesta.",
        should_end_session=False,
    )
