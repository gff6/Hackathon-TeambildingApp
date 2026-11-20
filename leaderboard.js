// LEADERBOARD
// Mock data. "isMe" highlights the current user's row.
const users = [
  { name: "You",   xp: 245, weeklyXp: 60,  isMe: true },
  { name: "Mia",   xp: 340, weeklyXp: 90 },
  { name: "Jonas", xp: 210, weeklyXp: 150 },
  { name: "Lena",  xp: 80,  weeklyXp: 40 },
  { name: "Ali",   xp: 275, weeklyXp: 20 },
];

let range = "weeklyXp"; // "weeklyXp" or "xp" (all time)

function renderLeaderboard() {
  // [...users] copies the array so sorting doesn't change the original
  const sorted = [...users].sort((a, b) => b[range] - a[range]);
  const medals = ["🥇", "🥈", "🥉"];

  document.getElementById("leaderboard-list").innerHTML = sorted.map((user, i) => `
    <li class="${user.isMe ? "me" : ""}">
      <span>${medals[i] || (i + 1) + "."} ${user.name}</span>
      <strong>${user[range]} XP</strong>
    </li>
  `).join("");
}

// Weekly / all-time buttons
document.querySelectorAll(".range").forEach((button) => {
  button.addEventListener("click", () => {
    document.querySelectorAll(".range").forEach((b) => b.classList.remove("active"));
    button.classList.add("active");
    range = button.dataset.range;
    renderLeaderboard();
  });
});

renderLeaderboard();
