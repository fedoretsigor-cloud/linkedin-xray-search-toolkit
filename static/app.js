const state = {
  run: null,
  selectedCandidateId: null,
};

const TAB_ACCESS_KEY = "engineerSearchTabAccess";

function lines(value) {
  return value
    .split(/\r?\n/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function hasCyrillic(value) {
  return /[?-??-?????????]/.test(value || "");
}

function validateEnglishOnly(data) {
  const fields = [
    data.role,
    ...data.titles,
    ...data.tech_groups,
    ...data.locations,
    data.experience,
    data.availability,
  ];

  return !fields.some(hasCyrillic);
}

function getExpectedQueryPasses(resultLimit) {
  const limit = Number(resultLimit) || 20;
  if (limit <= 20) return 1;
  if (limit <= 40) return 2;
  if (limit <= 60) return 3;
  if (limit <= 100) return 5;
  return 10;
}
function scoreClass(score) {
  if (score >= 90) return "score-strong";
  if (score >= 75) return "score-good";
  if (score >= 50) return "score-review";
  return "score-weak";
}

function formatTitleCaseValue(value) {
  if (!value) return "-";
  const text = String(value).trim();
  if (!text) return "-";
  return text.charAt(0).toUpperCase() + text.slice(1);
}

function redirectToLogin(payload) {
  const next = encodeURIComponent(window.location.pathname + window.location.search);
  const base = payload?.login_url || "/login";
  window.location.href = `${base}?next=${next}`;
}

function setFormMessage(message) {
  const node = document.getElementById("search-form-error");
  if (!node) return;
  if (!message) {
    node.textContent = "";
    node.classList.add("hidden");
    return;
  }
  node.textContent = message;
  node.classList.remove("hidden");
}

function getProgressElements() {
  return {
    card: document.getElementById("search-progress"),
    title: document.getElementById("search-progress-title"),
    copy: document.getElementById("search-progress-copy"),
    percent: document.getElementById("search-progress-percent"),
    bar: document.getElementById("search-progress-bar"),
    steps: Array.from(document.querySelectorAll(".progress-step")),
    empty: document.getElementById("results-state"),
    table: document.getElementById("results-table-wrapper"),
    meta: document.getElementById("results-meta"),
  };
}

function paintProgress(percent, title, copy) {
  const ui = getProgressElements();
  if (!ui.card) return;
  const safePercent = Math.max(0, Math.min(100, Math.round(percent)));
  ui.card.classList.remove("hidden");
  ui.empty.classList.add("hidden");
  ui.table.classList.add("hidden");
  ui.meta.textContent = "Search in progress...";
  ui.title.textContent = title;
  ui.copy.textContent = copy;
  ui.percent.textContent = `${safePercent}%`;
  ui.bar.style.width = `${safePercent}%`;

  ui.steps.forEach((step, index) => {
    const stepNumber = index + 1;
    step.classList.toggle("is-active", safePercent >= (stepNumber - 1) * 25 && safePercent < stepNumber * 25);
    step.classList.toggle("is-complete", safePercent >= stepNumber * 25);
  });
}

function hideProgressCard() {
  const ui = getProgressElements();
  if (!ui.card) return;
  ui.card.classList.add("hidden");
  ui.bar.style.width = "0%";
  ui.percent.textContent = "0%";
  ui.steps.forEach((step) => {
    step.classList.remove("is-active", "is-complete");
  });
  if (ui.steps[0]) {
    ui.steps[0].classList.add("is-active");
  }
}

function startSearchProgress(data) {
  const sourceCount = Math.max(data.sources.length, 1);
  const expectedSteps = getExpectedQueryPasses(data.num);
  const expectedDuration = Math.max(9000, 4500 + expectedSteps * 2800 + sourceCount * 1200);
  const startedAt = Date.now();
  const minimumVisibleMs = 1600;

  const phases = [
    { until: 15, title: "Validating search input", copy: "Checking fields, normalizing keywords, and preparing your request." },
    { until: 35, title: "Building query set", copy: `Preparing up to ${expectedSteps} search passes across ${sourceCount} selected source${sourceCount > 1 ? "s" : ""}.` },
    { until: 82, title: "Searching public sources", copy: "Scanning public profiles, merging candidate lists, and removing duplicates." },
    { until: 96, title: "Ranking candidates", copy: "Ranking the strongest matches and preparing the shortlist for review." },
  ];

  paintProgress(4, phases[0].title, phases[0].copy);

  const timer = window.setInterval(() => {
    const elapsed = Date.now() - startedAt;
    const ratio = Math.min(elapsed / expectedDuration, 0.94);
    const percent = 4 + ratio * 90;
    const phase = phases.find((item) => percent <= item.until) || phases[phases.length - 1];
    paintProgress(percent, phase.title, phase.copy);
  }, 220);

  return {
    finish(message = "Finalizing results") {
      window.clearInterval(timer);
      paintProgress(100, message, "Search complete. Loading the final candidate list.");
      const remaining = Math.max(700, minimumVisibleMs - (Date.now() - startedAt));
      window.setTimeout(() => hideProgressCard(), remaining);
    },
    fail(message = "Search stopped") {
      window.clearInterval(timer);
      paintProgress(100, message, "The request was interrupted before results were returned.");
      const remaining = Math.max(1200, minimumVisibleMs - (Date.now() - startedAt));
      window.setTimeout(() => hideProgressCard(), remaining);
    },
  };
}

function enforceTabAccess() {
  if (sessionStorage.getItem(TAB_ACCESS_KEY) === "1") {
    return true;
  }

  fetch("/logout", { method: "POST" })
    .catch(() => null)
    .finally(() => {
      redirectToLogin({ login_url: "/login" });
    });

  return false;
}

function renderCandidateDetails(candidate) {
  const container = document.getElementById("candidate-details");
  if (!candidate) {
    container.className = "details-empty";
    container.textContent = "No candidate selected.";
    return;
  }

  const reasons = candidate.analysis.reasons.map((item) => `<li>${item}</li>`).join("");

  container.className = "details-card";
  container.innerHTML = `
    <div class="candidate-hero">
      <div>
        <h3>${candidate.name}</h3>
        <p>${formatTitleCaseValue(candidate.role || "Profile result")}, ${formatTitleCaseValue(candidate.location || "Unknown location")}</p>
      </div>
      <div class="score-badge ${scoreClass(candidate.score)}">${candidate.score}%</div>
    </div>
    <div class="detail-block">
      <h4>Candidate Summary</h4>
      <p>${candidate.analysis.summary}</p>
    </div>
    <div class="detail-block">
      <h4>Profile</h4>
      <p><a href="${candidate.profile_url}" target="_blank" rel="noreferrer">Open source profile</a></p>
      <p>${candidate.short_description || "No indexed description available."}</p>
    </div>
    <div class="detail-block">
      <h4>Suggested Outreach Message</h4>
      <p>${candidate.analysis.outreach}</p>
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
      <td>${formatTitleCaseValue(candidate.role)}</td>
      <td>${formatTitleCaseValue(candidate.location)}</td>
      <td>${candidate.stack || "-"}</td>
      <td>${formatTitleCaseValue(candidate.source)}</td>
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

async function handleSearch(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const button = document.getElementById("search-button");
  button.disabled = true;
  button.classList.add("is-loading");
  button.textContent = "Searching...";
  setFormMessage("");

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

  const progress = startSearchProgress(data);

  if (!validateEnglishOnly(data)) {
    progress.fail("Input needs attention");
    setFormMessage("Please use English only.");
    button.disabled = false;
    button.classList.remove("is-loading");
    button.textContent = "Run Search";
    return;
  }

  try {
    const response = await fetch("/api/search", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    const payload = await response.json();
    if (response.status === 401) {
      progress.fail("Authentication required");
      redirectToLogin(payload);
      return;
    }
    if (!response.ok) {
      throw new Error(payload.error || "Search failed");
    }

    progress.finish();
    renderResults(payload);
    await loadHistory();
  } catch (error) {
    progress.fail("Search failed");
    setFormMessage(error.message || "Search failed.");
  } finally {
    button.disabled = false;
    button.classList.remove("is-loading");
    button.textContent = "Run Search";
  }
}

const searchForm = document.getElementById("search-form");
const searchButton = document.getElementById("search-button");
const logoutForm = document.querySelector('form[action="/logout"]');

if (logoutForm) {
  logoutForm.addEventListener("submit", () => {
    sessionStorage.removeItem(TAB_ACCESS_KEY);
  });
}

if (enforceTabAccess()) {
  searchForm.addEventListener("submit", handleSearch);
  searchButton.addEventListener("click", () => {
    searchForm.requestSubmit();
  });

  loadHistory();
}









