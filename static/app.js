const state = {
  run: null,
  selectedCandidateId: null,
  roleVariants: [],
  requirementBrief: null,
  requirementSourceUrl: "",
  confirmedBrief: null,
  strategyPreview: null,
  currentProjectId: "",
  profileReviews: {},
  resumeReviews: {},
};

const TAB_ACCESS_KEY = "engineerSearchTabAccess";
const TAB_BOOTSTRAP_KEY = "engineerSearchTabBootstrap";
const SEARCH_INTENT_TERMS = [
  ["robot framework", "Robot Framework", "language"],
  ["python", "Python", "language"],
  ["pytest", "pytest", "language"],
  ["automotive", "automotive", "domain"],
  ["embedded", "embedded", "domain"],
  ["multi-ecu", "multi-ECU", "domain"],
  ["multi ecu", "multi-ECU", "domain"],
  ["ecu", "ECU", "domain"],
  ["adas", "ADAS", "domain"],
  ["hil", "HiL", "domain"],
  ["hardware-in-the-loop", "HiL", "domain"],
  ["sil", "SIL", "domain"],
  ["software-in-the-loop", "SIL", "domain"],
  ["can", "CAN", "domain"],
  ["lin", "LIN", "domain"],
  ["ethernet", "Ethernet", "domain"],
  ["git", "Git", "tooling"],
  ["jfrog", "JFrog", "tooling"],
  ["artifactory", "Artifactory", "tooling"],
  ["virtual environment", "virtual environments", "tooling"],
  ["virtual environments", "virtual environments", "tooling"],
  ["log analysis", "log analysis", "tooling"],
  ["analyze logs", "log analysis", "tooling"],
  ["logs", "logs", "tooling"],
  ["bdd", "BDD", "methodology"],
  ["gherkin", "Gherkin", "methodology"],
  ["keyword-driven", "keyword-driven testing", "methodology"],
  ["selenium", "Selenium", "language"],
  ["cypress", "Cypress", "language"],
  ["playwright", "Playwright", "language"],
  ["puppeteer", "Puppeteer", "language"],
  ["typescript", "TypeScript", "language"],
  ["javascript", "JavaScript", "language"],
  ["java", "Java", "language"],
  ["spring boot", "Spring Boot", "tooling"],
  ["spring", "Spring", "tooling"],
  ["kafka", "Kafka", "tooling"],
  ["aws", "AWS", "tooling"],
];

const GENERIC_SEARCH_PHRASES = new Set([
  "ability",
  "ability to",
  "experience",
  "experience with",
  "proven experience",
  "proven experience developing",
  "strong communication skills",
  "technical documentation",
  "requirements",
  "development",
  "testing",
]);

function lines(value) {
  return value
    .split(/\r?\n/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function hasCyrillic(value) {
  return /[\u0400-\u04FF]/.test(value || "");
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

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function renderList(items, emptyText) {
  const values = Array.isArray(items) ? items.filter(Boolean) : [];
  if (!values.length) {
    return `<li>${escapeHtml(emptyText)}</li>`;
  }
  return values.map((item) => `<li>${escapeHtml(item)}</li>`).join("");
}

function renderPlainList(items, emptyText) {
  return `<ul>${renderList(items, emptyText)}</ul>`;
}

async function readJsonResponse(response) {
  const text = await response.text();
  if (!text) return {};
  try {
    return JSON.parse(text);
  } catch {
    const clean = text.replace(/<[^>]*>/g, " ").replace(/\s+/g, " ").trim();
    return {
      error: clean || `Server returned a non-JSON response (${response.status})`,
    };
  }
}

function normalizeVariant(value) {
  return String(value || "").trim().replace(/\s+/g, " ");
}

function setRoleVariants(values) {
  const seen = new Set();
  state.roleVariants = [];
  values.forEach((value) => {
    const variant = normalizeVariant(value);
    const key = variant.toLowerCase();
    if (!variant || seen.has(key)) return;
    seen.add(key);
    state.roleVariants.push(variant);
  });
  renderRoleVariants();
}

function addRoleVariant(value) {
  setRoleVariants([...state.roleVariants, value]);
}

function removeRoleVariant(value) {
  const target = normalizeVariant(value).toLowerCase();
  setRoleVariants(state.roleVariants.filter((item) => item.toLowerCase() !== target));
}

function syncRoleVariantsField() {
  const field = document.getElementById("role-variants-hidden");
  if (!field) return;
  field.value = state.roleVariants.join("\n");
}

function renderRoleVariants() {
  const container = document.getElementById("role-variant-chips");
  if (!container) return;
  syncRoleVariantsField();

  if (!state.roleVariants.length) {
    container.innerHTML = `<span class="variant-empty">No variants yet. Presets or manual additions will appear here.</span>`;
    return;
  }

  container.innerHTML = state.roleVariants
    .map(
      (variant) => `
        <span class="variant-chip">
          ${escapeHtml(variant)}
          <button type="button" aria-label="Remove ${escapeHtml(variant)}" data-variant="${escapeHtml(variant)}">x</button>
        </span>
      `,
    )
    .join("");

  container.querySelectorAll("button[data-variant]").forEach((button) => {
    button.addEventListener("click", () => removeRoleVariant(button.dataset.variant));
  });
}

function getRolePresetGroups() {
  return Array.isArray(window.ROLE_PRESETS) ? window.ROLE_PRESETS : [];
}

function findPreset(groupName, presetName) {
  const group = getRolePresetGroups().find((item) => item.group === groupName);
  if (!group) return null;
  return group.presets.find((preset) => preset.name === presetName) || null;
}

function populateRoleGroups() {
  const groupSelect = document.getElementById("role-group-select");
  if (!groupSelect) return;
  getRolePresetGroups().forEach((group) => {
    const option = document.createElement("option");
    option.value = group.group;
    option.textContent = group.group;
    groupSelect.appendChild(option);
  });
}

function populateRolePresets(groupName) {
  const presetSelect = document.getElementById("role-preset-select");
  if (!presetSelect) return;
  presetSelect.innerHTML = "";

  const group = getRolePresetGroups().find((item) => item.group === groupName);
  if (!group) {
    presetSelect.disabled = true;
    presetSelect.appendChild(new Option("Select group first", ""));
    return;
  }

  presetSelect.disabled = false;
  presetSelect.appendChild(new Option("Choose a role preset", ""));
  group.presets.forEach((preset) => {
    presetSelect.appendChild(new Option(preset.name, preset.name));
  });
}

function applyRolePreset(preset) {
  const form = document.getElementById("search-form");
  if (!form || !preset) return;
  form.role.value = preset.role || "";
  setRoleVariants(preset.variants || []);
  if (preset.stacks?.length) {
    form.tech_groups.value = preset.stacks.join("\n");
  }
}

function initializeRolePresets() {
  const groupSelect = document.getElementById("role-group-select");
  const presetSelect = document.getElementById("role-preset-select");
  const addButton = document.getElementById("add-role-variant");
  const variantInput = document.getElementById("role-variant-input");

  populateRoleGroups();
  populateRolePresets("");
  renderRoleVariants();

  groupSelect?.addEventListener("change", () => {
    populateRolePresets(groupSelect.value);
  });

  presetSelect?.addEventListener("change", () => {
    const preset = findPreset(groupSelect.value, presetSelect.value);
    if (preset) applyRolePreset(preset);
  });

  addButton?.addEventListener("click", () => {
    addRoleVariant(variantInput.value);
    variantInput.value = "";
    variantInput.focus();
  });

  variantInput?.addEventListener("keydown", (event) => {
    if (event.key !== "Enter") return;
    event.preventDefault();
    addRoleVariant(variantInput.value);
    variantInput.value = "";
  });
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
  const activeWaitMessages = [
    "Still working. Some public sources answer more slowly than others.",
    "Search is still running. Keeping the page open is enough.",
    "Gathering and cleaning results before ranking the shortlist.",
    "Still alive. Larger query sets can take a little longer.",
    "Almost there. We are waiting for the final search responses.",
  ];

  const phases = [
    { until: 15, title: "Validating search input", copy: "Checking fields, normalizing keywords, and preparing your request." },
    { until: 35, title: "Building query set", copy: `Preparing up to ${expectedSteps} search passes across ${sourceCount} selected source${sourceCount > 1 ? "s" : ""}.` },
    { until: 72, title: "Searching public sources", copy: "Scanning public profiles, merging candidate lists, and removing duplicates." },
    { until: 87, title: "Ranking candidates", copy: "Ranking the strongest matches and preparing the shortlist for review." },
  ];

  paintProgress(4, phases[0].title, phases[0].copy);

  const timer = window.setInterval(() => {
    const elapsed = Date.now() - startedAt;
    const ratio = Math.min(elapsed / expectedDuration, 1);
    const percent = Math.min(87, 4 + ratio * 83);
    const phase = phases.find((item) => percent <= item.until) || phases[phases.length - 1];
    let copy = phase.copy;
    if (elapsed > 10000) {
      const waitIndex = Math.floor((elapsed - 10000) / 4500) % activeWaitMessages.length;
      copy = activeWaitMessages[waitIndex];
    }
    if (elapsed > 25000) {
      copy = "This is a larger search, and it can take 30-60 seconds. The search is still running.";
    }
    paintProgress(percent, phase.title, copy);
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

  const bootstrapToken = localStorage.getItem(TAB_BOOTSTRAP_KEY);
  if (bootstrapToken) {
    sessionStorage.setItem(TAB_ACCESS_KEY, "1");
    localStorage.removeItem(TAB_BOOTSTRAP_KEY);
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

  const analysis = candidate.analysis || {};
  const savedReview = getSavedProfileReview(candidate);
  const review = savedReview?.analysis;
  const savedResumeReview = getSavedResumeReview(candidate);
  const resumeReview = savedResumeReview?.analysis;

  container.className = "details-card";
  container.innerHTML = `
    <div class="candidate-hero">
      <div>
        <h3>${escapeHtml(candidate.name)}</h3>
        <p>${escapeHtml(formatTitleCaseValue(candidate.role || "Profile result"))}, ${escapeHtml(formatTitleCaseValue(candidate.location || "Unknown location"))}</p>
      </div>
      <div class="score-badge ${scoreClass(candidate.score)}">${candidate.score}%</div>
    </div>
    <div class="detail-block">
      <h4>Profile</h4>
      <p><a href="${escapeHtml(candidate.profile_url)}" target="_blank" rel="noreferrer">Open source profile</a></p>
      <p>${escapeHtml(candidate.short_description || "No indexed description available.")}</p>
    </div>
    <div class="detail-block">
      <h4>Suggested Outreach Message</h4>
      <p>${escapeHtml(analysis.outreach || "No outreach draft available.")}</p>
    </div>
    <div class="detail-block manual-review-block">
      <h4>Manual Profile Review</h4>
      <p class="field-note">Open the profile yourself, paste relevant text here, and let the agent compare it with the confirmed brief.</p>
      <textarea id="profile-review-text" rows="8" placeholder="Paste LinkedIn/profile text here..."></textarea>
      <button type="button" class="primary-btn compact-action-btn" id="analyze-profile-button">Analyze Profile</button>
      <div id="profile-review-message" class="form-message hidden" role="alert"></div>
      ${savedReview ? `<p class="field-note">Saved review: ${escapeHtml(savedReview.created_at || "saved in project")}</p>` : ""}
      <div id="profile-review-result" class="profile-review-result ${review ? "" : "hidden"}">
        ${review ? renderProfileReview(review) : ""}
      </div>
    </div>
    <div class="detail-block manual-review-block">
      <h4>Resume Review</h4>
      <p class="field-note">Upload a PDF/DOCX resume or paste text. The agent compares it with the confirmed brief and profile review.</p>
      <input id="resume-review-file" type="file" accept=".pdf,.docx,.txt,.md,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document">
      <textarea id="resume-review-text" rows="7" placeholder="Optional fallback: paste resume text here..."></textarea>
      <button type="button" class="primary-btn compact-action-btn" id="analyze-resume-button">Analyze Resume</button>
      <div id="resume-review-message" class="form-message hidden" role="alert"></div>
      ${savedResumeReview ? `<p class="field-note">Saved resume review: ${escapeHtml(savedResumeReview.created_at || "saved in project")}</p>` : ""}
      <div id="resume-review-result" class="profile-review-result ${resumeReview ? "" : "hidden"}">
        ${resumeReview ? renderResumeReview(resumeReview) : ""}
      </div>
    </div>
  `;

  document.getElementById("analyze-profile-button")?.addEventListener("click", () => handleProfileReview(candidate));
  document.getElementById("analyze-resume-button")?.addEventListener("click", () => handleResumeReview(candidate));
}

function profileReviewKeysForCandidate(candidate) {
  return [candidate?.profile_url, candidate?.id].filter(Boolean);
}

function getSavedProfileReview(candidate) {
  for (const key of profileReviewKeysForCandidate(candidate)) {
    if (state.profileReviews[key]) {
      return state.profileReviews[key];
    }
  }
  return null;
}

function rememberProfileReview(review, candidate = null) {
  const keys = [
    review?.candidate_url,
    review?.candidate_id,
    ...profileReviewKeysForCandidate(candidate),
  ].filter(Boolean);

  keys.forEach((key) => {
    state.profileReviews[key] = review;
  });
}

function getSavedResumeReview(candidate) {
  for (const key of profileReviewKeysForCandidate(candidate)) {
    if (state.resumeReviews[key]) {
      return state.resumeReviews[key];
    }
  }
  return null;
}

function rememberResumeReview(review, candidate = null) {
  const keys = [
    review?.candidate_url,
    review?.candidate_id,
    ...profileReviewKeysForCandidate(candidate),
  ].filter(Boolean);

  keys.forEach((key) => {
    state.resumeReviews[key] = review;
  });
}

function renderProfileReview(review) {
  return `
    <div class="requirement-brief-header">
      <strong>${escapeHtml(formatDecision(review.decision))}</strong>
      <span>${escapeHtml(String(review.score || 0))}%</span>
    </div>
    <p>${escapeHtml(review.summary || "No summary returned.")}</p>
    <div class="brief-section">
      <h4>Evidence</h4>
      ${renderPlainList(review.evidence, "No clear evidence found.")}
    </div>
    <div class="brief-section">
      <h4>Risks</h4>
      ${renderPlainList(review.risks, "No major risks found.")}
    </div>
    <div class="brief-section">
      <h4>Questions to ask</h4>
      ${renderPlainList(review.questions_to_ask, "No questions suggested.")}
    </div>
    <div class="brief-section">
      <h4>Outreach draft</h4>
      <p>${escapeHtml(review.outreach_message || "No outreach draft returned.")}</p>
    </div>
  `;
}

function renderResumeReview(review) {
  return `
    <div class="requirement-brief-header">
      <strong>${escapeHtml(formatDecision(review.decision))}</strong>
      <span>${escapeHtml(String(review.score || 0))}%</span>
    </div>
    <p>${escapeHtml(review.summary || "No summary returned.")}</p>
    <div class="brief-section">
      <h4>Resume evidence</h4>
      ${renderPlainList(review.resume_evidence, "No resume evidence found.")}
    </div>
    <div class="brief-section">
      <h4>Profile alignment</h4>
      ${renderPlainList(review.profile_alignment, "No profile alignment found.")}
    </div>
    <div class="brief-section">
      <h4>Contradictions</h4>
      ${renderPlainList(review.contradictions, "No contradictions found.")}
    </div>
    <div class="brief-section">
      <h4>Questions to ask</h4>
      ${renderPlainList(review.questions_to_ask, "No questions suggested.")}
    </div>
    <div class="brief-section">
      <h4>Recommended next action</h4>
      <p>${escapeHtml(review.recommended_next_action || "No next action returned.")}</p>
    </div>
  `;
}

function formatDecision(value) {
  return String(value || "unclear").replaceAll("_", " ");
}

function setProfileReviewMessage(message) {
  const node = document.getElementById("profile-review-message");
  if (!node) return;
  if (!message) {
    node.textContent = "";
    node.classList.add("hidden");
    return;
  }
  node.textContent = message;
  node.classList.remove("hidden");
}

function setResumeReviewMessage(message) {
  const node = document.getElementById("resume-review-message");
  if (!node) return;
  if (!message) {
    node.textContent = "";
    node.classList.add("hidden");
    return;
  }
  node.textContent = message;
  node.classList.remove("hidden");
}

async function handleProfileReview(candidate) {
  const textArea = document.getElementById("profile-review-text");
  const button = document.getElementById("analyze-profile-button");
  const resultNode = document.getElementById("profile-review-result");
  const profileText = textArea?.value.trim() || "";
  const projectId = state.run?.project_id || state.currentProjectId;
  setProfileReviewMessage("");

  if (!projectId) {
    setProfileReviewMessage("Run a project-linked search before reviewing candidates.");
    return;
  }
  if (profileText.length < 80) {
    setProfileReviewMessage("Paste more profile text before analysis.");
    return;
  }

  button.disabled = true;
  button.textContent = "Analyzing...";
  try {
    const response = await fetch(`/api/projects/${encodeURIComponent(projectId)}/candidate-reviews`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        candidate_id: candidate.id,
        candidate_name: candidate.name,
        candidate_url: candidate.profile_url,
        candidate,
        profile_text: profileText,
      }),
    });
    const payload = await readJsonResponse(response);
    if (response.status === 401) {
      redirectToLogin(payload);
      return;
    }
    if (!response.ok) {
      throw new Error(payload.error || "Profile review failed");
    }
    rememberProfileReview(payload, candidate);
    resultNode.classList.remove("hidden");
    resultNode.innerHTML = renderProfileReview(payload.analysis);
    setProfileReviewMessage("Profile review saved to this sourcing project.");
  } catch (error) {
    setProfileReviewMessage(error.message || "Profile review failed.");
  } finally {
    button.disabled = false;
    button.textContent = "Analyze Profile";
  }
}

async function handleResumeReview(candidate) {
  const fileInput = document.getElementById("resume-review-file");
  const textArea = document.getElementById("resume-review-text");
  const button = document.getElementById("analyze-resume-button");
  const resultNode = document.getElementById("resume-review-result");
  const resumeText = textArea?.value.trim() || "";
  const resumeFile = fileInput?.files?.[0] || null;
  const projectId = state.run?.project_id || state.currentProjectId;
  const savedProfileReview = getSavedProfileReview(candidate);
  setResumeReviewMessage("");

  if (!projectId) {
    setResumeReviewMessage("Run a project-linked search before reviewing resumes.");
    return;
  }
  if (!resumeFile && resumeText.length < 80) {
    setResumeReviewMessage("Upload a PDF/DOCX resume or paste more resume text.");
    return;
  }

  const formData = new FormData();
  formData.append("candidate_id", candidate.id);
  formData.append("candidate_name", candidate.name);
  formData.append("candidate_url", candidate.profile_url || "");
  formData.append("candidate", JSON.stringify(candidate));
  formData.append("resume_text", resumeText);
  if (savedProfileReview?.analysis) {
    formData.append("profile_review", JSON.stringify(savedProfileReview.analysis));
  }
  if (resumeFile) {
    formData.append("resume_file", resumeFile);
  }

  button.disabled = true;
  button.textContent = "Analyzing...";
  try {
    const response = await fetch(`/api/projects/${encodeURIComponent(projectId)}/resume-reviews`, {
      method: "POST",
      body: formData,
    });
    const payload = await readJsonResponse(response);
    if (response.status === 401) {
      redirectToLogin(payload);
      return;
    }
    if (!response.ok) {
      throw new Error(payload.error || "Resume review failed");
    }
    rememberResumeReview(payload, candidate);
    resultNode.classList.remove("hidden");
    resultNode.innerHTML = renderResumeReview(payload.analysis);
    setResumeReviewMessage("Resume review saved to this sourcing project.");
  } catch (error) {
    setResumeReviewMessage(error.message || "Resume review failed.");
  } finally {
    button.disabled = false;
    button.textContent = "Analyze Resume";
  }
}

async function loadProjectReviews(projectId) {
  if (!projectId) return;
  try {
    const response = await fetch(`/api/projects/${encodeURIComponent(projectId)}`);
    const project = await readJsonResponse(response);
    if (response.status === 401) {
      redirectToLogin(project);
      return;
    }
    if (!response.ok) return;
    indexProjectReviews(project);
    if (state.currentProjectId === projectId) {
      rerenderSelectedCandidate();
    }
  } catch {
    // Saved reviews are helpful, but search results should remain usable if project loading fails.
  }
}

function indexProjectReviews(project) {
  state.profileReviews = {};
  state.resumeReviews = {};
  (project.candidate_reviews || []).forEach((review) => {
    rememberProfileReview(review);
  });
  (project.resume_reviews || []).forEach((review) => {
    rememberResumeReview(review);
  });
}

function rerenderSelectedCandidate() {
  if (!state.selectedCandidateId || !state.run?.candidates?.length) return;
  const candidate = state.run.candidates.find((item) => item.id === state.selectedCandidateId);
  if (candidate) {
    renderCandidateDetails(candidate);
  }
}

function setRequirementMessage(message) {
  const node = document.getElementById("requirement-message");
  if (!node) return;
  if (!message) {
    node.textContent = "";
    node.classList.add("hidden");
    return;
  }
  node.textContent = message;
  node.classList.remove("hidden");
}

function renderRequirementBrief(result) {
  const container = document.getElementById("requirement-brief");
  if (!container) return;
  if (!result?.brief) {
    container.classList.add("hidden");
    container.innerHTML = "";
    return;
  }

  const brief = result.brief;
  state.requirementBrief = brief;
  state.requirementSourceUrl = result.source_url || document.getElementById("requirement-url")?.value.trim() || "";
  state.confirmedBrief = null;
  state.strategyPreview = null;
  state.currentProjectId = "";
  const mustHave = renderList(brief.must_have_skills, "No must-have skills extracted.");
  const niceToHave = renderList(brief.nice_to_have_skills, "No nice-to-have skills extracted.");
  const questions = renderList(brief.open_questions, "No open questions.");
  const variants = renderList(brief.role_variants, "No role variants extracted.");

  container.classList.remove("hidden");
  container.innerHTML = `
    <div class="requirement-brief-header">
      <strong>Agent understanding</strong>
      <span>${escapeHtml(brief.confidence || "low")} confidence</span>
    </div>
    <p>${escapeHtml(brief.human_summary || "I extracted a draft sourcing brief.")}</p>
    <dl class="brief-grid">
      <div><dt>Role</dt><dd>${escapeHtml(brief.role || "-")}</dd></div>
      <div><dt>Seniority</dt><dd>${escapeHtml(brief.seniority || "-")}</dd></div>
      <div><dt>Location</dt><dd>${escapeHtml(brief.location || "-")}</dd></div>
      <div><dt>Remote</dt><dd>${escapeHtml(brief.remote_policy || "-")}</dd></div>
      <div><dt>Domain</dt><dd>${escapeHtml(brief.domain || "-")}</dd></div>
    </dl>
    <div class="brief-section">
      <h4>Must-have skills</h4>
      <ul>${mustHave}</ul>
    </div>
    <div class="brief-section">
      <h4>Nice-to-have skills</h4>
      <ul>${niceToHave}</ul>
    </div>
    <div class="brief-section">
      <h4>Role variants</h4>
      <ul>${variants}</ul>
    </div>
    <div class="brief-section">
      <h4>Questions for human confirmation</h4>
      <ul>${questions}</ul>
    </div>
    <button type="button" class="primary-btn apply-brief-btn" id="apply-requirement-brief">Apply to Search Builder</button>
    <div id="search-strategy-preview" class="strategy-preview hidden"></div>
  `;

  document.getElementById("apply-requirement-brief")?.addEventListener("click", applyRequirementBrief);
}

function applyRequirementBrief() {
  const form = document.getElementById("search-form");
  const brief = state.requirementBrief;
  if (!form || !brief) return;

  const intent = buildSearchIntentFromBrief(brief);
  form.role.value = shortenSearchPhrase(brief.role || "", 80);
  setRoleVariants((brief.role_variants || []).slice(0, 4).map((item) => shortenSearchPhrase(item, 80)));
  form.tech_groups.value = intent.skill_groups.map((group) => group.join(" | ")).join("\n");
  form.locations.value = [shortenSearchPhrase(brief.location || "", 60)].filter(Boolean).join("\n");
  state.confirmedBrief = null;
  setRequirementMessage("Draft applied. Edit fields if needed. Search will use the current fields.");
  renderSearchStrategyPreview();
}

function buildConfirmedBriefFromForm() {
  const form = document.getElementById("search-form");
  syncRoleVariantsField();
  const searchIntent = buildSearchIntentFromForm(form);
  return {
    source_url: state.requirementSourceUrl,
    original_brief: state.requirementBrief,
    role: form.role.value.trim(),
    role_variants: [...state.roleVariants],
    tech_groups: lines(form.tech_groups.value),
    search_intent: searchIntent,
    locations: lines(form.locations.value),
    location_policy: "strict",
    sources: Array.from(form.querySelectorAll('input[name="sources"]:checked')).map((input) => input.value),
    results_limit: Number(form.num.value),
  };
}

function buildStrategyPreviewFromForm() {
  const form = document.getElementById("search-form");
  syncRoleVariantsField();
  const titles = [form.role.value.trim(), ...state.roleVariants].filter(Boolean).map((item) => shortenSearchPhrase(item, 80));
  const searchIntent = buildSearchIntentFromForm(form);
  const skillGroups = searchIntent.skill_groups.length
    ? searchIntent.skill_groups
    : lines(form.tech_groups.value).flatMap((group) => chunkArray(group.split("|").map((item) => shortenSearchPhrase(item, 45)).filter(Boolean), 3));
  const locations = lines(form.locations.value).map((item) => shortenSearchPhrase(item, 60));
  const sources = Array.from(form.querySelectorAll('input[name="sources"]:checked')).map((input) => input.value);
  const queryCount = Math.max(titles.length, 1) * Math.max(skillGroups.length, 1) * Math.max(locations.length, 1) * Math.max(sources.length, 1);
  const sampleQueries = [];

  titles.slice(0, 2).forEach((title) => {
    (skillGroups.length ? skillGroups : [[]]).slice(0, 2).forEach((skills) => {
      (locations.length ? locations : [""]).slice(0, 1).forEach((location) => {
        const parts = ['site:linkedin.com/in/'];
        if (title) parts.push(`"${title}"`);
        if (skills.length === 1) parts.push(`"${skills[0]}"`);
        if (skills.length > 1) parts.push(`(${skills.map((skill) => `"${skill}"`).join(" OR ")})`);
        if (location) parts.push(`"${location}"`);
        sampleQueries.push(parts.join(" "));
      });
    });
  });

  return {
    titles,
    skill_groups: skillGroups,
    search_intent: searchIntent,
    locations,
    sources,
    query_count: queryCount,
    location_policy: "strict",
    sample_queries: sampleQueries.slice(0, 4),
  };
}

function renderSearchStrategyPreview() {
  const container = document.getElementById("search-strategy-preview");
  if (!container) return;
  const strategy = buildStrategyPreviewFromForm();
  state.strategyPreview = strategy;
  container.classList.remove("hidden");
  container.innerHTML = `
    <div class="requirement-brief-header">
      <strong>Search strategy preview</strong>
      <span>${strategy.query_count} base queries</span>
    </div>
    <div class="brief-section">
      <h4>Role titles</h4>
      <ul>${renderList(strategy.titles, "No titles selected.")}</ul>
    </div>
    <div class="brief-section">
      <h4>Location policy</h4>
      <ul><li>Strict: candidates must show target location evidence in indexed text.</li></ul>
    </div>
    <div class="brief-section">
      <h4>Must-have search anchors</h4>
      <ul>${renderList(strategy.search_intent.must_have_keywords, "No must-have anchors selected.")}</ul>
    </div>
    <div class="brief-section">
      <h4>Domain keywords</h4>
      <ul>${renderList(strategy.search_intent.domain_keywords, "No domain keywords selected.")}</ul>
    </div>
    <div class="brief-section">
      <h4>Query groups</h4>
      <ul>${renderList(strategy.skill_groups.map((group) => group.join(" | ")), "No skills selected.")}</ul>
    </div>
    <div class="brief-section">
      <h4>Sample queries</h4>
      <ul>${renderList(strategy.sample_queries, "No query examples.")}</ul>
    </div>
  `;
}

function buildSearchIntentFromBrief(brief) {
  const terms = collectSearchIntentTerms([
    ...(brief.search_keywords || []),
    ...(brief.must_have_skills || []),
    ...(brief.nice_to_have_skills || []),
    brief.domain || "",
    brief.role || "",
  ]);
  return buildSearchIntentPayload({
    roleTitles: [brief.role || "", ...(brief.role_variants || [])],
    terms,
  });
}

function buildSearchIntentFromForm(form) {
  const formTerms = lines(form.tech_groups.value).flatMap((group) => group.split("|"));
  const briefTerms = state.requirementBrief
    ? collectSearchIntentTerms([
        ...(state.requirementBrief.search_keywords || []),
        ...(state.requirementBrief.must_have_skills || []),
        ...(state.requirementBrief.nice_to_have_skills || []),
        state.requirementBrief.domain || "",
      ])
    : [];
  const terms = collectSearchIntentTerms([...formTerms, ...briefTerms]);
  return buildSearchIntentPayload({
    roleTitles: [form.role.value.trim(), ...state.roleVariants],
    terms,
  });
}

function collectSearchIntentTerms(values) {
  const terms = [];
  values.forEach((value) => {
    const text = cleanSearchPhrase(value);
    if (!text) return;
    let matched = false;
    SEARCH_INTENT_TERMS.forEach(([needle, label, kind]) => {
      if (termMatches(text, needle)) {
        terms.push({ label, kind });
        matched = true;
      }
    });
    const keyword = cleanSearchKeyword(text);
    if (!matched && keyword && !GENERIC_SEARCH_PHRASES.has(keyword.toLowerCase())) {
      terms.push({ label: keyword, kind: classifySearchKeyword(keyword) });
    }
  });
  return dedupeIntentTerms(terms);
}

function termMatches(value, needle) {
  const normalizedValue = normalizeForSearchIntent(value);
  const normalizedNeedle = normalizeForSearchIntent(needle);
  const escaped = normalizedNeedle.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  return new RegExp(`(^|[^a-z0-9])${escaped}([^a-z0-9]|$)`).test(normalizedValue);
}

function normalizeForSearchIntent(value) {
  return String(value || "").toLowerCase().replace(/[/-]/g, " ").replace(/\s+/g, " ").trim();
}

function cleanSearchKeyword(value) {
  const text = cleanSearchPhrase(value);
  if (!text || text.length > 35 || text.split(/\s+/).length > 4) return "";
  return text;
}

function classifySearchKeyword(value) {
  const match = SEARCH_INTENT_TERMS.find(([needle]) => termMatches(value, needle));
  return match?.[2] || "other";
}

function dedupeIntentTerms(terms) {
  const seen = new Set();
  return terms.filter((term) => {
    const key = term.label.toLowerCase();
    if (!term.label || seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

function buildSearchIntentPayload({ roleTitles, terms }) {
  const byKind = {
    language: terms.filter((term) => term.kind === "language").map((term) => term.label),
    domain: terms.filter((term) => term.kind === "domain").map((term) => term.label),
    tooling: terms.filter((term) => term.kind === "tooling").map((term) => term.label),
    methodology: terms.filter((term) => term.kind === "methodology").map((term) => term.label),
    other: terms.filter((term) => term.kind === "other").map((term) => term.label),
  };
  const skillGroups = [
    ...chunkArray(dedupeTextValues(byKind.language).slice(0, 3), 3),
    ...chunkArray(dedupeTextValues(byKind.domain).slice(0, 4), 3),
    ...chunkArray(dedupeTextValues([...byKind.tooling, ...byKind.methodology]).slice(0, 6), 3),
  ].filter((group) => group.length);

  if (!skillGroups.length && byKind.other.length) {
    skillGroups.push(dedupeTextValues(byKind.other).slice(0, 3));
  }

  return {
    role_titles: dedupeTextValues(roleTitles).slice(0, 5),
    must_have_keywords: dedupeTextValues([...byKind.language, ...byKind.domain]),
    domain_keywords: dedupeTextValues(byKind.domain),
    tool_keywords: dedupeTextValues([...byKind.tooling, ...byKind.methodology]),
    optional_keywords: dedupeTextValues(byKind.other),
    skill_groups: skillGroups,
  };
}

function dedupeTextValues(values) {
  const seen = new Set();
  return values
    .map((value) => cleanSearchPhrase(value))
    .filter((value) => {
      const key = value.toLowerCase();
      if (!value || seen.has(key)) return false;
      seen.add(key);
      return true;
    });
}

function chunkArray(values, size) {
  const chunks = [];
  for (let index = 0; index < values.length; index += size) {
    chunks.push(values.slice(index, index + size));
  }
  return chunks;
}

function shortenSearchPhrase(value, maxLength) {
  const text = cleanSearchPhrase(value);
  if (text.length <= maxLength) return text;
  const separators = ["(", " - ", " | ", " / ", ",", ":"];
  for (const separator of separators) {
    if (text.includes(separator)) {
      const candidate = text.split(separator)[0].trim();
      if (candidate && candidate.length <= maxLength) return cleanSearchPhrase(candidate);
    }
  }
  return cleanSearchPhrase(text.slice(0, maxLength).replace(/\s+\S*$/, ""));
}

function cleanSearchPhrase(value) {
  return String(value || "").trim().replace(/\s+/g, " ").replace(/^[,;:()[\]{}\-\s]+|[,;:()[\]{}\-\s]+$/g, "");
}

async function handleRequirementAnalysis() {
  const input = document.getElementById("requirement-url");
  const button = document.getElementById("analyze-requirement-button");
  const url = input?.value.trim();
  setRequirementMessage("");

  if (!url) {
    setRequirementMessage("Please paste a public requirement URL first.");
    return;
  }

  button.disabled = true;
  button.textContent = "Analyzing...";
  renderRequirementBrief(null);

  try {
    const response = await fetch("/api/requirements/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url }),
    });
    const payload = await readJsonResponse(response);
    if (response.status === 401) {
      redirectToLogin(payload);
      return;
    }
    if (!response.ok) {
      throw new Error(payload.error || "Requirement analysis failed");
    }
    renderRequirementBrief(payload);
  } catch (error) {
    setRequirementMessage(error.message || "Requirement analysis failed.");
  } finally {
    button.disabled = false;
    button.textContent = "Analyze Requirement";
  }
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
  state.currentProjectId = run.project_id || "";
  state.profileReviews = {};
  state.resumeReviews = {};
  const meta = document.getElementById("results-meta");
  const projectCopy = run.project_id ? ` - project ${run.project_id}` : "";
  const locationPolicy = run.search_strategy?.location_policy === "strict" ? " - strict location" : "";
  meta.textContent = `${run.candidates.length} candidates - ${run.queries_count} queries - ${run.duration_seconds}s${locationPolicy}${projectCopy}`;

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
      <td>${escapeHtml(candidate.name)}</td>
      <td>${escapeHtml(formatTitleCaseValue(candidate.role))}</td>
      <td>${escapeHtml(formatTitleCaseValue(candidate.location))}</td>
      <td>${escapeHtml(candidate.stack || "-")}</td>
      <td>${escapeHtml(formatTitleCaseValue(candidate.source))}</td>
      <td>${escapeHtml(candidate.status)}</td>
    `;
    row.addEventListener("click", () => selectCandidate(candidate.id));
    body.appendChild(row);
  });

  selectCandidate(run.candidates[0].id);
  loadProjectReviews(run.project_id);
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
      <strong>${escapeHtml(item.role || "Untitled search")}</strong>
      <span>${item.candidate_count} candidates - ${item.strong_matches} strong${item.project_id ? ` - project ${escapeHtml(item.project_id)}` : ""}</span>
    `;
    node.addEventListener("click", async () => {
      const response = await fetch(`/api/searches/${item.id}`);
      const run = await readJsonResponse(response);
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
  const items = await readJsonResponse(response);
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
  setFormMessage("");
  syncRoleVariantsField();

  const data = {
    role: form.role.value.trim(),
    titles: lines(form.titles.value),
    tech_groups: lines(form.tech_groups.value),
    locations: lines(form.locations.value),
    location_policy: "strict",
    experience: form.experience.value,
    availability: form.availability.value,
    num: Number(form.num.value),
    sources: Array.from(form.querySelectorAll('input[name="sources"]:checked')).map((input) => input.value),
    project_id: state.currentProjectId || "",
    requirement_url: state.requirementSourceUrl || document.getElementById("requirement-url")?.value.trim() || "",
    requirement_brief: state.requirementBrief,
    confirmed_brief: state.requirementBrief ? buildConfirmedBriefFromForm() : null,
  };

  if (!validateEnglishOnly(data)) {
    setFormMessage("Please use English only.");
    button.disabled = false;
    button.classList.remove("is-loading");
    button.textContent = "Run Search";
    return;
  }

  button.disabled = true;
  button.classList.add("is-loading");
  button.textContent = "Searching...";
  const progress = startSearchProgress(data);

  try {
    const response = await fetch("/api/search", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    const payload = await readJsonResponse(response);
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
const analyzeRequirementButton = document.getElementById("analyze-requirement-button");
const logoutForm = document.querySelector('form[action="/logout"]');

if (logoutForm) {
  logoutForm.addEventListener("submit", () => {
    sessionStorage.removeItem(TAB_ACCESS_KEY);
    localStorage.removeItem(TAB_BOOTSTRAP_KEY);
  });
}

if (enforceTabAccess()) {
  initializeRolePresets();
  searchForm.addEventListener("submit", handleSearch);
  searchButton.addEventListener("click", () => {
    searchForm.requestSubmit();
  });
  analyzeRequirementButton?.addEventListener("click", handleRequirementAnalysis);

  loadHistory();
}











