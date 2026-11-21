// TEAM NEWSFEED
// Mock data: newest post first. Replace with data from your backend later.
const posts = [
  { user: "Mia",   icon: "🎓", text: "completed an assignment (+25 XP)", time: "10 min ago" },
  { user: "Jonas", icon: "🎉", text: "reached Level 3",                  time: "1 h ago" },
  { user: "Ali",   icon: "🔥", text: "is on a 5 day streak",             time: "3 h ago" },
  { user: "Lena",  icon: "👑", text: "unlocked the Legend skin",         time: "Yesterday" },
];

// Escape text so nobody can inject HTML into the page (matters once posts come from users)
function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

document.getElementById("feed-list").innerHTML = posts.map((post) => `
  <li>
    ${post.icon} <strong>${escapeHtml(post.user)}</strong> ${escapeHtml(post.text)}<br>
    <small>${post.time}</small>
  </li>
`).join("");
