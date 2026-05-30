function sendAnswer() {
    let answerBox = document.getElementById("answer");
    let answer = answerBox.value;

    if (!answer) return;

    let chat = document.getElementById("chat");

    // show user answer
    chat.innerHTML += `<div class="user">🧑 You: ${answer}</div>`;

    fetch("/ask", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ answer: answer })
    })
    .then(res => res.json())
    .then(data => {

        chat.innerHTML += `<div class="bot">🤖 Feedback: ${data.feedback}</div>`;
        chat.innerHTML += `<div class="bot">🤖 Next: ${data.next_question}</div>`;

        answerBox.value = "";
    });
}