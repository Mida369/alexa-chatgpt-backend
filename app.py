from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/ping")
def ping():
    return "OK", 200

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    user_message = data.get("message", "")
    return jsonify({"reply": f"Test reply: you said '{user_message}'"})

@app.route("/")
def home():
    return "Alexa Backend Online", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
