const askBtn = document.getElementById('askBtn');
const questionInput = document.getElementById('question');
const answerDiv = document.getElementById('answer');
const cooldownDiv = document.getElementById('cooldown');

let cooldownActive = false;

askBtn.onclick = async () => {
  if (cooldownActive) return;

  const question = questionInput.value.trim();
  if (!question) return alert("Please enter a question");

  askBtn.disabled = true;
  answerDiv.textContent = "Thinking...";

  const res = await fetch('/ask', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question })
  });

  const data = await res.json();
  console.log(data.answer, data)
  answerDiv.textContent = data.answer.output || "Something went wrong.";

  // Start cooldown
  cooldownActive = true;
  let seconds = 60;
  cooldownDiv.textContent = `Please wait ${seconds} seconds...`;

  const interval = setInterval(() => {
    seconds--;
    if (seconds <= 0) {
      clearInterval(interval);
      cooldownDiv.textContent = '';
      askBtn.disabled = false;
      cooldownActive = false;
    } else {
      cooldownDiv.textContent = `Please wait ${seconds} seconds...`;
    }
  }, 1000);
};