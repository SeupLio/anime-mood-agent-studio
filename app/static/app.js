const apiBase = window.location.protocol === "file:" ? "http://127.0.0.1:8000" : "";

const emotionLabels = {
  joy: "喜悦",
  sadness: "悲伤",
  anger: "愤怒",
  fear: "恐惧",
  trust: "信任",
  surprise: "惊讶",
  anticipation: "期待",
  disgust: "厌恶",
  neutral: "中性",
};

const referenceAssets = Array.from({ length: 7 }, (_, index) => `/static/assets/reference_${index + 1}.jpg`);

function apiUrl(path) {
  return `${apiBase}${path}`;
}

async function requestJson(path, options = {}) {
  let response;
  try {
    response = await fetch(apiUrl(path), options);
  } catch (error) {
    throw new Error("无法连接后端服务，请确认 FastAPI 已启动。");
  }

  if (!response.ok) {
    let detail = `HTTP ${response.status}`;
    try {
      const payload = await response.json();
      detail = payload.detail || detail;
    } catch (error) {
      detail = `${detail}`;
    }
    throw new Error(detail);
  }
  return response.json();
}

function setMeter(id, value, signed = false) {
  const safe = Math.max(signed ? -1 : 0, Math.min(1, value));
  const width = signed ? ((safe + 1) / 2) * 100 : safe * 100;
  document.querySelector(`#${id}-meter`).style.width = `${width}%`;
  document.querySelector(`#${id}-value`).textContent = safe.toFixed(2);
}

function renderEmotionGrid(vector) {
  const emotionGrid = document.querySelector("#emotion-grid");
  emotionGrid.innerHTML = "";
  Object.entries(vector)
    .sort((a, b) => b[1] - a[1])
    .forEach(([emotion, score]) => {
      const tile = document.createElement("div");
      tile.className = "emotion-tile";
      tile.innerHTML = `<b>${emotionLabels[emotion] || emotion}</b><span>${(score * 100).toFixed(1)}%</span>`;
      emotionGrid.appendChild(tile);
    });
}

function renderList(selector, items) {
  const root = document.querySelector(selector);
  root.innerHTML = "";
  items.forEach((item) => {
    const li = document.createElement("li");
    li.textContent = typeof item === "string" ? item : `${item.tool}: ${item.observation}`;
    root.appendChild(li);
  });
}

function renderResult(data) {
  document.querySelector("#primary-emotion").textContent =
    emotionLabels[data.fusion.primary_emotion] || data.fusion.primary_emotion;
  const risk = document.querySelector("#risk-level");
  risk.textContent = `risk: ${data.agent.risk_level}`;
  risk.className = `risk-pill ${data.agent.risk_level}`;
  setMeter("valence", data.fusion.valence, true);
  setMeter("arousal", data.fusion.arousal);
  setMeter("confidence", data.fusion.confidence);
  renderEmotionGrid(data.fusion.vector);
  renderSemantic(data.semantic);
  document.querySelector("#player-reply").textContent = data.agent.player_reply;
  renderList("#ops-actions", data.agent.ops_actions);
  renderList("#trace", data.agent.trace);
}

function renderSemantic(semantic) {
  const root = document.querySelector("#semantic-band");
  if (!semantic) {
    root.innerHTML = `<p class="eyebrow">Semantic Alignment</p><p>当前样本未同时提供文本和图片。</p>`;
    return;
  }
  root.innerHTML = `
    <p class="eyebrow">Semantic Alignment</p>
    <div class="semantic-grid">
      <b>${semantic.label}</b>
      <span>一致性 ${(semantic.consistency_score * 100).toFixed(1)}%</span>
      <span>反差 ${(semantic.contrast_score * 100).toFixed(1)}%</span>
    </div>
    <p>${semantic.evidence.join("；")}</p>
  `;
}

async function loadExamples() {
  const samples = document.querySelector("#samples");
  const feedback = document.querySelector("#feedback");
  const archetype = document.querySelector("#archetype");
  const data = await requestJson("/api/examples");
  samples.innerHTML = "";
  data.items.forEach((item) => {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = item.title;
    button.addEventListener("click", () => {
      feedback.value = item.text;
      archetype.value = item.archetype;
    });
    samples.appendChild(button);
  });
}

function loadReferenceGallery() {
  const root = document.querySelector("#reference-gallery");
  root.innerHTML = "";
  referenceAssets.forEach((asset, index) => {
    const button = document.createElement("button");
    button.type = "button";
    button.style.backgroundImage = `url("${asset}")`;
    button.title = `参考图 ${index + 1}`;
    button.addEventListener("click", () => selectReferenceImage(asset, index + 1));
    root.appendChild(button);
  });
}

async function selectReferenceImage(asset, index) {
  const imageInput = document.querySelector("#image");
  const blob = await fetch(asset).then((response) => response.blob());
  const file = new File([blob], `reference_${index}.jpg`, { type: "image/jpeg" });
  const transfer = new DataTransfer();
  transfer.items.add(file);
  imageInput.files = transfer.files;
}

async function loadModelStatus() {
  const status = await requestJson("/api/model-status");
  const root = document.querySelector("#model-status");
  root.innerHTML = `
    <span>Text: ${status.text_emotion_backend}</span>
    <span>DeepSeek: ${status.deepseek_configured ? status.deepseek_model : "fallback"}</span>
    <span>Vision: ${status.multimodal_backend}</span>
    <span>RAG: ${status.rag_backend}</span>
  `;
}

function initTabs() {
  document.querySelectorAll(".tab").forEach((button) => {
    button.addEventListener("click", () => {
      document.querySelectorAll(".tab").forEach((item) => item.classList.remove("active"));
      document.querySelectorAll(".tab-page").forEach((item) => item.classList.remove("active"));
      button.classList.add("active");
      document.querySelector(`#tab-${button.dataset.tab}`).classList.add("active");
    });
  });
}

async function loadDashboard() {
  const version = document.querySelector("#version-filter").value;
  const event = document.querySelector("#event-filter").value;
  const params = new URLSearchParams();
  if (version) params.set("version", version);
  if (event) params.set("event_name", event);
  const data = await requestJson(`/api/dashboard?${params.toString()}`);
  fillFilters(data);
  renderDashboard(data);
}

function fillFilters(data) {
  fillSelect("#version-filter", data.versions, "全部版本");
  fillSelect("#event-filter", data.events, "全部活动");
}

function fillSelect(selector, values, label) {
  const select = document.querySelector(selector);
  const current = select.value;
  select.innerHTML = `<option value="">${label}</option>`;
  values.forEach((value) => {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = value;
    select.appendChild(option);
  });
  select.value = values.includes(current) ? current : "";
}

function renderDashboard(data) {
  const stats = document.querySelector("#dashboard-stats");
  stats.innerHTML = "";
  [
    ["样本量", data.total],
    ["高风险", (data.risk_counts["高"] || 0) + (data.risk_counts["严重"] || 0)],
    ["主要情绪", topKey(data.emotion_counts)],
    ["聚类数", data.clusters.length],
  ].forEach(([label, value]) => {
    const item = document.createElement("div");
    item.className = "stat";
    item.innerHTML = `<span>${label}</span><b>${value}</b>`;
    stats.appendChild(item);
  });

  const maxTotal = Math.max(...data.trend.map((item) => item.total), 1);
  document.querySelector("#trend-list").innerHTML = data.trend
    .slice(-12)
    .map(
      (item) => `
        <div class="trend-row">
          <span>${item.date.slice(5)}</span>
          <div><i style="width:${(item.total / maxTotal) * 100}%"></i></div>
          <b>${item.total}</b>
        </div>
      `
    )
    .join("");

  document.querySelector("#cluster-list").innerHTML = data.clusters
    .map(
      (item) => `
        <article class="cluster">
          <div><b>${item.name}</b><span>${item.size} 条 · ${item.risk_level}</span></div>
          <p>${item.top_terms.join(" / ") || "无标签"}</p>
        </article>
      `
    )
    .join("");

  document.querySelector("#risk-list").innerHTML = data.risk_samples
    .map(
      (item) => `
        <article class="risk-item">
          <b>${item.risk_level}</b>
          <div>
            <span>${item.feedback_id} · ${item.version} · ${item.event_name}</span>
            <p>${item.text}</p>
            <em>${item.recommended_action}</em>
          </div>
        </article>
      `
    )
    .join("");
}

async function loadEvaluation() {
  const data = await requestJson("/api/evaluation");
  renderEvaluation(data);
}

function renderEvaluation(data) {
  const metrics = document.querySelector("#eval-metrics");
  metrics.innerHTML = "";
  data.metrics.forEach((metric) => {
    const item = document.createElement("div");
    item.className = "stat";
    item.innerHTML = `<span>${metric.name}</span><b>${metric.value}</b><em>support ${metric.support}</em>`;
    metrics.appendChild(item);
  });

  document.querySelector("#confusion-list").innerHTML = data.confusion
    .map(
      (item) => `
        <article class="cluster">
          <div><b>${item.expected} -> ${item.predicted}</b><span>${item.count} 条</span></div>
        </article>
      `
    )
    .join("");

  document.querySelector("#hard-list").innerHTML = data.hard_examples
    .map(
      (item) => `
        <article class="risk-item">
          <b>${item.expected}</b>
          <div>
            <span>${item.feedback_id} · pred ${item.predicted} · conf ${item.confidence}</span>
            <p>${item.text}</p>
          </div>
        </article>
      `
    )
    .join("");

  renderList("#eval-recommendations", data.recommendations);
}

function topKey(values) {
  const entries = Object.entries(values);
  if (!entries.length) return "-";
  return entries.sort((a, b) => b[1] - a[1])[0][0];
}

async function submitAnalysis(event) {
  event.preventDefault();
  const button = event.currentTarget.querySelector("button[type='submit']");
  button.disabled = true;
  button.textContent = "分析中...";
  try {
    const data = await requestJson("/api/analyze", {
      method: "POST",
      body: new FormData(event.currentTarget),
    });
    renderResult(data);
  } catch (error) {
    document.querySelector("#player-reply").textContent = error.message;
  } finally {
    button.disabled = false;
    button.textContent = "运行情绪感知 Agent";
  }
}

async function submitRag(event) {
  event.preventDefault();
  const data = await requestJson("/api/rag", {
    method: "POST",
    body: new FormData(event.currentTarget),
  });
  document.querySelector("#rag-answer").textContent = data.answer;
  document.querySelector("#citation-grid").innerHTML = data.citations
    .map(
      (item) => `
        <article class="citation">
          <b>${item.section}</b>
          <span>${item.source_doc} · score ${item.score}</span>
          <p>${item.content}</p>
        </article>
      `
    )
    .join("");
}

async function submitVideo(event) {
  event.preventDefault();
  const button = event.currentTarget.querySelector("button[type='submit']");
  button.disabled = true;
  button.textContent = "生成中...";
  try {
    const data = await requestJson("/api/video", {
      method: "POST",
      body: new FormData(event.currentTarget),
    });
    document.querySelector("#video-summary").innerHTML = data.summary.map((item) => `<span>${item}</span>`).join("");
    document.querySelector("#video-timeline").innerHTML = data.frames
      .map(
        (item) => `
          <div class="frame-dot">
            <b>${item.frame_index + 1}</b>
            <span>${emotionLabels[item.image.vector && topKey(item.image.vector)] || topKey(item.image.vector)}</span>
            <i style="height:${Math.max(18, item.image.arousal * 92)}px"></i>
          </div>
        `
      )
      .join("");
  } catch (error) {
    document.querySelector("#video-summary").textContent = error.message;
  } finally {
    button.disabled = false;
    button.textContent = "生成时间线";
  }
}

document.querySelector("#analysis-form").addEventListener("submit", submitAnalysis);
document.querySelector("#rag-form").addEventListener("submit", submitRag);
document.querySelector("#video-form").addEventListener("submit", submitVideo);
document.querySelector("#run-eval").addEventListener("click", loadEvaluation);
document.querySelector("#version-filter").addEventListener("change", loadDashboard);
document.querySelector("#event-filter").addEventListener("change", loadDashboard);

initTabs();
loadReferenceGallery();
loadExamples().catch((error) => (document.querySelector("#player-reply").textContent = error.message));
loadModelStatus().catch(() => {});
loadDashboard().catch(() => {});
loadEvaluation().catch(() => {});
