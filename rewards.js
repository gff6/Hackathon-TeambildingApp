// REWARD PROFILE
// Mock data: the user's level and the list of skins.
const userLevel = 3;
let equippedId = "default";

const skins = [
  { id: "default", name: "Rookie", icon: "🙂", level: 1 },
  { id: "knight",  name: "Knight", icon: "🛡️", level: 2 },
  { id: "wizard",  name: "Wizard", icon: "🧙", level: 3 },
  { id: "dragon",  name: "Dragon", icon: "🐉", level: 5 },
  { id: "legend",  name: "Legend", icon: "👑", level: 8 },
  { id: "darklord", name: "Dark Lord", icon "😈", level 10},
];

// Draws every skin card. Call it again whenever the data changes.
function renderSkins() {
  const grid = document.getElementById("skin-grid");

  grid.innerHTML = skins.map((skin) => {
    const locked = userLevel < skin.level;
    const equipped = skin.id === equippedId;

    let status = "Unlocked";
    if (locked) status = "🔒 Level " + skin.level;
    if (equipped) status = "Equipped";

    return `
      <div class="card skin ${locked ? "locked" : ""} ${equipped ? "equipped" : ""}">
        <div class="icon">${skin.icon}</div>
        <strong>${skin.name}</strong>
        <p class="muted">${status}</p>
        ${locked || equipped ? "" : `<button data-skin="${skin.id}">Equip</button>`}
      </div>`;
  }).join("");
}

// One click listener on the grid handles every Equip button
document.getElementById("skin-grid").addEventListener("click", (event) => {
  if (event.target.dataset.skin) {
    equippedId = event.target.dataset.skin;
    renderSkins();
  }
});

renderSkins();
