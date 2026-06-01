import os
from flask import Flask, render_template, request, jsonify, session
import google.generativeai as genai
from dotenv import load_dotenv

# Load variables from .env file securely
load_dotenv()

app = Flask(__name__)
app.secret_key = "devkey123_secured"

# SAFE WAY: Automatically reads the key from your .env file
# Make sure your .env file has: GEMINI_API_KEY=your_actual_key
# RIGHT WAY: Reads it securely out of your .env file
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Using the blazing fast, free-tier compatible model
model = genai.GenerativeModel("gemini-2.5-flash")

def ask_gemini(prompt):
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"⚠️ API Error: Ensure your GEMINI_API_KEY is correct in your .env file. Details: {str(e)}"

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/interview")
def interview():
    # Capture the exact role typed by the user on the home page landing input
    role = request.args.get("role", "Software Engineer").strip()
    session["role"] = role
    session["history"] = []

    # DYNAMIC PROMPT: Injecting the actual role variable directly into the system instructions!
    first_prompt = f"""
You are an expert, professional job interviewer conducting a high-pressure interview for a {role} position.

Task:
Start the interview by introducing yourself briefly and asking exactly ONE relevant, technical, or situational opening interview question tailored specifically for a candidate applying as a {role}.

Rules:
- Do not explain anything else.
- Keep your total response concise and engaging.
"""

    first_question = ask_gemini(first_prompt)
    
    # Store history matching the format
    session["history"].append({"q": first_question, "a": ""})
    session.modified = True

    # Passing 'role' and 'first_question' so your premium template stays fully styled!
    return render_template("interview.html", role=role, first_question=first_question)

@app.route("/ask", methods=["POST"])
def ask():
    data = request.json
    user_answer = data.get("answer", "").strip()

    role = session.get("role", "Software Engineer")
    history = session.get("history", [])

    if not history:
        return jsonify({"reply": "Session expired. Please restart the interview from the home page."})

    last_question = history[-1]["q"]

    # DYNAMIC PROGRESSION PROMPT: Evaluates the candidate's answer based on their specific target role
    prompt = f"""
You are a professional job interviewer conducting an interview for a {role} position.

Previous Interviewer Question:
"{last_question}"

Candidate's Response:
"{user_answer}"

Task:
Perform exactly two tasks sequentially:
1. Provide a sharp, realistic 1-2 sentence evaluation/feedback on their answer (highlight what was good or what critical details they missed for a {role} level standard).
2. Smoothly transition and ask the NEXT logical, increasingly challenging interview question for a {role}.

Rules:
- Be strict, constructive, and realistic.
- Do not break character. Keep your total response brief.
"""

    reply = ask_gemini(prompt)

    # Log this exchange to conversation history
    history.append({"q": reply, "a": user_answer})
    session["history"] = history
    session.modified = True

    return jsonify({"reply": reply})
app = app
if __name__ == "__main__":
    app.run(debug=True)