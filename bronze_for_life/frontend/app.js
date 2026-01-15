const solveBtn = document.getElementById("solveBtn");
const resultDiv = document.getElementById("result");
const loadingDiv = document.getElementById("loading");

solveBtn.onclick = async () => {
    const solver = document.getElementById("solver").value;
    const maxTeam = parseInt(document.getElementById("maxTeam").value);
    const timeLimit = parseFloat(document.getElementById("timeLimit").value);

    const forced = document
        .getElementById("forced")
        .value.split(",")
        .map(s => s.trim())
        .filter(Boolean);

    const banned = document
        .getElementById("banned")
        .value.split(",")
        .map(s => s.trim())
        .filter(Boolean);

    const payload = {
        max_team: maxTeam,
        time_limit: timeLimit,
        forced: forced,
        banned: banned,
        emblems: {}
    };

    resultDiv.innerHTML = "";
    loadingDiv.classList.remove("hidden");

    try {
        const res = await fetch(`/solve/${solver}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        const data = await res.json();
        renderResult(data);
    } catch (err) {
        resultDiv.innerHTML = `<p class="error">Error: ${err}</p>`;
    } finally {
        loadingDiv.classList.add("hidden");
    }
};

function renderResult(teams) {
    if (!teams || teams.length === 0) {
        resultDiv.innerHTML = "<p>No result</p>";
        return;
    }

    teams.forEach((t, idx) => {
        const div = document.createElement("div");
        div.className = "team";

        div.innerHTML = `
            <h3>#${idx + 1} | Score: ${t.score} | Cost: ${t.total_cost}</h3>
            <div class="champions">
                ${t.team.map(c => `
                    <div class="champ">
                        <strong>${c.name}</strong>
                        <span>Cost: ${c.cost}</span>
                        <span>${c.traits.join(", ")}</span>
                    </div>
                `).join("")}
            </div>
        `;

        resultDiv.appendChild(div);
    });
}
