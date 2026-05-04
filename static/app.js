const state = {
  run: null,
  selectedCandidateId: null,
};

function lines(value) {
  return value
    .split(/\r?\n/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function scoreClass(score) {
  if (score >= 90) return "score-strong";
  if (score >= 75) return "score-good";
  if (score >= 50) return "score-review";
  return "score-weak";
}

function redirectToLogin(payload) {
  const next = encodeURIComponent(window.location.pathname + window.location.search);
  const base = payload?.login_url || "/login";
  window.location.href = `${base}?next=${next}`;
}


function renderCandidateDetails(candidate) {
  const container = document.getElementById("candidate-details");
  if (!candidate) {
    container.className = "details-empty";
    container.textContent = "No candidate selected.";
    return;
  }

  const reasons = candidate.analysis.reasons.map((item) => `<li>${item}</li>`).join("");
  const risks = candidate.analysis.risks.map((item) => `<li>${item}</li>`).join("");

  container.className = "details-card";
  container.innerHTML = `
    <div class="candidate-hero">
      <div>
        <h3>${candidate.name}</h3>
        <p>${candidate.role || "Profile result"}, ${candidate.location || "Unknown location"}</p>
      </div>
      <div class="score-badge ${scoreClass(candidate.score)}">${candidate.score}%</div>
    </div>
    <div class="detail-block">
      <h4>Candidate Summary</h4>
      <p>${candidate.analysis.summary}</p>
    </div>
    <div class="detail-block">
      <h4>Why this candidate?</h4>
      <ul>${reasons}</ul>
    </div>
    <div class="detail-block">
      <h4>What to check</h4>
      <ul>${risks}</ul>
    </div>
    <div class="detail-block">
      <h4>Suggested Outreach Message</h4>
      <p>${candidate.analysis.outreach}</p>
    </div>
    <div class="detail-block">
      <h4>Profile</h4>
      <p><a href="${candidate.profile_url}" target="_blank" rel="noreferrer">Open source profile</a></p>
      <p>${candidate.short_description || "No indexed description available."}</p>
    </div>
  `;
}

function selectCandidate(candidateId) {
  state.selectedCandidateId = candidateId;
  const candidate = state.run?.candidates.find((item) => item.id === candidateId);
  renderCandidateDetails(candidate);
  document.querySelectorAll(".results-row").forEach((row) => {
    row.classList.toggle("selected", row.dataset.id === candidateId);
  });
}

function renderResults(run) {
  state.run = run;
  const meta = document.getElementById("results-meta");
  meta.textContent = `${run.candidates.length} candidates · ${run.queries_count} queries · ${run.duration_seconds}s`;

  const empty = document.getElementById("results-state");
  const wrapper = document.getElementById("results-table-wrapper");
  const body = document.getElementById("results-body");
  body.innerHTML = "";

  if (!run.candidates.length) {
    empty.classList.remove("hidden");
    wrapper.classList.add("hidden");
    empty.textContent = "No candidates found for this search.";
    renderCandidateDetails(null);
    return;
  }

  empty.classList.add("hidden");
  wrapper.classList.remove("hidden");

  run.candidates.forEach((candidate) => {
    const row = document.createElement("tr");
    row.className = "results-row";
    row.dataset.id = candidate.id;
    row.innerHTML = `
      <td><span class="score-pill ${scoreClass(candidate.score)}">${candidate.score}%</span></td>
      <td>${candidate.name}</td>
      <td>${candidate.role || "-"}</td>
      <td>${candidate.location || "-"}</td>
      <td>${candidate.stack || "-"}</td>
      <td>${candidate.source}</td>
      <td>${candidate.status}</td>
    `;
    row.addEventListener("click", () => selectCandidate(candidate.id));
    body.appendChild(row);
  });

  selectCandidate(run.candidates[0].id);
}

function renderHistory(items) {
  const container = document.getElementById("search-history");
  container.innerHTML = "";
  if (!items.length) {
    container.innerHTML = `<div class="history-empty">No saved searches yet.</div>`;
    return;
  }

  items.forEach((item) => {
    const node = document.createElement("button");
    node.className = "history-item";
    node.innerHTML = `
      <strong>${item.role || "Untitled search"}</strong>
      <span>${item.candidate_count} candidates · ${item.strong_matches} strong</span>
    `;
    node.addEventListener("click", async () => {
  const response = await fetch(`/api/searches/${item.id}`);
  const run = await response.json();
  if (response.status === 401) {
    redirectToLogin(run);
    return;
  }
  renderResults(run);
});
    container.appendChild(node);
  });
}

async function loadHistory() {
  const response = await fetch("/api/searches");
  const items = await response.json();
  if (response.status === 401) {
    redirectToLogin(items);
    return;
  }
  renderHistory(items);
}

}

async function handleSearch(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const button = document.getElementById("search-button");
  button.disabled = true;
  button.textContent = "Searching...";

  const data = {
    role: form.role.value.trim(),
    titles: lines(form.titles.value),
    tech_groups: lines(form.tech_groups.value),
    locations: lines(form.locations.value),
    experience: form.experience.value,
    availability: form.availability.value,
    num: Number(form.num.value),
    sources: Array.from(form.querySelectorAll('input[name="sources"]:checked')).map((input) => input.value),
  };

  try {
    const response = await fetch("/api/search", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    const payload = await response.json();
if (response.status === 401) {
  redirectToLogin(payload);
  return;
}
if (!response.ok) {
  throw new Error(payload.error || "Search failed");
}

    renderResults(payload);
    await loadHistory();
  } catch (error) {
    alert(error.message);
  } finally {
    button.disabled = false;
    button.textContent = "Run Search";
  }
}

document.getElementById("search-form").addEventListener("submit", handleSearch);
loadHistory();
