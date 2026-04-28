import { PublicClientApplication } from "@azure/msal-browser";
import {
  CopilotStudioClient,
  ConnectionSettings,
} from "@microsoft/agents-copilotstudio-client";

// ---------------------------------------------------------------------------
// Config from Vite env
// ---------------------------------------------------------------------------
const config = {
  environmentId: import.meta.env.VITE_ENVIRONMENT_ID,
  agentSchema: import.meta.env.VITE_AGENT_SCHEMA,
  tenantId: import.meta.env.VITE_TENANT_ID,
  clientId: import.meta.env.VITE_CLIENT_ID,
  guideUrl: import.meta.env.VITE_GUIDE_URL || "https://microsoft.github.io/enhanced-task-completion/",
};

// ---------------------------------------------------------------------------
// DOM refs
// ---------------------------------------------------------------------------
const messagesEl = document.getElementById("messages");
const welcomeEl = document.getElementById("welcome");
const inputForm = document.getElementById("input-form");
const inputEl = document.getElementById("input");
const sendBtn = document.getElementById("send-btn");
const guideLink = document.getElementById("guide-link");

guideLink.href = config.guideUrl;

// Set scenario links
document.querySelectorAll(".scenario-link").forEach((link) => {
  const path = link.dataset.scenario;
  if (path) link.href = config.guideUrl.replace(/\/$/, "") + path;
  link.target = "_blank";
});

// ---------------------------------------------------------------------------
// Auth (MSAL)
// ---------------------------------------------------------------------------
const msal = new PublicClientApplication({
  auth: {
    clientId: config.clientId,
    authority: `https://login.microsoftonline.com/${config.tenantId}`,
  },
});

await msal.initialize();

const settings = new ConnectionSettings({
  environmentId: config.environmentId,
  agentIdentifier: config.agentSchema,
});

const scopes = [CopilotStudioClient.scopeFromSettings(settings)];

async function getToken() {
  const accounts = msal.getAllAccounts();
  if (accounts.length > 0) {
    try {
      const result = await msal.acquireTokenSilent({ scopes, account: accounts[0] });
      return result.accessToken;
    } catch { /* fall through */ }
  }
  const result = await msal.loginPopup({ scopes });
  return result.accessToken;
}

// ---------------------------------------------------------------------------
// SDK Client
// ---------------------------------------------------------------------------
let client = null;
let conversationId = null;

async function ensureClient() {
  const token = await getToken();
  // Create fresh client each time to ensure fresh token
  client = new CopilotStudioClient(settings, token);
  return client;
}

// ---------------------------------------------------------------------------
// ETC Event Parsing
// ---------------------------------------------------------------------------
function parseToolCall(entity) {
  // Handle both object and string formats
  if (typeof entity === "object" && entity !== null) {
    if (entity.type === "toolCall" || entity.type === "https://schema.org/toolCall") {
      return {
        tool_call_id: entity.tool_call_id || entity.toolCallId,
        tool_name: entity.tool_name || entity.toolName,
        tool_display_name: entity.tool_display_name || entity.toolDisplayName,
        status: entity.status,
        duration_ms: entity.duration_ms || entity.durationMs,
        result: entity.result,
      };
    }
    return null;
  }
  // String format (Python SDK repr)
  const entityStr = String(entity);
  if (!entityStr.includes("type='toolCall'") && !entityStr.includes("toolCall")) return null;
  const result = {};
  for (const key of ["tool_call_id", "tool_name", "tool_display_name", "status", "duration_ms"]) {
    const m = entityStr.match(new RegExp(`${key}='([^']*)'`));
    if (m) result[key] = m[1];
  }
  const rm = entityStr.match(/result='(.+?)'\s*$/);
  if (rm) {
    try {
      const parsed = JSON.parse(rm[1]);
      if (parsed?.content) {
        for (const c of parsed.content) {
          if (c.type === "text") {
            try { result.result = JSON.parse(c.text); } catch { result.result = c.text; }
            break;
          }
        }
      } else {
        result.result = parsed;
      }
    } catch { result.result_raw = rm[1].substring(0, 300); }
  }
  return Object.keys(result).length ? result : null;
}

function parseThought(entity) {
  if (typeof entity === "object" && entity !== null) {
    if (entity.type === "thought" || entity.type === "https://schema.org/thought") {
      return entity.text;
    }
    return null;
  }
  const entityStr = String(entity);
  if (!entityStr.includes("type='thought'") && !entityStr.includes("thought")) return null;
  const m = entityStr.match(/text=['"](.*?)['"](?:\s+reasoned_for_seconds|\s*$)/);
  return m ? m[1] : null;
}

// ---------------------------------------------------------------------------
// Rendering
// ---------------------------------------------------------------------------
function addMessage(role, html, className = "") {
  const div = document.createElement("div");
  div.className = `msg msg-${role} ${className}`.trim();
  div.innerHTML = html;
  messagesEl.appendChild(div);
  scrollToBottom();
  return div;
}

function addTypingIndicator() {
  const div = document.createElement("div");
  div.className = "msg-typing";
  div.id = "typing";
  div.innerHTML = "<span></span><span></span><span></span>";
  messagesEl.appendChild(div);
  scrollToBottom();
}

function removeTypingIndicator() {
  document.getElementById("typing")?.remove();
}

function addToolCall(name, status) {
  const div = document.createElement("div");
  div.className = `msg-tool ${status}`;
  div.innerHTML = `<div class="tool-header">
    <span class="tool-icon">${status === "pending" ? "&#9676;" : "&#10003;"}</span>
    <span class="tool-name">${escapeHtml(name)}</span>
    <span class="tool-status"></span>
  </div>
  <pre class="tool-result"></pre>`;
  div.querySelector(".tool-header").onclick = () => div.classList.toggle("expanded");
  messagesEl.appendChild(div);
  scrollToBottom();
  return div;
}


function addReasoning(thought) {
  const div = document.createElement("div");
  div.className = "msg-reasoning";
  div.textContent = thought;
  div.onclick = () => div.classList.toggle("expanded");
  messagesEl.appendChild(div);
  scrollToBottom();
}

function addNewConvAction() {
  // Remove any existing one first
  document.querySelector(".conv-action")?.remove();
  const div = document.createElement("div");
  div.className = "conv-action";
  div.innerHTML = `<button class="conv-action-btn" onclick="resetConversation()">
    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M12 5v14"/><path d="M5 12h14"/></svg>
    New conversation
  </button>`;
  messagesEl.appendChild(div);
  scrollToBottom();
}

function scrollToBottom() {
  const chat = document.getElementById("chat");
  chat.scrollTop = chat.scrollHeight;
}

function escapeHtml(s) {
  const d = document.createElement("div");
  d.textContent = s;
  return d.innerHTML;
}

// Markdown renderer — handles common patterns from agent responses
function renderMarkdown(text) {
  // Extract and render tables first (before other transforms break the pipes)
  text = text.replace(/((?:^\|.+\|$\n?)+)/gm, (tableBlock) => {
    const rows = tableBlock.trim().split("\n").filter(r => r.trim());
    if (rows.length < 2) return tableBlock;
    // Skip separator row (|---|---|)
    const dataRows = rows.filter(r => !/^\|[\s-:|]+\|$/.test(r));
    if (dataRows.length === 0) return tableBlock;
    const parseRow = (r) => r.split("|").slice(1, -1).map(c => c.trim());
    const headers = parseRow(dataRows[0]);
    const body = dataRows.slice(1).map(parseRow);
    let html = "<table><thead><tr>" + headers.map(h => `<th>${h}</th>`).join("") + "</tr></thead><tbody>";
    for (const row of body) {
      html += "<tr>" + row.map(c => `<td>${c}</td>`).join("") + "</tr>";
    }
    html += "</tbody></table>";
    return html;
  });

  return text
    // Headings
    .replace(/^### (.+)$/gm, "<h3>$1</h3>")
    .replace(/^## (.+)$/gm, "<h2>$1</h2>")
    // Horizontal rules
    .replace(/^---$/gm, "<hr>")
    // Bold
    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
    // Italic
    .replace(/(?<!\*)\*([^*]+)\*(?!\*)/g, "<em>$1</em>")
    // Links
    .replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2" target="_blank">$1</a>')
    // Inline code
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    // Unordered lists (- item)
    .replace(/^- (.+)$/gm, "<li>$1</li>")
    .replace(/((?:<li>.*<\/li>\n?)+)/g, "<ul>$1</ul>")
    // Ordered lists (1. item)
    .replace(/^\d+\. (.+)$/gm, "<li>$1</li>")
    // Blockquotes
    .replace(/^> (.+)$/gm, "<blockquote>$1</blockquote>")
    // Line breaks (but not after block elements)
    .replace(/\n(?!<)/g, "<br>");
}

// ---------------------------------------------------------------------------
// Send message
// ---------------------------------------------------------------------------
let sending = false;

async function sendMessage(text) {
  if (!text.trim() || sending) return;
  sending = true;
  inputEl.disabled = true;
  sendBtn.disabled = true;

  // Hide scenarios, remove old new-conv action
  welcomeEl.classList.add("hidden");
  document.querySelector(".conv-action")?.remove();

  // Show user message
  addMessage("user", escapeHtml(text));

  // Show typing
  addTypingIndicator();

  const toolElements = new Map(); // tool_call_id -> DOM element
  let typingRemoved = false;

  function ensureTypingRemoved() {
    if (!typingRemoved) { removeTypingIndicator(); typingRemoved = true; }
  }

  try {
    const c = await ensureClient();

    // Use streaming API to get typing events with ETC metadata in real-time
    let activityStream;
    if (conversationId) {
      activityStream = c.sendActivityStreaming(
        { type: "message", text },
        conversationId
      );
    } else {
      // Start conversation first
      for await (const a of c.startConversationStreaming(true)) {
        if (a.conversation?.id) conversationId = a.conversation.id;
      }
      activityStream = c.sendActivityStreaming(
        { type: "message", text },
        conversationId
      );
    }

    for await (const activity of activityStream) {
      if (!conversationId && activity.conversation?.id) {
        conversationId = activity.conversation.id;
      }

      console.log("[activity]", activity.type, JSON.stringify({
        text: activity.text?.substring(0, 80),
        entities: activity.entities,
        channelData: activity.channelData,
      }));

      const entities = activity.entities || [];
      const channelData = activity.channelData || {};
      const streamType = channelData.streamType || "";

      // Process entities on ANY activity type (thoughts/tools can arrive on typing after message)
      for (const entity of entities) {
        // Reasoning
        const thought = parseThought(entity);
        if (thought) {
          ensureTypingRemoved();
          addReasoning(thought);
        }

        // Tool calls
        const tc = parseToolCall(entity);
        if (tc) {
          ensureTypingRemoved();
          const toolName = tc.tool_display_name || tc.tool_name || "tool";
          const status = tc.status || "";

          if (status === "started") {
            const el = addToolCall(toolName, "pending");
            if (tc.tool_call_id) toolElements.set(tc.tool_call_id, el);
          } else if (status === "completed" || status === "complete") {
            const el = toolElements.get(tc.tool_call_id);
            if (el) {
              el.className = "msg-tool done";
              el.querySelector(".tool-icon").textContent = "\u2713";
              const dur = tc.duration_ms || tc.durationMs;
              el.querySelector(".tool-status").textContent = dur ? `${(dur / 1000).toFixed(1)}s` : "";
              // Populate result
              const result = tc.result || tc.result_raw;
              if (result) {
                const hidden = new Set(["conversation_id", "id", "botId", "bot_id", "agent_id", "is_error"]);
                let text;
                if (typeof result === "object" && result !== null) {
                  const cleaned = Object.fromEntries(Object.entries(result).filter(([k]) => !hidden.has(k)));
                  text = Object.keys(cleaned).length ? JSON.stringify(cleaned, null, 2) : "";
                } else {
                  text = String(result);
                }
                if (text) el.querySelector(".tool-result").textContent = text;
              }
            }
          }
        }
      }

      // Render messages
      if (activity.type === "message" && activity.text) {
        if (streamType === "final" || !streamType) {
          ensureTypingRemoved();
          addMessage("bot", renderMarkdown(activity.text));
        }
      } else if (activity.type === "endOfConversation") {
        break;
      }
    }

    ensureTypingRemoved();
    addNewConvAction();
  } catch (err) {
    ensureTypingRemoved();
    addMessage("bot", `<span style="color:#D83B73">Error: ${escapeHtml(err.message)}</span>`);
    addNewConvAction();
    console.error(err);
  }

  sending = false;
  inputEl.disabled = false;
  sendBtn.disabled = false;
  inputEl.focus();
}

// ---------------------------------------------------------------------------
// Event handlers
// ---------------------------------------------------------------------------
inputEl.addEventListener("input", () => {
  sendBtn.disabled = !inputEl.value.trim();
});

inputForm.addEventListener("submit", (e) => {
  e.preventDefault();
  const text = inputEl.value.trim();
  if (!text) return;
  inputEl.value = "";
  sendBtn.disabled = true;
  sendMessage(text);
});

// Scenario cards
document.querySelectorAll(".scenario-card").forEach((card) => {
  card.addEventListener("click", (e) => {
    if (e.target.classList.contains("scenario-link")) return;
    const prompt = card.dataset.prompt;
    if (prompt) {
      inputEl.value = prompt;
      sendBtn.disabled = false;
      inputEl.focus();
    }
  });
});

// New conversation — triggered by inline button
function resetConversation() {
  conversationId = null;
  client = null;
  messagesEl.innerHTML = "";
  welcomeEl.classList.remove("hidden");
  inputEl.value = "";
  sendBtn.disabled = true;
  inputEl.focus();
}

// Expose for inline onclick
window.resetConversation = resetConversation;
