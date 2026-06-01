import os
from flask import Flask, render_template, request, jsonify, session
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(
    __name__,
    template_folder="../templates",
    static_folder="../static"
)

# Secret key
app.secret_key = os.getenv("SECRET_KEY", "fallback_dev_secret")

# Gemini setup
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY not found in environment variables.")

genai.configure(api_key=GEMINI_API_KEY)

# Model
model = genai.GenerativeModel("gemini-2.5-flash")


def ask_gemini(prompt):
    """
    Sends prompt to Gemini and returns response text.
    Handles quota errors gracefully.
    """
    try:
        response = model.generate_content(prompt)

        if hasattr(response, "text") and response.text:
            return response.text

        return "⚠️ Gemini returned an empty response."

    except Exception as e:
        error = str(e)

        if "429" in error:
            return (
                "🚦 Rate limit reached. Please wait about a minute "
                "before continuing the interview."
            )

        if "API_KEY" in error.upper():
            return "🔑 Gemini API key appears invalid."

        return f"⚠️ AI service temporarily unavailable."


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/interview")
def interview():

    role = request.args.get("role", "Software Engineer").strip()

    session["role"] = role
    session["history"] = []

    first_prompt = f"""
You are an expert professional interviewer conducting an interview for a {role} position.

Your task:
- Introduce yourself briefly.
- Ask exactly ONE opening interview question relevant to the {role} role.

Rules:
- Professional tone.
- No explanations.
- No multiple questions.
- Keep it concise.
"""

    first_question = ask_gemini(first_prompt)

    history = [{"q": first_question, "a": ""}]
    session["history"] = history

    return render_template(
        "interview.html",
        role=role,
        first_question=first_question
    )


@app.route("/ask", methods=["POST"])
def ask():

    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "reply": "Invalid request."
        }), 400

    user_answer = data.get("answer", "").strip()

    if not user_answer:
        return jsonify({
            "reply": "Please provide an answer."
        })

    role = session.get("role", "Software Engineer")
    history = session.get("history", [])

    if not history:
        return jsonify({
            "reply": "Session expired. Please restart the interview."
        })

    last_question = history[-1]["q"]

    prompt = f"""
You are a professional interviewer for a {role} position.

Previous Interview Question:
{last_question}

Candidate Answer:
{user_answer}

Task:

1. Give brief professional feedback on the candidate's answer.
2. Ask the next logical interview question.
3. Increase difficulty gradually.

Rules:
- Be realistic.
- Be constructive.
- Keep the entire response under 120 words.
- Stay in interviewer character.
"""

    reply = ask_gemini(prompt)

    history.append({
        "q": reply,
        "a": user_answer
    })

    session["history"] = history

    return jsonify({
        "reply": reply
    })


# Vercel entrypoint
app = app

if __name__ == "__main__":
    app.run(debug=True)