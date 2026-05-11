const state = {
  run: null,
  selectedCandidateId: null,
  roleVariants: [],
  requirementBrief: null,
  requirementSourceUrl: "",
  confirmedBrief: null,
  strategyPreview: null,
  currentProjectId: "",
  searchMode: "manual",
  profileReviews: {},
  resumeReviews: {},
};

const TAB_ACCESS_KEY = "engineerSearchTabAccess";
const TAB_BOOTSTRAP_KEY = "engineerSearchTabBootstrap";
const SEARCH_DEPTHS = {
  standard: {
    label: "Standard",
    providers: ["tavily"],
    pageCap: 1,
  },
  medium: {
    label: "Medium",
    providers: ["tavily", "bing_serpapi"],
    pageCap: 2,
  },
  extended: {
    label: "Extended",
    providers: ["tavily", "bing_serpapi", "serpapi"],
    pageCap: 3,
  },
  max: {
    label: "Max",
    providers: ["tavily", "bing_serpapi", "serpapi", "serper"],
    pageCap: 10,
  },
};
const PAGINATED_SEARCH_PROVIDERS = new Set(["bing_serpapi", "serpapi", "serper"]);
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
  ["front office", "Front Office", "domain"],
  ["power trading", "Power Trading", "domain"],
  ["energy trading", "Energy Trading", "domain"],
  ["commodity trading", "Commodity Trading", "domain"],
  ["commodities", "Commodities", "domain"],
  ["etrm", "ETRM", "domain"],
  ["ctrm", "CTRM", "domain"],
  ["orchestrade", "Orchestrade", "tooling"],
  ["endur", "Endur", "tooling"],
  ["openlink", "Openlink", "tooling"],
  ["rightangle", "RightAngle", "tooling"],
  ["allegro", "Allegro", "tooling"],
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

const ROLE_PATTERN_FAMILIES = [
  {
    family: "Energy / ETRM Business Analyst",
    triggers: [
      "etrm",
      "ctrm",
      "front office",
      "power trading",
      "energy trading",
      "commodity trading",
      "commodities",
      "orchestrade",
      "endur",
      "rightangle",
      "allegro",
      "openlink",
    ],
    coreTerms: ["Business Analyst"],
    roleTerms: [],
    queryStrategy: "grouped_anchors",
    fixedAnchors: ["Front Office"],
    domainTerms: ["Power Trading", "Energy Trading", "ETRM"],
    toolTerms: ["Orchestrade", "Endur"],
  },
  {
    family: "QA Automation",
    triggers: ["qa", "quality assurance", "test automation", "automation test", "automated test", "sdet", "tester"],
    coreTerms: ["Automation"],
    roleTerms: ["Engineer", "QA", "Tester", "Test Engineer", "SDET"],
  },
  {
    family: "Java Backend",
    triggers: ["java backend", "backend java", "java developer", "java engineer"],
    coreTerms: ["Java"],
    roleTerms: ["Backend", "Back End", "Engineer", "Developer", "Software Engineer"],
  },
  {
    family: "Frontend",
    triggers: ["frontend", "front end", "react", "angular", "vue"],
    coreTerms: ["Frontend", "Front End"],
    roleTerms: ["Engineer", "Developer", "Software Engineer"],
  },
  {
    family: "Fullstack",
    triggers: ["fullstack", "full stack"],
    coreTerms: ["Fullstack", "Full Stack"],
    roleTerms: ["Engineer", "Developer", "Software Engineer"],
  },
  {
    family: "iOS",
    triggers: ["ios", "swift", "iphone"],
    coreTerms: ["iOS", "Swift"],
    roleTerms: ["Engineer", "Developer", "Mobile Engineer", "Mobile Developer"],
  },
  {
    family: "Android",
    triggers: ["android", "kotlin"],
    coreTerms: ["Android", "Kotlin"],
    roleTerms: ["Engineer", "Developer", "Mobile Engineer", "Mobile Developer"],
  },
  {
    family: "DevOps / SRE",
    triggers: ["devops", "sre", "site reliability", "platform engineer", "infrastructure"],
    coreTerms: ["DevOps", "SRE", "Site Reliability"],
    roleTerms: ["Engineer", "Platform Engineer", "Infrastructure Engineer"],
  },
  {
    family: "Data Engineer",
    triggers: ["data engineer", "etl", "pipeline engineer", "analytics engineer"],
    coreTerms: ["Data"],
    roleTerms: ["Engineer", "ETL", "Pipeline Engineer", "Analytics Engineer"],
  },
  {
    family: "ML / AI Engineer",
    triggers: ["machine learning", "ml engineer", "ai engineer", "applied scientist"],
    coreTerms: ["Machine Learning", "ML", "AI"],
    roleTerms: ["Engineer", "Applied Scientist", "Research Engineer"],
  },
  {
    family: "Embedded",
    triggers: ["embedded", "firmware"],
    coreTerms: ["Embedded"],
    roleTerms: ["Engineer", "Software Engineer", "Firmware Engineer"],
  },
];

const FAMILY_DEFAULT_QUERY_GROUPS = {
  "Java Backend": [
    ["Java", "JVM"],
    ["Spring Boot", "Spring"],
    ["Kafka", "RabbitMQ", "message broker"],
    ["AWS", "cloud"],
    ["microservices", "distributed systems"],
    ["PostgreSQL", "MySQL", "Oracle"],
    ["REST", "API", "GraphQL"],
    ["Docker", "Kubernetes"],
    ["Hibernate", "JPA"],
    ["CI/CD", "Jenkins", "GitLab"],
    ["Redis", "Elasticsearch"],
    ["SQL", "NoSQL"],
  ],
  "QA Automation": [
    ["Python", "pytest"],
    ["Selenium", "Playwright", "Cypress"],
    ["automation framework", "test automation"],
    ["automotive", "embedded", "ADAS"],
    ["HiL", "SIL"],
    ["log analysis", "logs", "virtual environments"],
    ["Git", "CI/CD"],
    ["BDD", "Gherkin", "keyword-driven testing"],
    ["Robot Framework"],
    ["Puppeteer"],
    ["Jenkins", "GitLab"],
    ["API testing", "REST"],
  ],
  Frontend: [
    ["JavaScript", "TypeScript"],
    ["React", "Next.js"],
    ["Angular", "Vue"],
    ["HTML", "CSS"],
    ["Redux", "state management"],
    ["frontend architecture"],
    ["GraphQL", "REST"],
    ["Jest", "Cypress", "Playwright"],
  ],
  Fullstack: [
    ["JavaScript", "TypeScript"],
    ["React", "Angular", "Vue"],
    ["Node.js", "Express"],
    ["Java", "Spring"],
    ["Python", "Django", "FastAPI"],
    ["PostgreSQL", "MySQL", "MongoDB"],
    ["AWS", "cloud"],
    ["Docker", "Kubernetes"],
  ],
  iOS: [
    ["Swift", "SwiftUI"],
    ["iOS", "UIKit"],
    ["Objective-C"],
    ["Xcode"],
    ["Combine", "async await"],
    ["Core Data"],
    ["App Store"],
    ["mobile architecture"],
  ],
  Android: [
    ["Kotlin", "Java"],
    ["Android", "Jetpack"],
    ["Compose", "Jetpack Compose"],
    ["Gradle"],
    ["Coroutines", "Flow"],
    ["Android SDK"],
    ["Google Play"],
    ["mobile architecture"],
  ],
  "DevOps / SRE": [
    ["Kubernetes", "Docker"],
    ["AWS", "Azure", "GCP"],
    ["Terraform", "IaC"],
    ["CI/CD", "Jenkins", "GitLab"],
    ["Prometheus", "Grafana"],
    ["Linux", "Bash"],
    ["SRE", "observability"],
    ["Helm", "ArgoCD"],
  ],
  "Data Engineer": [
    ["Python", "SQL"],
    ["Spark", "Databricks"],
    ["Airflow", "ETL"],
    ["Kafka", "streaming"],
    ["Snowflake", "BigQuery", "Redshift"],
    ["dbt"],
    ["AWS", "GCP", "Azure"],
    ["data pipelines"],
  ],
  "ML / AI Engineer": [
    ["Python", "machine learning"],
    ["PyTorch", "TensorFlow"],
    ["LLM", "NLP"],
    ["MLOps", "model deployment"],
    ["scikit-learn"],
    ["computer vision"],
    ["AWS", "GCP", "Azure"],
    ["vector search", "embeddings"],
  ],
  Embedded: [
    ["C", "C++"],
    ["embedded", "firmware"],
    ["RTOS", "FreeRTOS"],
    ["microcontroller", "MCU"],
    ["CAN", "LIN", "Ethernet"],
    ["automotive", "ADAS"],
    ["Linux", "Yocto"],
    ["hardware", "debugging"],
  ],
};

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

function formatProviderLabel(value) {
  const key = String(value || "").trim().toLowerCase();
  const labels = {
    tavily: "Tavily",
    bing_serpapi: "Bing / SerpApi",
    serpapi: "Google / SerpApi",
    serper: "Google / Serper",
  };
  return labels[key] || formatTitleCaseValue(key.replaceAll("_", " "));
}

function formatProviderErrorKind(kind) {
  const labels = {
    credits: "Credits / quota issue",
    rate_limit: "Rate limit",
    auth: "API key / access issue",
    configuration: "Missing configuration",
    api_error: "Provider API error",
  };
  return labels[kind] || "Provider warning";
}

function getSearchDepthConfig(value) {
  return SEARCH_DEPTHS[value] || SEARCH_DEPTHS.extended;
}

function getSelectedSearchDepth(form = document.getElementById("search-form")) {
  const value = form?.search_depth?.value || document.querySelector('input[name="search_depth"]:checked')?.value;
  return getSearchDepthConfig(value);
}

function getProviderPageCap(provider, searchDepth) {
  return PAGINATED_SEARCH_PROVIDERS.has(provider) ? searchDepth.pageCap : 1;
}

function countProviderPasses(providers, searchDepth) {
  return providers.reduce((total, provider) => total + getProviderPageCap(provider, searchDepth), 0);
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

function renderLimitedList(items, emptyText, limit = 5) {
  const values = Array.isArray(items) ? items.filter(Boolean).slice(0, limit) : [];
  if (!values.length) {
    return `<li>${escapeHtml(emptyText)}</li>`;
  }
  return values.map((item) => `<li>${escapeHtml(shortenSearchPhrase(item, 95))}</li>`).join("");
}

function renderAnchorChips(items, emptyText, limit = 8) {
  const values = Array.isArray(items) ? dedupeTextValues(items).filter(Boolean).slice(0, limit) : [];
  if (!values.length) {
    return `<p class="field-note">${escapeHtml(emptyText)}</p>`;
  }
  return `
    <div class="anchor-chips">
      ${values.map((item) => `<span class="anchor-chip">${escapeHtml(shortenSearchPhrase(item, 32))}</span>`).join("")}
    </div>
  `;
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

function setSearchMode(mode) {
  state.searchMode = mode === "requirement_url" ? "requirement_url" : "manual";
  document.querySelectorAll('input[name="search_mode"]').forEach((input) => {
    input.checked = input.value === state.searchMode;
  });
  const requirementCard = document.getElementById("requirement-card");
  if (requirementCard) {
    requirementCard.classList.toggle("hidden", state.searchMode !== "requirement_url");
  }
  if (state.searchMode === "manual") {
    setRequirementMessage("");
  }
  refreshStrategyPreviewIfVisible();
}

function refreshStrategyPreviewIfVisible() {
  const container = document.getElementById("search-strategy-preview");
  if (!container || container.classList.contains("hidden")) return;
  renderSearchStrategyPreview();
}

function resetSearchStrategyPreview() {
  const container = document.getElementById("search-strategy-preview");
  if (container) {
    container.classList.add("hidden");
    container.innerHTML = "";
  }
  state.strategyPreview = null;
  renderStrategyPreviewStatus(null);
}

function showStrategyPreview() {
  renderSearchStrategyPreview();
  if (state.searchMode === "requirement_url" && state.requirementBrief) {
    setRequirementMessage("Search brief updated. Search will use the current fields.");
  }
}

function renderStrategyPreviewStatus(strategy) {
  const node = document.getElementById("strategy-preview-status");
  if (!node) return;
  if (!strategy) {
    node.classList.add("hidden");
    node.innerHTML = "";
    return;
  }
  node.innerHTML = `
    <strong>${escapeHtml(strategy.role_pattern_family || "Custom role")}</strong>
    <span> ${escapeHtml(strategy.role_pattern_mode || "fallback")}, ${escapeHtml(strategy.role_pattern_confidence || "low")} confidence</span>
    <code>${escapeHtml(strategy.title_pattern || "No role pattern selected.")}</code>
  `;
  node.classList.remove("hidden");
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
    button.addEventListener("click", () => {
      removeRoleVariant(button.dataset.variant);
      refreshStrategyPreviewIfVisible();
    });
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
  refreshStrategyPreviewIfVisible();
}

function initializeRolePresets() {
  const groupSelect = document.getElementById("role-group-select");
  const presetSelect = document.getElementById("role-preset-select");
  const addButton = document.getElementById("add-role-variant");
  const variantInput = document.getElementById("role-variant-input");
  const updateStrategyButton = document.getElementById("update-strategy-preview");
  const modeInputs = Array.from(document.querySelectorAll('input[name="search_mode"]'));

  populateRoleGroups();
  populateRolePresets("");
  renderRoleVariants();
  setSearchMode(state.searchMode);

  modeInputs.forEach((input) => {
    input.addEventListener("change", () => {
      setSearchMode(input.value);
    });
  });

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
    refreshStrategyPreviewIfVisible();
  });

  variantInput?.addEventListener("keydown", (event) => {
    if (event.key !== "Enter") return;
    event.preventDefault();
    addRoleVariant(variantInput.value);
    variantInput.value = "";
    refreshStrategyPreviewIfVisible();
  });

  updateStrategyButton?.addEventListener("click", showStrategyPreview);
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
    providerAlerts: document.getElementById("provider-alerts"),
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
  ui.providerAlerts?.classList.add("hidden");
  document.getElementById("search-diagnostics")?.classList.add("hidden");
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

function renderProviderAlerts(errors) {
  const container = document.getElementById("provider-alerts");
  if (!container) return;
  const providerErrors = Array.isArray(errors) ? errors : [];
  if (!providerErrors.length) {
    container.innerHTML = "";
    container.classList.add("hidden");
    return;
  }

  container.classList.remove("hidden");
  container.innerHTML = providerErrors.map((error) => {
    const kind = error.kind || "api_error";
    const status = error.status_code ? `HTTP ${error.status_code}` : "";
    const detail = error.message ? `<span class="provider-alert-detail">${escapeHtml(error.message)}</span>` : "";
    const userMessage = error.user_message || "This provider failed, but search continued with the remaining providers.";
    return `
      <div class="provider-alert-card is-${escapeHtml(kind)}">
        <div>
          <strong>${escapeHtml(formatProviderLabel(error.provider))}</strong>
          <span>${escapeHtml(formatProviderErrorKind(kind))}${status ? ` · ${escapeHtml(status)}` : ""}</span>
        </div>
        <p>${escapeHtml(userMessage)}</p>
        ${detail}
      </div>
    `;
  }).join("");
}

function toReportNumber(value) {
  const number = Number(value);
  return Number.isFinite(number) ? number : 0;
}

function countByProvider(items, providerKey = "provider", { includeVerification = true } = {}) {
  return (Array.isArray(items) ? items : []).reduce((counts, item) => {
    if (!includeVerification && item?.query_type === "location_verification") return counts;
    const provider = item?.[providerKey] || "unknown";
    counts[provider] = (counts[provider] || 0) + 1;
    return counts;
  }, {});
}

function orderedProviderKeys(...sources) {
  const keys = [];
  const seen = new Set();
  sources.forEach((source) => {
    const values = Array.isArray(source) ? source : Object.keys(source || {});
    values.forEach((value) => {
      if (!value || seen.has(value)) return;
      seen.add(value);
      keys.push(value);
    });
  });
  return keys;
}

function getProviderContributionReport(run) {
  return run?.provider_contribution_report
    || run?.search_strategy?.provider_contribution_report
    || buildProviderContributionFallback(run);
}

function buildProviderContributionFallback(run) {
  const strategy = run?.search_strategy || {};
  const diagnostics = strategy.result_diagnostics || {};
  const byProvider = diagnostics.by_provider || {};
  const hasDiagnostics = Object.keys(byProvider).length > 0;
  if (!hasDiagnostics) return null;

  const queryProviders = Array.isArray(strategy.providers) ? strategy.providers : [];
  const plannedCalls = countByProvider(run?.queries || [], "provider", { includeVerification: false });
  const executedCalls = countByProvider(run?.queries || [], "provider", { includeVerification: false });
  const verificationCalls = countByProvider(
    (run?.queries || []).filter((item) => item.query_type === "location_verification"),
    "provider",
  );
  const finalCandidates = countByProvider(run?.candidates || [], "search_provider");
  const warnings = countByProvider(run?.provider_errors || [], "provider");
  const providers = orderedProviderKeys(queryProviders, byProvider, finalCandidates, warnings).map((provider) => {
    const stats = byProvider[provider] || {};
    const acceptedRows = toReportNumber(stats.accepted_rows);
    const finalCount = toReportNumber(finalCandidates[provider]);
    return {
      provider,
      planned_calls: toReportNumber(plannedCalls[provider]),
      executed_calls: toReportNumber(executedCalls[provider]),
      verification_calls: toReportNumber(verificationCalls[provider]),
      raw_rows: toReportNumber(stats.raw_rows),
      quality_rows: toReportNumber(stats.quality_rows),
      strict_location_rejected: toReportNumber(stats.strict_location_rejected),
      accepted_rows: acceptedRows,
      final_candidates: finalCount,
      unique_lift: finalCount,
      deduped_or_capped_out: Math.max(acceptedRows - finalCount, 0),
      warning_count: toReportNumber(warnings[provider]),
    };
  });

  return {
    location_policy: strategy.location_policy || "strict",
    providers,
    totals: {
      requested_candidates: toReportNumber(run?.search?.results_limit),
      planned_calls: providers.reduce((sum, item) => sum + item.planned_calls, 0),
      executed_calls: providers.reduce((sum, item) => sum + item.executed_calls, 0),
      verification_calls: providers.reduce((sum, item) => sum + item.verification_calls, 0),
      raw_rows: toReportNumber(diagnostics.raw_rows),
      quality_rows: toReportNumber(diagnostics.quality_rows),
      strict_location_rejected: toReportNumber(diagnostics.strict_location_rejected),
      accepted_rows: toReportNumber(diagnostics.accepted_rows),
      final_candidates: Array.isArray(run?.candidates) ? run.candidates.length : 0,
      provider_warnings: Array.isArray(run?.provider_errors) ? run.provider_errors.length : 0,
    },
  };
}

function renderProviderReportMetric(label, value, subtext = "") {
  return `
    <div class="provider-report-metric">
      <strong>${escapeHtml(toReportNumber(value).toLocaleString())}</strong>
      <span>${escapeHtml(label)}</span>
      ${subtext ? `<small>${escapeHtml(subtext)}</small>` : ""}
    </div>
  `;
}

function formatReportPercent(value, total) {
  const numerator = toReportNumber(value);
  const denominator = toReportNumber(total);
  if (!denominator) return "0%";
  return `${Math.round((numerator / denominator) * 100)}%`;
}

function csvCell(value) {
  const text = String(value ?? "");
  return `"${text.replaceAll('"', '""')}"`;
}

function providerReportToCsv(report, run) {
  const headers = [
    "Run ID",
    "Provider",
    "Planned calls",
    "Executed calls",
    "Verification calls",
    "Raw rows",
    "Quality rows",
    "Strict location rejected",
    "Accepted rows",
    "Final unique candidates",
    "Unique lift",
    "Deduped or capped out",
    "Warnings",
  ];
  const rows = (report.providers || []).map((provider) => [
    run?.id || "",
    formatProviderLabel(provider.provider),
    provider.planned_calls,
    provider.executed_calls,
    provider.verification_calls,
    provider.raw_rows,
    provider.quality_rows,
    provider.strict_location_rejected,
    provider.accepted_rows,
    provider.final_candidates,
    provider.unique_lift,
    provider.deduped_or_capped_out,
    provider.warning_count,
  ]);
  return [
    headers.map(csvCell).join(","),
    ...rows.map((row) => row.map(csvCell).join(",")),
  ].join("\n");
}

function downloadProviderReportCsv(report, run) {
  const csv = providerReportToCsv(report, run);
  const blob = new Blob([`\uFEFF${csv}`], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `provider-contribution-${run?.id || "search"}.csv`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

function renderSearchDiagnostics(run) {
  const container = document.getElementById("search-diagnostics");
  if (!container) return;
  const report = getProviderContributionReport(run);
  const providerRows = Array.isArray(report?.providers) ? report.providers : [];
  if (!providerRows.length) {
    container.innerHTML = "";
    container.classList.add("hidden");
    return;
  }

  const totals = report.totals || {};
  container.classList.remove("hidden");
  container.innerHTML = `
    <div class="provider-report-card">
      <div class="provider-report-header">
        <div>
          <strong>Provider Contribution Report</strong>
          <p>Raw results -> strict-location filtering -> dedupe/cap -> final unique candidates.</p>
        </div>
        <button type="button" class="ghost-btn compact-btn" data-provider-report-export>Export CSV</button>
      </div>
      <div class="provider-report-metrics">
        ${renderProviderReportMetric("raw rows", totals.raw_rows)}
        ${renderProviderReportMetric("strict location rejected", totals.strict_location_rejected)}
        ${renderProviderReportMetric("accepted after strict", totals.accepted_rows)}
        ${renderProviderReportMetric("final unique candidates", totals.final_candidates, `${formatReportPercent(totals.final_candidates, totals.accepted_rows)} of accepted`)}
        ${renderProviderReportMetric("executed provider calls", totals.executed_calls, `${toReportNumber(totals.verification_calls)} verification`)}
      </div>
      <div class="provider-report-table-wrap">
        <table class="provider-report-table">
          <thead>
            <tr>
              <th>Provider</th>
              <th>Calls</th>
              <th>Raw</th>
              <th>Strict filtered</th>
              <th>After strict</th>
              <th>Final unique</th>
              <th>Dedupe / cap</th>
              <th>Warnings</th>
            </tr>
          </thead>
          <tbody>
            ${providerRows.map((provider) => `
              <tr>
                <td><strong>${escapeHtml(formatProviderLabel(provider.provider))}</strong></td>
                <td>${escapeHtml(toReportNumber(provider.executed_calls).toLocaleString())}/${escapeHtml(toReportNumber(provider.planned_calls).toLocaleString())}</td>
                <td>${escapeHtml(toReportNumber(provider.raw_rows).toLocaleString())}</td>
                <td>${escapeHtml(toReportNumber(provider.strict_location_rejected).toLocaleString())}</td>
                <td>${escapeHtml(toReportNumber(provider.accepted_rows).toLocaleString())}</td>
                <td><span class="provider-lift">${escapeHtml(toReportNumber(provider.final_candidates).toLocaleString())}</span></td>
                <td>${escapeHtml(toReportNumber(provider.deduped_or_capped_out).toLocaleString())}</td>
                <td>${escapeHtml(toReportNumber(provider.warning_count).toLocaleString())}</td>
              </tr>
            `).join("")}
          </tbody>
        </table>
      </div>
      <p class="provider-report-note">
        Unique lift is attributed to the provider whose row survived dedupe first. This is enough to compare provider value without exposing noisy raw diagnostics in the main table.
      </p>
    </div>
  `;
  container.querySelector("[data-provider-report-export]")?.addEventListener("click", () => {
    downloadProviderReportCsv(report, run);
  });
}

function startSearchProgress(data) {
  const sourceCount = Math.max(data.sources.length, 1);
  const providerCount = Math.max(data.providers?.length || 1, 1);
  const expectedSteps = getExpectedQueryPasses(data.num);
  const expectedDuration = Math.max(9000, 4500 + expectedSteps * 2800 + sourceCount * 1200 + providerCount * 1800);
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
    { until: 35, title: "Building query set", copy: `Preparing query passes across ${providerCount} search provider${providerCount > 1 ? "s" : ""}.` },
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
  const providerCopy = candidate.search_provider
    ? `<p class="field-note">Found via ${escapeHtml(formatProviderLabel(candidate.search_provider))}</p>`
    : "";

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
      ${providerCopy}
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
  setSearchMode("requirement_url");
  state.requirementBrief = brief;
  state.requirementSourceUrl = result.source_url || document.getElementById("requirement-url")?.value.trim() || "";
  state.confirmedBrief = null;
  resetSearchStrategyPreview();
  state.currentProjectId = "";
  const intent = buildSearchIntentFromBrief(brief);
  const mustHaveAnchors = renderAnchorChips(
    [...(intent.must_have_keywords || []), ...(intent.tool_keywords || [])],
    "No short search anchors extracted."
  );
  const niceToHave = renderLimitedList(brief.nice_to_have_skills, "No nice-to-have skills extracted.", 5);
  const mustHaveDetails = renderLimitedList(brief.must_have_skills, "No must-have details extracted.", 12);
  const questions = renderLimitedList(brief.open_questions, "No open questions.");
  const variants = renderLimitedList(brief.role_variants, "No role variants extracted.", 4);

  container.classList.remove("hidden");
  container.innerHTML = `
    <div class="requirement-brief-header">
      <strong>Search brief draft</strong>
      <span>${escapeHtml(brief.confidence || "low")} confidence</span>
    </div>
    <dl class="brief-grid">
      <div><dt>Role</dt><dd>${escapeHtml(brief.role || "-")}</dd></div>
      <div><dt>Seniority</dt><dd>${escapeHtml(brief.seniority || "-")}</dd></div>
      <div><dt>Location</dt><dd>${escapeHtml(brief.location || "-")}</dd></div>
      <div><dt>Remote</dt><dd>${escapeHtml(brief.remote_policy || "-")}</dd></div>
      <div><dt>Domain</dt><dd>${escapeHtml(brief.domain || "-")}</dd></div>
    </dl>
    <div class="brief-section">
      <h4>Must-have anchors</h4>
      ${mustHaveAnchors}
    </div>
    <details class="brief-details">
      <summary>Nice-to-have anchors</summary>
      <ul>${niceToHave}</ul>
    </details>
    <details class="brief-details">
      <summary>Full extracted requirements</summary>
      <div class="brief-section">
        <h4>Must-have details</h4>
        <ul>${mustHaveDetails}</ul>
      </div>
      <div class="brief-section">
        <h4>Nice-to-have details</h4>
        <ul>${niceToHave}</ul>
      </div>
    </details>
    <details class="brief-details">
      <summary>Suggested role variants</summary>
      <ul>${variants}</ul>
    </details>
    <details class="brief-details">
      <summary>Open questions</summary>
      <ul>${questions}</ul>
    </details>
    <button type="button" class="primary-btn apply-brief-btn" id="apply-requirement-brief">Apply to Search Builder</button>
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
  const strategyPreview = buildStrategyPreviewFromForm();
  state.strategyPreview = strategyPreview;
  const searchIntent = strategyPreview.search_intent || buildSearchIntentFromForm(form);
  const usesRequirement = state.searchMode === "requirement_url" && Boolean(state.requirementBrief);
  const requirementUrl = state.searchMode === "requirement_url"
    ? state.requirementSourceUrl || document.getElementById("requirement-url")?.value.trim() || ""
    : "";
  const searchDepth = getSelectedSearchDepth(form);
  return {
    source_type: usesRequirement ? "requirement_url" : "manual",
    source_url: requirementUrl,
    original_brief: usesRequirement ? state.requirementBrief : null,
    role: form.role.value.trim(),
    role_variants: [...state.roleVariants],
    tech_groups: lines(form.tech_groups.value),
    search_intent: searchIntent,
    search_strategy: strategyPreview,
    locations: lines(form.locations.value),
    location_policy: "strict",
    sources: Array.from(form.querySelectorAll('input[name="sources"]:checked')).map((input) => input.value),
    search_depth: form.search_depth?.value || "extended",
    providers: searchDepth.providers,
    results_limit: Number(form.num.value),
  };
}

function buildQuotedOrGroup(values) {
  const cleaned = dedupeTextValues(values).filter(Boolean);
  if (!cleaned.length) return "";
  if (cleaned.length === 1) return `"${cleaned[0]}"`;
  return `(${cleaned.map((value) => `"${value}"`).join(" OR ")})`;
}

function buildTitlePattern(primaryRole, roleVariants) {
  const primary = cleanSearchPhrase(primaryRole);
  const variants = dedupeTextValues(roleVariants).filter(Boolean);
  if (primary && variants.length) return `"${primary}" ${buildQuotedOrGroup(variants)}`;
  if (primary) return `"${primary}"`;
  return buildQuotedOrGroup(variants);
}

function flattenRolePatternContext(value) {
  if (!value) return [];
  if (typeof value === "string") return [value];
  if (Array.isArray(value)) return value.flatMap(flattenRolePatternContext);
  if (typeof value === "object") return Object.values(value).flatMap(flattenRolePatternContext);
  return [String(value)];
}

function buildSemanticRolePattern(primaryRole, roleVariants, context = null) {
  const titleText = [primaryRole, ...roleVariants].join(" ").toLowerCase().replaceAll("-", " ").replaceAll("/", " ");
  const contextText = flattenRolePatternContext(context).join(" ").toLowerCase().replaceAll("-", " ").replaceAll("/", " ");
  let titleMatched = null;
  let titleScore = 0;
  let contextMatched = null;
  let contextScore = 0;
  ROLE_PATTERN_FAMILIES.forEach((family) => {
    const titleHits = family.triggers.filter((trigger) => titleText.includes(trigger));
    const contextHits = family.triggers.filter((trigger) => contextText.includes(trigger));
    if (titleHits.length > titleScore) {
      titleMatched = family;
      titleScore = titleHits.length;
    } else if (!titleHits.length && contextHits.length > contextScore) {
      contextMatched = family;
      contextScore = contextHits.length;
    }
  });
  const matched = titleMatched || contextMatched;
  if (!matched) {
    return {
      family: "Custom role",
      mode: "fallback",
      confidence: "low",
      coreTerms: [primaryRole].filter(Boolean),
      roleTerms: roleVariants,
      queryStrategy: "skill_groups",
      fixedAnchors: [],
      domainTerms: [],
      toolTerms: [],
      titlePattern: buildTitlePattern(primaryRole, roleVariants),
    };
  }
  return {
    family: matched.family,
    mode: "semantic",
    confidence: titleMatched ? "high" : "medium",
    coreTerms: matched.coreTerms,
    roleTerms: matched.roleTerms,
    queryStrategy: matched.queryStrategy || "skill_groups",
    fixedAnchors: matched.fixedAnchors || [],
    domainTerms: matched.domainTerms || [],
    toolTerms: matched.toolTerms || [],
    titlePattern: `${buildQuotedOrGroup(matched.coreTerms)} ${buildQuotedOrGroup(matched.roleTerms)}`.trim(),
  };
}

function buildLocationQueryValues(locations) {
  const values = dedupeTextValues(
    locations.map((location) => {
      const primaryLocation = cleanSearchPhrase(location).split(/[,;/\n]+/)[0] || "";
      const normalized = cleanSearchPhrase(primaryLocation).toLowerCase().replaceAll("-", " ").replaceAll("/", " ");
      const stripped = normalized
        .replace(/\bwork from home\b/g, " ")
        .replace(/\bremote work\b/g, " ")
        .replace(/\bremotely\b/g, " ")
        .replace(/\bremote\b/g, " ")
        .replace(/\bwfh\b/g, " ")
        .replace(/\s+/g, " ")
        .trim();
      if (stripped) return stripped;
      return /\b(remote|remotely|remote work|work from home|wfh)\b/.test(normalized) ? "remote" : normalized;
    })
  ).filter(Boolean);
  const hasConcreteLocation = values.some((value) => value.toLowerCase() !== "remote");
  return hasConcreteLocation ? values.filter((value) => value.toLowerCase() !== "remote") : values;
}

function buildGroupedAnchorPreviewQueries(rolePattern, locations, sources) {
  const sampleQueries = [];
  const domainTerms = rolePattern.domainTerms?.length ? rolePattern.domainTerms : [""];
  const toolTerms = [...(rolePattern.toolTerms || []), ""];

  (sources.length ? sources : ["linkedin"]).slice(0, 1).forEach(() => {
    (locations.length ? locations : [""]).slice(0, 5).forEach((location) => {
      domainTerms.forEach((domainTerm) => {
        toolTerms.forEach((toolTerm) => {
          const parts = ['site:linkedin.com/in/'];
          const titlePattern = rolePattern.titlePattern;
          const fixedAnchors = rolePattern.fixedAnchors || [];
          if (titlePattern) parts.push(titlePattern);
          fixedAnchors.forEach((anchor) => {
            if (anchor) parts.push(`"${anchor}"`);
          });
          if (domainTerm) parts.push(`"${domainTerm}"`);
          if (toolTerm) parts.push(`"${toolTerm}"`);
          if (location) parts.push(`"${location}"`);
          sampleQueries.push(parts.join(" "));
        });
      });

      const broadParts = ['site:linkedin.com/in/'];
      if (rolePattern.titlePattern) broadParts.push(rolePattern.titlePattern);
      (rolePattern.fixedAnchors || []).forEach((anchor) => {
        if (anchor) broadParts.push(`"${anchor}"`);
      });
      const domainGroup = buildQuotedOrGroup(rolePattern.domainTerms || []);
      if (domainGroup) broadParts.push(domainGroup);
      if (location) broadParts.push(`"${location}"`);
      sampleQueries.push(broadParts.join(" "));
    });
  });

  return dedupeTextValues(sampleQueries);
}

function buildGroupedAnchorQueryCount(rolePattern, locations, sources) {
  const domainCount = Math.max((rolePattern.domainTerms || []).length, 1);
  const toolCount = (rolePattern.toolTerms || []).length + 1;
  const variantCount = domainCount * toolCount + 1;
  return variantCount * Math.max(locations.length, 1) * Math.max(sources.length, 1);
}

function applyProviderDepthToPreview(baseQueries, providers) {
  const queryGroups = [];
  baseQueries.forEach((query) => {
    providers.forEach((provider) => {
      queryGroups.push({ provider, query });
    });
  });
  return queryGroups;
}

function buildStrategyPreviewFromForm() {
  const form = document.getElementById("search-form");
  syncRoleVariantsField();
  const primaryRole = shortenSearchPhrase(form.role.value.trim(), 80);
  const roleVariants = state.roleVariants.filter(Boolean).map((item) => shortenSearchPhrase(item, 80));
  const titles = dedupeTextValues([primaryRole, ...roleVariants]);
  const searchIntent = buildSearchIntentFromForm(form);
  const skillGroups = searchIntent.skill_groups.length
    ? searchIntent.skill_groups
    : lines(form.tech_groups.value).flatMap((group) => chunkArray(group.split("|").map((item) => shortenSearchPhrase(item, 45)).filter(Boolean), 3));
  const displayLocations = lines(form.locations.value).map((item) => shortenSearchPhrase(item, 60));
  const locations = buildLocationQueryValues(displayLocations);
  const sources = Array.from(form.querySelectorAll('input[name="sources"]:checked')).map((input) => input.value);
  const searchDepthKey = form.search_depth?.value || "extended";
  const searchDepth = getSearchDepthConfig(searchDepthKey);
  const rolePattern = buildSemanticRolePattern(primaryRole, roleVariants, {
    searchIntent,
    requirementBrief: state.searchMode === "requirement_url" ? state.requirementBrief : null,
    techGroups: lines(form.tech_groups.value),
  });
  const expandedSkillGroups = expandSkillGroupsForTarget(skillGroups, rolePattern.family, form.num.value);
  const isGroupedAnchorStrategy = rolePattern.queryStrategy === "grouped_anchors";
  const baseQueryCount = isGroupedAnchorStrategy
    ? buildGroupedAnchorQueryCount(rolePattern, locations, sources)
    : Math.max(expandedSkillGroups.length, 1) * Math.max(locations.length, 1) * Math.max(sources.length, 1);
  const providerPasses = countProviderPasses(searchDepth.providers, searchDepth);
  const queryCount = baseQueryCount * providerPasses;
  let sampleQueries = [];
  const titlePattern = rolePattern.titlePattern;

  if (isGroupedAnchorStrategy) {
    sampleQueries = buildGroupedAnchorPreviewQueries(rolePattern, locations, sources);
  } else {
    (expandedSkillGroups.length ? expandedSkillGroups : [[]]).slice(0, 5).forEach((skills) => {
      (locations.length ? locations : [""]).slice(0, 1).forEach((location) => {
        const parts = ['site:linkedin.com/in/'];
        if (titlePattern) parts.push(titlePattern);
        if (skills.length === 1) parts.push(`"${skills[0]}"`);
        if (skills.length > 1) parts.push(`(${skills.map((skill) => `"${skill}"`).join(" OR ")})`);
        if (location) parts.push(`"${location}"`);
        sampleQueries.push(parts.join(" "));
      });
    });
  }
  const providerSampleQueries = applyProviderDepthToPreview(sampleQueries, searchDepth.providers);

  return {
    primary_role: primaryRole,
    role_variants: roleVariants,
    title_pattern: titlePattern,
    role_pattern_family: rolePattern.family,
    role_pattern_mode: rolePattern.mode,
    role_pattern_confidence: rolePattern.confidence,
    query_strategy: rolePattern.queryStrategy,
    titles,
    skill_groups: expandedSkillGroups,
    original_skill_groups: skillGroups,
    search_intent: searchIntent,
    locations,
    display_locations: displayLocations,
    sources,
    search_depth: searchDepthKey,
    search_depth_label: searchDepth.label,
    providers: searchDepth.providers,
    provider_passes: providerPasses,
    base_query_count: baseQueryCount,
    query_count: queryCount,
    location_policy: "strict",
    sample_queries: sampleQueries.slice(0, 5),
    sample_provider_queries: providerSampleQueries.slice(0, 5),
  };
}

function renderSearchStrategyPreview() {
  const container = document.getElementById("search-strategy-preview");
  if (!container) return;
  const strategy = buildStrategyPreviewFromForm();
  state.strategyPreview = strategy;
  renderStrategyPreviewStatus(strategy);
  container.classList.remove("hidden");
  container.innerHTML = `
    <div class="requirement-brief-header">
      <strong>Search strategy preview</strong>
      <span>${strategy.query_count} planned searches</span>
    </div>
    <div class="strategy-summary">
      <strong>${escapeHtml(strategy.role_pattern_family || "Custom role")}</strong>
      <code>${escapeHtml(strategy.title_pattern || "No role selected.")}</code>
    </div>
    <details class="brief-details">
      <summary>Role logic</summary>
      <ul>
        <li>Family: ${escapeHtml(strategy.role_pattern_family || "Custom role")} (${escapeHtml(strategy.role_pattern_mode || "fallback")}, ${escapeHtml(strategy.role_pattern_confidence || "low")} confidence)</li>
        <li>Pattern: ${escapeHtml(strategy.title_pattern || "No role selected.")}</li>
        <li>Family is recalculated from Detected Role, Role Signals, and extracted requirement/search-intent signals.</li>
        <li>Your edits affect this pattern immediately; if no semantic family matches, the edited role/signals are searched directly.</li>
      </ul>
    </details>
    <details class="brief-details">
      <summary>Location policy</summary>
      <ul>
        <li>Strict: candidates must show target location evidence in indexed text.</li>
        <li>Search location: ${escapeHtml(strategy.locations.length ? strategy.locations.join(" | ") : "No location selected.")}</li>
      </ul>
    </details>
    <details class="brief-details">
      <summary>Must-have search anchors</summary>
      <ul>${renderList(strategy.search_intent.must_have_keywords, "No must-have anchors selected.")}</ul>
    </details>
    <details class="brief-details">
      <summary>Domain keywords</summary>
      <ul>${renderList(strategy.search_intent.domain_keywords, "No domain keywords selected.")}</ul>
    </details>
    <details class="brief-details">
      <summary>Query groups</summary>
      <ul>${renderList(strategy.skill_groups.map((group) => group.join(" | ")), "No skills selected.")}</ul>
    </details>
    <details class="brief-details">
      <summary>Result limit</summary>
      <ul><li>All planned searches can run; final candidate list is deduped and capped by Results Limit.</li></ul>
    </details>
    <details class="brief-details" open>
      <summary>Search depth</summary>
      <ul>
        <li>${escapeHtml(strategy.search_depth_label || "Extended")}: ${escapeHtml((strategy.providers || []).map(formatProviderLabel).join(" + ") || "No provider selected.")}</li>
        <li>Base queries: ${escapeHtml(strategy.base_query_count || strategy.query_count)}; provider/page passes: ${escapeHtml(strategy.provider_passes || strategy.query_count)}; planned calls: ${escapeHtml(strategy.query_count)}.</li>
      </ul>
    </details>
    <details class="brief-details">
      <summary>Sample provider queries</summary>
      <ul>${renderList((strategy.sample_provider_queries || []).map((item) => `[${formatProviderLabel(item.provider)}] ${item.query}`), "No query examples.")}</ul>
    </details>
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
  const terms = dedupeIntentTerms([
    ...collectSearchIntentTerms(formTerms),
    ...briefTerms,
  ]);
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

function desiredQueryGroupCount(targetCount) {
  const limit = Number(targetCount) || 20;
  if (limit <= 20) return 3;
  if (limit <= 40) return 4;
  if (limit <= 60) return 5;
  if (limit <= 100) return 8;
  return 12;
}

function groupKey(group) {
  return group.map((value) => cleanSearchPhrase(value).toLowerCase()).filter(Boolean).sort().join("|");
}

function addQueryGroup(groups, group) {
  const cleaned = dedupeTextValues(group || []);
  if (!cleaned.length) {
    if (!groups.length) groups.push([]);
    return;
  }
  const key = groupKey(cleaned);
  if (groups.some((existing) => groupKey(existing) === key)) return;
  if (isSubsetOfExistingGroup(cleaned, groups)) return;
  groups.push(cleaned);
}

function isSubsetOfExistingGroup(group, groups) {
  const newTerms = new Set(group.map((value) => cleanSearchPhrase(value).toLowerCase()).filter(Boolean));
  if (!newTerms.size) return false;
  return groups.some((existing) => {
    const existingTerms = new Set(existing.map((value) => cleanSearchPhrase(value).toLowerCase()).filter(Boolean));
    return Array.from(newTerms).every((term) => existingTerms.has(term));
  });
}

function expandSkillGroupsForTarget(skillGroups, rolePatternFamily, targetCount) {
  const desiredCount = desiredQueryGroupCount(targetCount);
  const expanded = [];
  (skillGroups || [[]]).forEach((group) => addQueryGroup(expanded, group));
  (FAMILY_DEFAULT_QUERY_GROUPS[rolePatternFamily] || []).forEach((group) => {
    if (expanded.length >= desiredCount) return;
    addQueryGroup(expanded, group);
  });
  return (expanded.length ? expanded : [[]]).slice(0, desiredCount);
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
  const providers = Array.isArray(run.search_strategy?.providers) ? run.search_strategy.providers : [];
  const providerCopy = providers.length ? ` - ${providers.map(formatProviderLabel).join(" + ")}` : "";
  const providerErrors = Array.isArray(run.provider_errors) ? run.provider_errors : [];
  const warningCopy = providerErrors.length ? ` - ${providerErrors.length} provider warning${providerErrors.length === 1 ? "" : "s"}` : "";
  meta.textContent = `${run.candidates.length} candidates - ${run.queries_count} queries - ${run.duration_seconds}s${locationPolicy}${providerCopy}${warningCopy}${projectCopy}`;
  renderProviderAlerts(providerErrors);
  renderSearchDiagnostics(run);

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
    search_depth: form.search_depth?.value || "extended",
    providers: getSelectedSearchDepth(form).providers,
    experience: form.experience.value,
    availability: form.availability.value,
    num: Number(form.num.value),
    sources: Array.from(form.querySelectorAll('input[name="sources"]:checked')).map((input) => input.value),
    project_id: state.currentProjectId || "",
    requirement_url: state.searchMode === "requirement_url"
      ? state.requirementSourceUrl || document.getElementById("requirement-url")?.value.trim() || ""
      : "",
    requirement_brief: state.searchMode === "requirement_url" ? state.requirementBrief : null,
    confirmed_brief: buildConfirmedBriefFromForm(),
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
const searchDepthInputs = Array.from(document.querySelectorAll('input[name="search_depth"]'));
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
  searchForm.addEventListener("input", (event) => {
    if (event.target?.id === "role-variant-input") return;
    refreshStrategyPreviewIfVisible();
  });
  searchForm.addEventListener("change", refreshStrategyPreviewIfVisible);
  searchDepthInputs.forEach((input) => {
    input.addEventListener("change", refreshStrategyPreviewIfVisible);
  });
  searchButton.addEventListener("click", () => {
    searchForm.requestSubmit();
  });
  analyzeRequirementButton?.addEventListener("click", handleRequirementAnalysis);

  loadHistory();
}











