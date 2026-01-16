const API = "http://127.0.0.1:8000"

let forced = []
let banned = []
let emblems = {}

const forcedList = document.getElementById("forcedList")
const bannedList = document.getElementById("bannedList")
const emblemsDiv = document.getElementById("emblems")
const resultBody = document.getElementById("result")

// ===== DEFAULT =====
fetch(API + "/config/defaults")
  .then(r => r.json())
  .then(d => {
    forced = d.forced
    banned = d.banned
    renderForced()
    renderBanned()
  })

// ===== TRAITS =====
fetch(API + "/data/traits")
  .then(r => r.json())
  .then(traits => {
    traits.forEach(trait => {
      const row = document.createElement("div")
      row.className = "emblem-row"

      const label = document.createElement("span")
      label.textContent = trait

      const input = document.createElement("input")
      input.type = "number"
      input.min = 0
      input.max = 5
      input.value = 0

      input.onchange = () => {
        const v = parseInt(input.value)
        if (v > 0) emblems[trait] = v
        else delete emblems[trait]
      }

      row.appendChild(label)
      row.appendChild(input)
      emblemsDiv.appendChild(row)
    })
  })

// ===== FORCED / BANNED =====
function addForced() {
  const v = forcedInput.value.trim()
  if (v && !forced.includes(v)) forced.push(v)
  forcedInput.value = ""
  renderForced()
}

function addBanned() {
  const v = bannedInput.value.trim()
  if (v && !banned.includes(v)) banned.push(v)
  bannedInput.value = ""
  renderBanned()
}

function renderForced() {
  forcedList.innerHTML = ""
  forced.forEach((c, i) => {
    const li = document.createElement("li")
    li.textContent = c
    li.onclick = () => {
      forced.splice(i, 1)
      renderForced()
    }
    forcedList.appendChild(li)
  })
}

function renderBanned() {
  bannedList.innerHTML = ""
  banned.forEach((c, i) => {
    const li = document.createElement("li")
    li.textContent = c
    li.onclick = () => {
      banned.splice(i, 1)
      renderBanned()
    }
    bannedList.appendChild(li)
  })
}

// ===== SOLVE =====
function runSolver() {
  fetch(`${API}/solve/${solver.value}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      max_team: +maxTeam.value,
      time_limit: +timeLimit.value,
      forced,
      banned,
      emblems
    })
  })
    .then(r => r.json())
    .then(showResult)
}

// ===== RESULT =====
function showResult(data) {
  resultBody.innerHTML = ""
  data.forEach(t => {
    const tr = document.createElement("tr")
    tr.innerHTML = `
      <td>${t.team.join(", ")}</td>
      <td>${t.score}</td>
      <td>${t.team.length}</td>
    `
    resultBody.appendChild(tr)
  })
}
