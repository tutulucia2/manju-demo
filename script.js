const API_BASE = (window.MANJU_API_BASE || "http://127.0.0.1:8010").replace(/\/$/, "");
const STEP1_HISTORY_KEY = "manju-step1-history-v1";

const steps = [
  { id: 1, label: "项目输入" },
  { id: 2, label: "商业方案" },
  { id: 3, label: "世界观推演" },
  { id: 4, label: "人物卡" },
  { id: 5, label: "爆款对标" },
  { id: 6, label: "生成剧本" },
];

let currentStep = 1;
const appState = {
  projectId: "",
  selectedProposalId: null,
  selectedProposalText: "",
};

const stepper = document.getElementById("stepper");
const panels = [...document.querySelectorAll(".step-panel")];
const proposalStack = document.getElementById("proposalStack");
const step3WorldContent = document.getElementById("step3WorldContent");
const characterList = document.getElementById("characterList");
const step5BenchmarkContent = document.getElementById("step5BenchmarkContent");
const step6ScriptTitle = document.getElementById("step6ScriptTitle");
const step6ScriptText = document.getElementById("step6ScriptText");
const step6SummaryContent = document.getElementById("step6SummaryContent");
const loadingProgress = document.getElementById("loadingProgress");
const loadingProgressFill = document.getElementById("loadingProgressFill");
const loadingProgressPercent = document.getElementById("loadingProgressPercent");
const loadingProgressLabel = document.getElementById("loadingProgressLabel");

const step1Fields = {
  projectName: document.getElementById("step1ProjectName"),
  coreIdea: document.getElementById("step1CoreIdea"),
  commercialDirective: document.getElementById("step1CommercialDirective"),
  storyBible: document.getElementById("step1StoryBible"),
};
const step1HistorySelects = {
  projectName: document.getElementById("step1ProjectNameHistory"),
  coreIdea: document.getElementById("step1CoreIdeaHistory"),
  commercialDirective: document.getElementById("step1CommercialDirectiveHistory"),
  storyBible: document.getElementById("step1StoryBibleHistory"),
};

const step1GenerateBtn = document.getElementById("step1GenerateBtn");
const step1Feedback = document.getElementById("step1Feedback");
const step2RegenerateBtn = document.getElementById("step2RegenerateBtn");
const step2ConfirmBtn = document.getElementById("step2ConfirmBtn");
const step2Feedback = document.getElementById("step2Feedback");
const step3RegenerateBtn = document.getElementById("step3RegenerateBtn");
const step3ConfirmBtn = document.getElementById("step3ConfirmBtn");
const step3Feedback = document.getElementById("step3Feedback");
const step4RegenerateBtn = document.getElementById("step4RegenerateBtn");
const step4ConfirmBtn = document.getElementById("step4ConfirmBtn");
const step4Feedback = document.getElementById("step4Feedback");
const step5ConfirmBtn = document.getElementById("step5ConfirmBtn");
const step5Feedback = document.getElementById("step5Feedback");
const step6Feedback = document.getElementById("step6Feedback");

const loadingProgressState = {
  activeCount: 0,
  timer: null,
  value: 0,
};

const loadingLabelMap = {
  step1GenerateBtn: "商业方案生成中",
  step2RegenerateBtn: "商业方案重生成中",
  step2ConfirmBtn: "世界观与人物卡准备中",
  step3RegenerateBtn: "世界观重生成中",
  step3ConfirmBtn: "人物卡生成中",
  step4RegenerateBtn: "人物卡重生成中",
  step4ConfirmBtn: "爆款对标分析中",
  step5ConfirmBtn: "完整剧本生成中",
};

const STEP_TRANSITION_DELAY_MS = 140;

const characterState = {
  ellen: {
    name: "艾伦（Ellen）",
    hairStyle: "中长黑发，线条利落，偏冷感层次",
    hairColor: "黑色",
    eyeColor: "冷灰蓝",
    marks: "左耳有系统感银色耳饰，眉骨处有极淡旧伤痕",
    heightRatio: "高挑修长，肩颈线条明显，镜头中偏强控制感比例",
    outfits: [
      "银灰风衣，深色高领，极简系统感配饰",
      "深灰作战夹克，收束腰线，黑色长靴",
      "冷白衬衫，宽松长裤，室内裸耳造型",
    ],
  },
  linya: {
    name: "林涯（Leah）",
    hairStyle: "短黑发，整洁向后梳理",
    hairColor: "黑色",
    eyeColor: "深褐",
    marks: "黑金镜框，神情克制，几乎不出现明显情绪波动",
    heightRatio: "偏高，肩背平直，西装线条稳定",
    outfits: [
      "深色西装，黑金镜框，低饱和衬衫",
      "长款黑色大衣，冷光环境下的正式造型",
      "居家浅灰针织上衣，保留眼镜与极简配色",
    ],
  },
  ruanqiu: {
    name: "阮秋（Kael）",
    hairStyle: "短碎发，偏机能感处理",
    hairColor: "深棕",
    eyeColor: "琥珀",
    marks: "手臂数据纹身，随身便携终端",
    heightRatio: "中等偏高，动作轻快，躯干重心稳定",
    outfits: [
      "机能夹克，便携终端腰包，实验室运动鞋",
      "深色工装外套，内搭功能背心，操作手套",
      "室内连帽卫衣，保留终端挂件与纹身露出",
    ],
  },
};
function renderStepper() {
  stepper.innerHTML = steps
    .map((step) => {
      const stateClass =
        step.id < currentStep ? "completed" : step.id === currentStep ? "active" : "";
      const badge = step.id < currentStep ? "✓" : step.id;
      return `
        <div class="step-item ${stateClass}">
          <div class="step-badge">${badge}</div>
          <div class="step-label">${step.label}</div>
        </div>
      `;
    })
    .join("");
}

function renderPanels() {
  panels.forEach((panel) => {
    panel.classList.toggle("active", Number(panel.dataset.step) === currentStep);
  });
}

function goToStep(step) {
  currentStep = Math.max(1, Math.min(6, step));
  renderStepper();
  renderPanels();
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function setFeedback(node, text = "", type = "") {
  if (!node) return;
  node.textContent = text;
  node.classList.remove("error", "success");
  if (type) node.classList.add(type);
}

function setButtonLoading(button, loading, loadingText) {
  if (!button) return;
  if (loading) {
    button.dataset.originalText = button.textContent;
    button.textContent = loadingText;
    button.disabled = true;
    startLoadingProgress(button);
    return;
  }
  button.textContent = button.dataset.originalText || button.textContent;
  button.disabled = false;
  stopLoadingProgress();
}

function startLoadingProgress(button) {
  loadingProgressState.activeCount += 1;
  const nextLabel = loadingLabelMap[button?.id] || "节点处理中";

  if (loadingProgressLabel) {
    loadingProgressLabel.textContent = nextLabel;
  }

  if (loadingProgressState.activeCount > 1) {
    return;
  }

  loadingProgressState.value = 2;
  syncLoadingProgress();
  if (loadingProgress) {
    loadingProgress.hidden = false;
  }

  loadingProgressState.timer = window.setInterval(() => {
    const currentValue = loadingProgressState.value;
    if (currentValue >= 92) return;

    const increment =
      currentValue < 18 ? 2 :
      currentValue < 36 ? 3 :
      currentValue < 55 ? 2 :
      currentValue < 72 ? 1.5 :
      currentValue < 84 ? 1 :
      0.5;
    loadingProgressState.value = Math.min(92, currentValue + increment);
    syncLoadingProgress();
  }, 420);
}

function stopLoadingProgress() {
  loadingProgressState.activeCount = Math.max(0, loadingProgressState.activeCount - 1);
  if (loadingProgressState.activeCount > 0) {
    return;
  }

  if (loadingProgressState.timer) {
    window.clearInterval(loadingProgressState.timer);
    loadingProgressState.timer = null;
  }

  loadingProgressState.value = 100;
  syncLoadingProgress();

  window.setTimeout(() => {
    if (loadingProgressState.activeCount > 0) return;
    loadingProgressState.value = 0;
    syncLoadingProgress();
    if (loadingProgress) {
      loadingProgress.hidden = true;
    }
  }, 260);
}

function syncLoadingProgress() {
  const progressValue = Math.max(0, Math.min(100, Math.round(loadingProgressState.value)));
  if (loadingProgressFill) {
    loadingProgressFill.style.setProperty("--progress-angle", `${(progressValue / 100) * 360}deg`);
  }
  if (loadingProgressPercent) {
    loadingProgressPercent.textContent = `${progressValue}%`;
  }
}

function waitForStepTransition() {
  return new Promise((resolve) => {
    window.setTimeout(resolve, STEP_TRANSITION_DELAY_MS);
  });
}

async function apiRequest(path, options = {}) {
  try {
    const response = await fetch(`${API_BASE}${path}`, {
      headers: {
        "Content-Type": "application/json",
        ...(options.headers || {}),
      },
      ...options,
    });

    if (!response.ok) {
      const message = await response.text();
      throw new Error(message || `请求失败：${response.status}`);
    }

    return response.json();
  } catch (error) {
    if (error instanceof TypeError) {
      throw new Error(
        `无法连接到后端接口 ${API_BASE}${path}。当前 4173 只是静态页面，真实内容依赖 8010 API，请先启动后端。原始错误：${error.message}`
      );
    }
    throw error;
  }
}

function buildStep1Payload() {
  return {
    projectName: step1Fields.projectName.value.trim(),
    coreIdea: step1Fields.coreIdea.value.trim(),
    commercialDirective: step1Fields.commercialDirective.value.trim(),
    storyBibleInput: step1Fields.storyBible.value.trim(),
  };
}

async function fetchProjectState(projectId) {
  if (!projectId) {
    throw new Error("projectId 不能为空，无法读取项目状态。");
  }
  const encodedProjectId = encodeURIComponent(projectId);
  const result = await apiRequest(`/api/project/${encodedProjectId}/state`);
  return result.data || {};
}

function applyProjectState(stateView = {}) {
  if (!stateView || typeof stateView !== "object") return;

  appState.projectId = stateView.projectId || appState.projectId;
  appState.selectedProposalId = stateView.step2?.selected_proposal_id || null;
  appState.selectedProposalText = stateView.step2?.selected_proposal_text || "";

  if (stateView.step1) {
    step1Fields.projectName.value = stateView.step1.projectName || step1Fields.projectName.value;
    step1Fields.coreIdea.value = stateView.step1.coreIdea || step1Fields.coreIdea.value;
    step1Fields.commercialDirective.value = stateView.step1.commercialDirective || step1Fields.commercialDirective.value;
    step1Fields.storyBible.value = stateView.step1.storyBibleInput || step1Fields.storyBible.value;
  }

  renderProposalCards(stateView.step2?.proposal_options || []);
  renderWorldContent(stateView.step3 || {});
  renderCharacterList(stateView.step4?.characters || []);
  renderBenchmarkContent(stateView.step5?.benchmarkCases || "");
  renderScriptContent(stateView.step6 || {});
}

function loadStep1History() {
  try {
    const history = JSON.parse(localStorage.getItem(STEP1_HISTORY_KEY) || "{}");
    return {
      projectName: Array.isArray(history.projectName) ? history.projectName : [],
      coreIdea: Array.isArray(history.coreIdea) ? history.coreIdea : [],
      commercialDirective: Array.isArray(history.commercialDirective) ? history.commercialDirective : [],
      storyBible: Array.isArray(history.storyBible) ? history.storyBible : [],
    };
  } catch {
    return {
      projectName: [],
      coreIdea: [],
      commercialDirective: [],
      storyBible: [],
    };
  }
}

function saveStep1History(payload) {
  const currentHistory = loadStep1History();
  const nextHistory = {
    projectName: mergeHistoryItem(currentHistory.projectName, payload.projectName),
    coreIdea: mergeHistoryItem(currentHistory.coreIdea, payload.coreIdea),
    commercialDirective: mergeHistoryItem(currentHistory.commercialDirective, payload.commercialDirective),
    storyBible: mergeHistoryItem(currentHistory.storyBible, payload.storyBibleInput),
  };
  localStorage.setItem(STEP1_HISTORY_KEY, JSON.stringify(nextHistory));
  renderStep1HistoryOptions(nextHistory);
}

function mergeHistoryItem(historyList, nextValue) {
  if (!nextValue) return historyList.slice(0, 8);
  const normalizedValue = nextValue.trim();
  if (!normalizedValue) return historyList.slice(0, 8);

  return [normalizedValue, ...historyList.filter((item) => item !== normalizedValue)].slice(0, 8);
}

function renderStep1HistoryOptions(history = loadStep1History()) {
  Object.entries(step1HistorySelects).forEach(([key, select]) => {
    if (!select) return;

    const items = history[key] || [];
    const firstOptionLabel = select.dataset.placeholder || select.options[0]?.textContent || "选择历史记录";
    select.innerHTML = `<option value="">${escapeHtml(firstOptionLabel)}</option>`;

    items.forEach((item) => {
      const option = document.createElement("option");
      option.value = item;
      option.textContent = item.length > 42 ? `${item.slice(0, 42)}...` : item;
      select.appendChild(option);
    });

    select.hidden = items.length === 0;
  });
}

function bindStep1HistorySelects() {
  Object.entries(step1HistorySelects).forEach(([key, select]) => {
    const field = step1Fields[key];
    if (!select || !field) return;

    select.addEventListener("change", () => {
      if (!select.value) return;
      field.value = select.value;
    });
  });
}

function renderProposalCards(proposalOptions = []) {
  if (!proposalOptions.length) {
    proposalStack.innerHTML = `
      <article class="proposal-card">
        <div class="proposal-meta"><span>暂无方案</span></div>
        <h3>等待生成</h3>
        <p class="proposal-hook">请先完成第 1 页提交。</p>
      </article>
    `;
    return;
  }

  proposalStack.innerHTML = proposalOptions
    .map((proposal, index) => {
      const isSelected = appState.selectedProposalId === proposal.id;
      const highlights = (proposal.highlights || [])
        .map((item) => `<li>${escapeHtml(item)}</li>`)
        .join("");
      const title = escapeHtml(proposal.title || `方案 ${proposal.id.toUpperCase()}`);
      const platform = escapeHtml(proposal.platform || "");
      const heading = platform ? `${title}【${platform}】` : title;

      return `
        <article class="proposal-card ${isSelected ? "selected" : ""}" data-select-card="${proposal.id}" data-raw-text="${encodeURIComponent(proposal.raw_text || "")}">
          <div class="proposal-meta">
            <span>方案 ${index + 1}</span>
          </div>
          <h3>${heading}</h3>
          <p class="proposal-hook">${escapeHtml(proposal.hook || "等待提案生成")}</p>
          <div class="proposal-grid">
            <div>
              <h4>核心卖点</h4>
              <ul>${highlights || "<li>待生成</li>"}</ul>
            </div>
            <div>
              <h4>平台适配</h4>
              <p>${escapeHtml(proposal.platform || "待生成")}</p>
              <h4>受众定位</h4>
              <p>${escapeHtml(proposal.audience || "待生成")}</p>
            </div>
          </div>
          ${isSelected ? '<div class="selected-indicator">✓</div>' : ""}
        </article>
      `;
    })
    .join("");
}

async function handleStep1Generate() {
  const payload = buildStep1Payload();
  if (!payload.projectName || !payload.coreIdea) {
    setFeedback(step1Feedback, "请先填写项目代号和核心灵感。", "error");
    return;
  }

  try {
    saveStep1History(payload);
    setFeedback(step1Feedback, "正在创建项目并生成商业方案...", "success");
    setButtonLoading(step1GenerateBtn, true, "生成中...");

    const initResult = await apiRequest("/api/project/init", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    appState.projectId = initResult.projectId;

    const proposalsResult = await apiRequest("/api/proposals/generate", {
      method: "POST",
      body: JSON.stringify({ projectId: appState.projectId }),
    });
    const syncedState = await fetchProjectState(proposalsResult.projectId || appState.projectId);
    applyProjectState(syncedState);
    setFeedback(step1Feedback, "商业方案已生成。", "success");
    setFeedback(step2Feedback, "请选择一套方案后继续。");
    goToStep(2);
  } catch (error) {
    setFeedback(step1Feedback, `生成失败：${readErrorMessage(error)}`, "error");
  } finally {
    setButtonLoading(step1GenerateBtn, false);
  }
}

async function handleStep2Regenerate() {
  if (!appState.projectId) {
    setFeedback(step2Feedback, "请先在第 1 页完成项目初始化。", "error");
    return;
  }

  try {
    setFeedback(step2Feedback, "正在重新生成商业方案...", "success");
    setButtonLoading(step2RegenerateBtn, true, "生成中...");
    const result = await apiRequest("/api/proposals/generate", {
      method: "POST",
      body: JSON.stringify({ projectId: appState.projectId }),
    });
    const syncedState = await fetchProjectState(result.projectId || appState.projectId);
    applyProjectState(syncedState);
    setFeedback(step2Feedback, "商业方案已更新。", "success");
  } catch (error) {
    setFeedback(step2Feedback, `重新生成失败：${readErrorMessage(error)}`, "error");
  } finally {
    setButtonLoading(step2RegenerateBtn, false);
  }
}

async function handleStep2Confirm() {
  if (!appState.projectId) {
    setFeedback(step2Feedback, "请先在第 1 页完成项目初始化。", "error");
    return;
  }
  if (!appState.selectedProposalText) {
    setFeedback(step2Feedback, "请先选中一个商业方案。", "error");
    return;
  }

  try {
    setFeedback(step2Feedback, "正在确认方案并进入下一步...", "success");
    setButtonLoading(step2ConfirmBtn, true, "提交中...");
    const selectResult = await apiRequest("/api/proposals/select", {
      method: "POST",
      body: JSON.stringify({
        projectId: appState.projectId,
        selectedProposalText: appState.selectedProposalText,
      }),
    });
    const syncedState = await fetchProjectState(selectResult.projectId || appState.projectId);
    applyProjectState(syncedState);
    setFeedback(step2Feedback, "方案已确认。", "success");
    stopLoadingProgress();
    await waitForStepTransition();
    goToStep(3);
  } catch (error) {
    setFeedback(step2Feedback, `确认失败：${readErrorMessage(error)}`, "error");
  } finally {
    setButtonLoading(step2ConfirmBtn, false);
  }
}

async function handleStep3Regenerate() {
  if (!appState.projectId) {
    setFeedback(step3Feedback, "请先完成前两步。", "error");
    return;
  }

  try {
    setFeedback(step3Feedback, "正在重新生成世界观...", "success");
    setButtonLoading(step3RegenerateBtn, true, "生成中...");
    const result = await apiRequest("/api/world/generate", {
      method: "POST",
      body: JSON.stringify({ projectId: appState.projectId }),
    });
    const syncedState = await fetchProjectState(result.projectId || appState.projectId);
    applyProjectState(syncedState);
    setFeedback(step3Feedback, "世界观已更新。", "success");
  } catch (error) {
    setFeedback(step3Feedback, `生成失败：${readErrorMessage(error)}`, "error");
  } finally {
    setButtonLoading(step3RegenerateBtn, false);
  }
}

async function handleStep3Confirm() {
  if (!appState.projectId) {
    setFeedback(step3Feedback, "请先完成前两步。", "error");
    return;
  }

  try {
    setFeedback(step3Feedback, "正在生成人物卡...", "success");
    setButtonLoading(step3ConfirmBtn, true, "生成中...");
    const result = await apiRequest("/api/characters/generate", {
      method: "POST",
      body: JSON.stringify({ projectId: appState.projectId }),
    });
    const syncedState = await fetchProjectState(result.projectId || appState.projectId);
    applyProjectState(syncedState);
    setFeedback(step4Feedback, "人物卡已生成。", "success");
    stopLoadingProgress();
    await waitForStepTransition();
    goToStep(4);
  } catch (error) {
    setFeedback(step3Feedback, `生成人物卡失败：${readErrorMessage(error)}`, "error");
  } finally {
    setButtonLoading(step3ConfirmBtn, false);
  }
}

async function handleStep4Regenerate() {
  if (!appState.projectId) {
    setFeedback(step4Feedback, "请先完成前面步骤。", "error");
    return;
  }

  try {
    setFeedback(step4Feedback, "正在重新生成人物卡...", "success");
    setButtonLoading(step4RegenerateBtn, true, "生成中...");
    const result = await apiRequest("/api/characters/regenerate", {
      method: "POST",
      body: JSON.stringify({ projectId: appState.projectId }),
    });
    const syncedState = await fetchProjectState(result.projectId || appState.projectId);
    applyProjectState(syncedState);
    setFeedback(step4Feedback, "人物卡已更新。", "success");
  } catch (error) {
    setFeedback(step4Feedback, `重新生成失败：${readErrorMessage(error)}`, "error");
  } finally {
    setButtonLoading(step4RegenerateBtn, false);
  }
}

async function handleStep4Confirm() {
  if (!appState.projectId) {
    setFeedback(step4Feedback, "请先完成人物卡生成。", "error");
    return;
  }

  try {
    setFeedback(step4Feedback, "正在生成爆款对标...", "success");
    setButtonLoading(step4ConfirmBtn, true, "生成中...");
    let syncedState = await fetchProjectState(appState.projectId);
    if (!syncedState.step5?.benchmarkCases) {
      const result = await apiRequest("/api/benchmarks/generate", {
        method: "POST",
        body: JSON.stringify({ projectId: appState.projectId }),
      });
      syncedState = await fetchProjectState(result.projectId || appState.projectId);
    }
    applyProjectState(syncedState);
    setFeedback(step5Feedback, "爆款对标已生成。", "success");
    stopLoadingProgress();
    await waitForStepTransition();
    goToStep(5);
  } catch (error) {
    setFeedback(step4Feedback, `生成爆款对标失败：${readErrorMessage(error)}`, "error");
  } finally {
    setButtonLoading(step4ConfirmBtn, false);
  }
}

async function handleStep5Confirm() {
  if (!appState.projectId) {
    setFeedback(step5Feedback, "请先完成爆款对标分析。", "error");
    return;
  }

  try {
    setFeedback(step5Feedback, "正在生成完整剧本...", "success");
    setButtonLoading(step5ConfirmBtn, true, "生成中...");
    let syncedState = await fetchProjectState(appState.projectId);
    if (!syncedState.step6?.scriptText) {
      const result = await apiRequest("/api/script/generate", {
        method: "POST",
        body: JSON.stringify({ projectId: appState.projectId }),
      });
      syncedState = await fetchProjectState(result.projectId || appState.projectId);
    }
    applyProjectState(syncedState);
    setFeedback(step6Feedback, "完整剧本已生成。", "success");
    stopLoadingProgress();
    await waitForStepTransition();
    goToStep(6);
  } catch (error) {
    setFeedback(step5Feedback, `生成完整剧本失败：${readErrorMessage(error)}`, "error");
  } finally {
    setButtonLoading(step5ConfirmBtn, false);
  }
}

function renderWorldContent(step3Data = {}) {
  if (!step3WorldContent) return;
  const worldOutlineHtml = renderWorldOutline(step3Data.worldOutline || "");
  const selectedPlan = formatWorldBlockBody(step3Data.selectedCommercialPlan);
  const deadlocks = formatWorldBlockBody(step3Data.societalDeadlocks);
  const traumas = formatWorldBlockBody(step3Data.traumaProfiles);
  const dynamicBlocks = worldOutlineHtml || `<h3>【世界观框架】</h3><p>等待生成世界观推演内容。</p>`;

  const supportingBlocks = [
    buildWorldTextBlock("【已选商业方案】", selectedPlan),
    buildWorldTextBlock("【社会性死局】", deadlocks),
    buildWorldTextBlock("【创伤原型】", traumas),
  ]
    .filter(Boolean)
    .join("");

  step3WorldContent.innerHTML = `${dynamicBlocks}${supportingBlocks}`;
}

function renderWorldOutline(worldOutline) {
  if (!worldOutline) return "";

  const lines = worldOutline.split("\n");
  const blocks = [];
  let listItems = [];
  let paragraphLines = [];

  const flushList = () => {
    if (!listItems.length) return;
    blocks.push(`<ul>${listItems.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>`);
    listItems = [];
  };

  const flushParagraph = () => {
    if (!paragraphLines.length) return;
    blocks.push(`<p>${escapeHtml(paragraphLines.join(" "))}</p>`);
    paragraphLines = [];
  };

  lines.forEach((rawLine) => {
    const line = rawLine.trim();
    if (!line) {
      flushList();
      flushParagraph();
      return;
    }

    if (/^-{3,}$/.test(line)) {
      flushList();
      flushParagraph();
      return;
    }

    if (/^\|(?:\s*:?-{3,}:?\s*\|)+\s*$/.test(line)) {
      flushList();
      flushParagraph();
      return;
    }

    const cleanedLine = line
      .replace(/^#+\s*/, "")
      .replace(/\*\*/g, "")
      .trim();

    if (!cleanedLine) {
      flushList();
      flushParagraph();
      return;
    }

    const isBracketHeading = /^【[^】]+】$/.test(cleanedLine);
    const isMarkdownHeading = /^(第[一二三四五六七八九十\d]+[集章节幕场：:])/.test(cleanedLine);
    if (isBracketHeading || isMarkdownHeading) {
      flushList();
      flushParagraph();
      blocks.push(`<h3>${escapeHtml(cleanedLine)}</h3>`);
      return;
    }

    const bulletMatch = cleanedLine.match(/^(?:[*\-•]\s+|\d+\.\s+)(.+)$/);
    if (bulletMatch) {
      flushParagraph();
      const item = bulletMatch[1].trim();
      if (item) {
        listItems.push(item);
      }
      return;
    }

    if (cleanedLine.startsWith("|") && cleanedLine.endsWith("|")) {
      flushList();
      const cells = cleanedLine
        .split("|")
        .map((cell) => cell.trim())
        .filter(Boolean);
      if (cells.length) {
        paragraphLines.push(cells.join(" / "));
      }
      return;
    }

    flushList();
    paragraphLines.push(cleanedLine);
  });

  flushList();
  flushParagraph();

  return blocks.join("");
}

function formatWorldBlockBody(value) {
  if (Array.isArray(value)) {
    return value.filter(Boolean).join("\n");
  }
  if (value && typeof value === "object") {
    return Object.entries(value)
      .filter(([, item]) => item)
      .map(([key, item]) => `${key}: ${item}`)
      .join("\n");
  }
  return typeof value === "string" ? value.trim() : "";
}

function buildWorldTextBlock(title, body) {
  if (!body) return "";

  const lines = body
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);

  if (!lines.length) return "";

  const listItems = lines
    .filter((line) => /^[-•\d]/.test(line) || line.includes("：") || line.includes(":"))
    .map((line) => line.replace(/^\s*(?:-|•|\d+\.\s*)/, "").trim());

  if (listItems.length >= 2) {
    return `<h3>${escapeHtml(title)}</h3><ul>${listItems.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>`;
  }

  return `<h3>${escapeHtml(title)}</h3><p>${escapeHtml(lines.join(" "))}</p>`;
}

function renderCharacterList(characters = []) {
  if (!characterList || !characters.length) return;

  Object.keys(characterState).forEach((key) => delete characterState[key]);
  characters.forEach((character, index) => {
    const id = character.id || `character_${index + 1}`;
    characterState[id] = {
      name: character.name || `角色${index + 1}`,
      hairStyle: character.hair_style || character.hairStyle || "",
      hairColor: character.hair_color || character.hairColor || "",
      eyeColor: character.eye_color || character.eyeColor || "",
      marks: character.marks || "",
      heightRatio: character.height_ratio || character.heightRatio || "",
      outfits: character.outfits || [],
    };
  });

  characterList.innerHTML = characters
    .map((character, index) => {
      const id = character.id || `character_${index + 1}`;
      const data = characterState[id];
      const avatarText = (data.name || "角").replace(/（.*?）/g, "").trim().slice(0, 1) || "角";
      const outfits = (data.outfits || [])
        .map(
          (item, outfitIndex) => `
            <div class="wardrobe-item">
              <span class="wardrobe-tag">方案 ${String.fromCharCode(65 + outfitIndex)}</span>
              <p>${escapeHtml(item)}</p>
            </div>
          `
        )
        .join("");

      return `
        <article class="character-card ${index === 0 ? "featured" : ""}" data-character-id="${escapeHtml(id)}">
          <div class="avatar">${escapeHtml(avatarText)}</div>
          <div class="character-main">
            <div class="character-head">
              <div>
                <h3>${escapeHtml(data.name)}</h3>
                <p class="character-subtitle">角色设定图鉴</p>
              </div>
            </div>
            <div class="character-grid">
              <div><strong>发型</strong><span>${escapeHtml(data.hairStyle)}</span></div>
              <div><strong>发色</strong><span>${escapeHtml(data.hairColor)}</span></div>
              <div><strong>瞳色</strong><span>${escapeHtml(data.eyeColor)}</span></div>
              <div><strong>显著伤痕 / 特征</strong><span>${escapeHtml(data.marks)}</span></div>
              <div><strong>身高比例</strong><span>${escapeHtml(data.heightRatio)}</span></div>
            </div>
            <div class="wardrobe-block">
              <strong>服装方案矩阵</strong>
              <div class="wardrobe-cards">
                ${outfits}
              </div>
            </div>
          </div>
        </article>
      `;
    })
    .join("");
}

function renderBenchmarkContent(benchmarkCases = "") {
  if (!step5BenchmarkContent) return;

  const blocks = renderBenchmarkBlocks(benchmarkCases);
  step5BenchmarkContent.innerHTML = blocks || `<h3>【爆款对标】</h3><p>等待人物卡确认后生成爆款对标分析。</p>`;
}

function renderBenchmarkBlocks(benchmarkCases) {
  if (!benchmarkCases) return "";

  const sections = [];
  const matches = [...benchmarkCases.matchAll(/【([^】]+)】：?\s*([\s\S]*?)(?=【[^】]+】|$)/g)];

  if (matches.length) {
    matches.forEach((match) => {
      const title = `【${match[1].trim()}】`;
      const lines = match[2]
        .split("\n")
        .map((line) => line.trim())
        .filter(Boolean)
        .map((line) => line.replace(/^\*+\s*/, ""));

      const listItems = lines
        .filter((line) => /^[-•\d]/.test(line))
        .map((line) => line.replace(/^\s*(?:-|•|\d+\.\s*)/, "").trim());

      if (listItems.length >= 2) {
        sections.push(`<h3>${escapeHtml(title)}</h3><ul>${listItems.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>`);
      } else {
        sections.push(`<h3>${escapeHtml(title)}</h3><p>${escapeHtml(lines.join(" "))}</p>`);
      }
    });
    return sections.join("");
  }

  return `<h3>【爆款对标】</h3><p>${escapeHtml(benchmarkCases)}</p>`;
}

function renderScriptContent(step6Data = {}) {
  if (step6ScriptTitle) {
    const projectLabel = appState.projectId || "完整剧本";
    step6ScriptTitle.textContent = `${projectLabel}_完整剧本.txt`;
  }

  if (step6ScriptText) {
    step6ScriptText.textContent = step6Data.scriptText || "等待生成完整剧本。";
  }

  if (step6SummaryContent) {
    const summaryBlocks = [];
    if (step6Data.rollingSummary) {
      summaryBlocks.push(`<h3>【滚动摘要】</h3><p>${escapeHtml(step6Data.rollingSummary)}</p>`);
    }

    const statusBook = step6Data.statusBook && typeof step6Data.statusBook === "object" ? step6Data.statusBook : {};
    const entries = Object.entries(statusBook).filter(([, value]) => value);
    if (entries.length) {
      summaryBlocks.push(
        `<h3>【状态簿】</h3><ul>${entries
          .map(([key, value]) => `<li>${escapeHtml(`${key}: ${value}`)}</li>`)
          .join("")}</ul>`
      );
    }

    step6SummaryContent.innerHTML = summaryBlocks.length
      ? summaryBlocks.join("")
      : ``;
  }
}

function syncSelectedProposal(card) {
  const allCards = [...document.querySelectorAll("[data-select-card]")];
  allCards.forEach((item) => item.classList.remove("selected"));
  allCards.forEach((item) => {
    const indicator = item.querySelector(".selected-indicator");
    if (indicator) indicator.remove();
  });

  card.classList.add("selected");
  const indicator = document.createElement("div");
  indicator.className = "selected-indicator";
  indicator.textContent = "✓";
  card.appendChild(indicator);

  appState.selectedProposalId = card.dataset.selectCard;
  appState.selectedProposalText = decodeURIComponent(card.dataset.rawText || "");
  setFeedback(step2Feedback, `已选中方案 ${appState.selectedProposalId.toUpperCase()}。`, "success");
}

function escapeHtml(value = "") {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function readErrorMessage(error) {
  if (!(error instanceof Error)) return String(error);

  const message = error.message || "未知错误";
  return message.replace(/^\{"detail":"?/, "").replace(/"?\}$/, "");
}

step1GenerateBtn?.addEventListener("click", handleStep1Generate);
step2RegenerateBtn?.addEventListener("click", handleStep2Regenerate);
step2ConfirmBtn?.addEventListener("click", handleStep2Confirm);
step3RegenerateBtn?.addEventListener("click", handleStep3Regenerate);
step3ConfirmBtn?.addEventListener("click", handleStep3Confirm);
step4RegenerateBtn?.addEventListener("click", handleStep4Regenerate);
step4ConfirmBtn?.addEventListener("click", handleStep4Confirm);
step5ConfirmBtn?.addEventListener("click", handleStep5Confirm);

document.addEventListener("click", (event) => {
  const prev = event.target.closest("[data-prev-step]");
  const card = event.target.closest("[data-select-card]");

  if (prev) {
    goToStep(Number(prev.dataset.prevStep));
  }

  if (card) {
    syncSelectedProposal(card);
  }
});

renderStepper();
renderPanels();
renderStep1HistoryOptions();
bindStep1HistorySelects();
