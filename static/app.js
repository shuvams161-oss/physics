function sendAnswer() {
    let box = document.getElementById("answer");
    let chat = document.getElementById("chat");

    let answer = box.value.trim();
    if (!answer) return;

    chat.innerHTML += `<div class="user">🧑 You: ${answer}</div>`;

    fetch("/ask", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({answer})
    })
    .then(res => res.json())
    .then(data => {
        chat.innerHTML += `
            <div class="bot">
                🤖 Score: ${data.score}/10<br>
                ${data.feedback}<br><br>
                <b>Next:</b> ${data.next_question}
            </div>
        `;

        box.value = "";
        chat.scrollTop = chat.scrollHeight;
    });
}


function finishInterview() {
    let chat = document.getElementById("chat");

    fetch("/finish", {method: "POST"})
    .then(res => res.json())
    .then(data => {

        chat.innerHTML += `
            <div class="bot">
                🏁 FINAL RESULT<br><br>
                Score: ${data.final_score}/10<br>
                Verdict: ${data.verdict}<br><br>
                Strengths: ${data.strengths}<br>
                Weaknesses: ${data.weaknesses}<br><br>
                ${data.summary}
            </div>
        `;
    });
}