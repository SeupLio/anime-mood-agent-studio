const form = document.querySelector("#analysis-form");
const feedback = document.querySelector("#feedback");
const archetype = document.querySelector("#archetype");
const samples = document.querySelector("#samples");
const emotionGrid = document.querySelector("#emotion-grid");

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

async function loadExamples() {
  const response = await fetch("/api/examples");
  const data = await response.json();
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

function setMeter(id, value, signed = false) {
  const safe = Math.max(signed ? -1 : 0, Math.min(1, value));
  const width = signed ? ((safe + 1) / 2) * 100 : safe * 100;
  document.querySelector(`#${id}-meter`).style.width = `${width}%`;
  document.querySelector(`#${id}-value`).textContent = safe.toFixed(2);
}

function renderEmotionGrid(vector) {
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
  document.querySelector("#player-reply").textContent = data.agent.player_reply;
  renderList("#ops-actions", data.agent.ops_actions);
  renderList("#trace", data.agent.trace);
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const button = form.querySelector("button[type='submit']");
  button.disabled = true;
  button.textContent = "分析中...";

  try {
    const formData = new FormData(form);
    const response = await fetch("/api/analyze", {
      method: "POST",
      body: formData,
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "分析失败");
    }
    renderResult(await response.json());
  } catch (error) {
    document.querySelector("#player-reply").textContent = error.message;
  } finally {
    button.disabled = false;
    button.textContent = "运行情绪感知 Agent";
  }
});

loadExamples();

