const sessionId = Math.random().toString(36).slice(2);
const form = document.getElementById("form");
const input = document.getElementById("input");
const messages = document.getElementById("messages");

function add(who, text) {
  const p = document.createElement("p");
  p.className = who === "You" ? "user" : "bot";
  p.textContent = text;
  messages.appendChild(p);
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const question = input.value.trim();
  if (!question) return;
  add("You", question);
  input.value = "";

  const thinking = document.createElement("p"); // new
  thinking.className = "bot"; // new
  thinking.textContent = "Thinking..."; // new
  messages.appendChild(thinking); // new

  try {
    const res = await fetch("/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, session_id: sessionId }),
    });
    thinking.remove();
    if (res.status === 429) {
      add("Bot", "You've hit the limit (10/hour, 30/day). Try again later.");
    } else {
      const data = await res.json();
      add("Bot", data.answer || "Something went wrong.");
    }
  } catch {
    thinking.remove();
    add("Bot", "Something went wrong. Please try again.");
  }
});
