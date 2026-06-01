import os
from flask import Flask, render_template, request, jsonify, session
import google.generativeai as genai
from dotenv import load_dotenv
from PyPDF2 import PdfReader

load_dotenv()

app = Flask(__name__, template_folder="../templates", static_folder="../static")
app.secret_key = os.getenv("SECRET_KEY", "dev_secret")

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel("gemini-2.5-flash")


def call_ai(prompt):
    try:
        return model.generate_content(prompt).text
    except Exception as e:
        return f"ERROR: {str(e)}"


# ---------- RESUME PARSER ----------
def extract_resume(file):
    if not file:
        return ""

    text = ""

    try:
        if file.filename.endswith(".pdf"):
            reader = PdfReader(file)
            for page in reader.pages:
                text += page.extract_text() or ""

        elif file.filename.endswith(".txt"):
            text = file.read().decode("utf-8")

    except:
        return ""

    return text[:8000]


# ---------- HOME ----------
@app.route("/")
def home():
    return render_template("index.html")


# ---------- INTERVIEW START + RESUME ----------
@app.route("/interview", methods=["GET", "POST"])
def interview():
    role = request.args.get("role", "Software Engineer").strip()

    session["role"] = role
    session["history"] = []
    session["scores"] = []

    resume_text = ""

    if request.method == "POST":
        file = request.files.get("resume")
        resume_text = extract_resume(file)

    session["resume"] = resume_text

    prompt = f"""
You are a strict technical interviewer.

Role: {role}

Candidate Resume:
{resume_text if resume_text else "No resume provided"}

Ask ONLY the first interview question.
Make it slightly personalized if resume exists.
"""

    first_q = call_ai(prompt)

    session["history"].append({"q": first_q, "a": ""})

    return render_template("interview.html", role=role, first_question=first_q)


# ---------- ASK / NEXT QUESTION ----------
@app.route("/ask", methods=["POST"])
def ask():
    data = request.json
    answer = data.get("answer", "").strip()

    role = session.get("role", "Software Engineer")
    history = session.get("history", [])
    scores = session.get("scores", [])
    resume = session.get("resume", "")

    last_q = history[-1]["q"]

    conversation = ""
    for h in history:
        conversation += f"Q: {h['q']}\nA: {h['a']}\n"

    prompt = f"""
You are a strict technical interviewer.

Role: {role}

Candidate Resume:
{resume}

Full Interview:
{conversation}

Latest Question:
{last_q}

Candidate Answer:
{answer}

Return ONLY JSON:
{{
  "score": 0-10,
  "feedback": "short feedback",
  "next_question": "next question"
}}
"""

    response = call_ai(prompt)

    try:
        data = eval(response) if "{" in response else {}
    except:
        return jsonify({
            "score": 0,
            "feedback": "AI response error",
            "next_question": response
        })

    score = data.get("score", 0)

    history[-1]["a"] = answer
    history.append({"q": data.get("next_question", "Next question error"), "a": ""})

    scores.append(score)

    session["history"] = history
    session["scores"] = scores

    return jsonify(data)


# ---------- FINISH INTERVIEW ----------
@app.route("/finish", methods=["POST"])
def finish():
    history = session.get("history", [])
    scores = session.get("scores", [])
    resume = session.get("resume", "")
    role = session.get("role", "Software Engineer")

    avg = sum(scores) / len(scores) if scores else 0

    convo = ""
    for h in history:
        convo += f"Q: {h['q']}\nA: {h['a']}\n"

    prompt = f"""
You are a senior recruiter.

Role: {role}

Resume:
{resume}

Interview:
{convo}

Average Score: {avg}

Return:
- final_score (0-10)
- verdict (HIRE or NO HIRE)
- strengths
- weaknesses
- summary
"""

    result = call_ai(prompt)

    return jsonify({
        "final_score": avg,
        "verdict": "HIRE" if avg >= 7 else "NO HIRE",
        "strengths": "Based on AI analysis",
        "weaknesses": "Based on AI analysis",
        "summary": result
    })


app = app