// USER PROFILE
// Mock data: replace this object with data from your backend later.
const profile = {
  name: "You",
  team: "Study Squad",
  avatar: "🧙",
  xp: 245,
  tasksDone: 18,
  streak: 4,
  badges: 3,
};

const XP_PER_LEVEL = 100; // every 100 XP = 1 level

const level = Math.floor(profile.xp / XP_PER_LEVEL) + 1;
const xpInLevel = profile.xp % XP_PER_LEVEL;

// Put the data into the elements from profile.html (matched by id)
document.getElementById("avatar").textContent = profile.avatar;
document.getElementById("name").textContent = profile.name;
document.getElementById("team").textContent = "Team: " + profile.team;
document.getElementById("level").textContent = "Level " + level;
document.getElementById("xp-fill").style.width = xpInLevel + "%";
document.getElementById("xp-text").textContent = `${xpInLevel} / ${XP_PER_LEVEL} XP to next level`;
document.getElementById("tasks").textContent = profile.tasksDone;
document.getElementById("streak").textContent = profile.streak;
document.getElementById("badges").textContent = profile.badges;
