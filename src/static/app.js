// ==============================================================================
// 🚀 FRONTEND CLIENT: Real-time ReAct Agent with WebSocket Streaming Trace
// ==============================================================================

document.addEventListener("DOMContentLoaded", () => {
    const chatForm = document.getElementById("chatForm");
    const userInput = document.getElementById("userInput");
    const btnSend = document.getElementById("btnSend");
    const chatMessages = document.getElementById("chatMessages");
    const memoryStatusBadge = document.getElementById("memoryStatusBadge");
    
    // Trace elements
    const traceTimeline = document.getElementById("traceTimeline");
    const metricLatency = document.getElementById("metricLatency");
    const metricSteps = document.getElementById("metricSteps");
    const metricTools = document.getElementById("metricTools");
    
    // Tabs
    const tabLive = document.getElementById("tabLive");
    const tabHistory = document.getElementById("tabHistory");
    const historyTraceView = document.getElementById("historyTraceView");
    const historyContent = document.getElementById("historyContent");
    const btnReloadHistory = document.getElementById("btnReloadHistory");
    
    // Modal
    const btnViewMemory = document.getElementById("btnViewMemory");
    const btnClearMemory = document.getElementById("btnClearMemory");
    const memoryModal = document.getElementById("memoryModal");
    const btnCloseModal = document.getElementById("btnCloseModal");
    const modalSummaryText = document.getElementById("modalSummaryText");
    const modalTurnsContainer = document.getElementById("modalTurnsContainer");

    // Real-time State
    let socket = null;
    let toolCount = 0;
    let currentTypingId = null;

    // Initialize WebSocket with auto-reconnect
    function initWebSocket() {
        const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
        const wsUrl = `${protocol}//${window.location.host}/ws/chat`;
        socket = new WebSocket(wsUrl);

        socket.onopen = () => {
            console.log("⚡ [WebSocket Connected]: Sẵn sàng truyền luồng suy luận Real-time!");
        };

        socket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                handleRealtimeEvent(data);
            } catch (err) {
                console.error("Lỗi parse WebSocket event:", err);
            }
        };

        socket.onclose = () => {
            console.log("⚠️ [WebSocket Closed]: Đang kết nối lại sau 2 giây...");
            setTimeout(initWebSocket, 2000);
        };

        socket.onerror = (err) => {
            console.error("WebSocket error:", err);
        };
    }

    initWebSocket();

    // Auto-expand textarea
    userInput.addEventListener("input", () => {
        userInput.style.height = "auto";
        userInput.style.height = Math.min(userInput.scrollHeight, 120) + "px";
    });

    // Enter to send (Shift+Enter for newline)
    userInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            chatForm.dispatchEvent(new Event("submit"));
        }
    });

    // Quick chips
    document.querySelectorAll(".chip").forEach(chip => {
        chip.addEventListener("click", () => {
            userInput.value = chip.getAttribute("data-prompt");
            userInput.focus();
            chatForm.dispatchEvent(new Event("submit"));
        });
    });

    // Submit handler
    chatForm.addEventListener("submit", (e) => {
        e.preventDefault();
        const text = userInput.value.trim();
        if (!text) return;

        // 1. Render User Message on Left
        appendMessage("user", text);
        userInput.value = "";
        userInput.style.height = "auto";
        btnSend.disabled = true;

        // 2. Prepare Right Panel for Live Stream
        tabLive.click();
        traceTimeline.innerHTML = "";
        toolCount = 0;
        metricLatency.textContent = "... ms";
        metricSteps.textContent = "0 steps";
        metricTools.textContent = "0 tools";

        // 3. Show Typing Indicator
        currentTypingId = showTypingIndicator();

        // 4. Send via WebSocket if open, else fallback HTTP POST
        if (socket && socket.readyState === WebSocket.OPEN) {
            socket.send(JSON.stringify({ message: text }));
        } else {
            fallbackHttpChat(text);
        }
    });

    // Fallback HTTP POST
    async function fallbackHttpChat(text) {
        try {
            const res = await fetch("/api/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message: text })
            });
            const data = await res.json();
            removeTypingIndicator(currentTypingId);
            btnSend.disabled = false;

            if (res.ok) {
                appendMessage("agent", data.reply);
                if (data.memory) updateMemoryUI(data.memory);
                renderAllTraces(data.traces, data.total_latency_ms);
            } else {
                appendMessage("agent", "❌ Lỗi: " + (data.error || "Không kết nối được server"));
            }
        } catch (err) {
            removeTypingIndicator(currentTypingId);
            btnSend.disabled = false;
            appendMessage("agent", "❌ Lỗi mạng: " + err.message);
        }
    }

    // ==============================================================================
    // ⚡ XỬ LÝ SỰ KIỆN SUY LUẬN REAL-TIME (REAL-TIME EVENT HANDLER)
    // ==============================================================================
    function handleRealtimeEvent(data) {
        const type = data.type;

        // 1. GUARDRAIL BLOCKED
        if (type === "guardrail_blocked") {
            removeTypingIndicator(currentTypingId);
            btnSend.disabled = false;
            const item = data.data || {};
            appendMessage("agent", item.output || "Yêu cầu bị từ chối.");

            const card = document.createElement("div");
            card.className = "step-card";
            card.innerHTML = `
                <div class="step-header">
                    <span class="step-badge" style="background: rgba(244, 63, 94, 0.2); border: 1px solid rgba(244, 63, 94, 0.5); color: #FDA4AF;">🛡️ Step 1: Guardrail Blocked</span>
                    <span class="step-latency">⏱️ ${item.latency_ms || 1.2} ms</span>
                </div>
                <div class="thought-box" style="border-left-color: var(--rose); background: rgba(244, 63, 94, 0.08);">
                    <div class="thought-header" style="color: #FDA4AF;">🧠 Thought:</div>
                    <div class="thought-content">${escapeHtml(item.thought || "")}</div>
                </div>
                <div class="action-box" style="border-left-color: var(--rose); background: rgba(244, 63, 94, 0.08);">
                    <div class="action-header" style="color: #FDA4AF;">
                        <span>🛡️ Security Intercept:</span>
                        <span class="tool-name-badge" style="background: #881337; color: #FECDD3;">VIOLATION_DETECTED</span>
                    </div>
                    <pre class="json-code">${JSON.stringify(item.arguments || {}, null, 2)}</pre>
                </div>
            `;
            traceTimeline.appendChild(card);
            traceTimeline.scrollTop = traceTimeline.scrollHeight;
            return;
        }

        // 2. THOUGHT EMITTED
        if (type === "thought") {
            const step = data.step || 1;
            metricSteps.textContent = step + " steps";

            // Lấy hoặc tạo Card cho Step này
            let card = document.getElementById(`step-card-${step}`);
            if (!card) {
                // Tắt pulse của các card cũ
                document.querySelectorAll(".step-card").forEach(c => c.classList.remove("live-pulse"));

                card = document.createElement("div");
                card.id = `step-card-${step}`;
                card.className = "step-card live-pulse";
                card.innerHTML = `
                    <div class="step-header">
                        <span class="step-badge running">⚡ Step ${step}: ReAct Loop</span>
                        <span class="step-latency live-clock">Đang xử lý...</span>
                    </div>
                    <div class="step-body"></div>
                `;
                traceTimeline.appendChild(card);
            }

            const body = card.querySelector(".step-body");
            const thoughtHtml = `
                <div class="thought-box">
                    <div class="thought-header">🧠 Thought (Suy luận):</div>
                    <div class="thought-content">${escapeHtml(data.thought || "")}</div>
                </div>
            `;
            body.innerHTML += thoughtHtml;
            traceTimeline.scrollTop = traceTimeline.scrollHeight;
            return;
        }

        // 3. ACTION PROPOSED (Tool Call)
        if (type === "action") {
            const step = data.step || 1;
            toolCount++;
            metricTools.textContent = toolCount + " tools";

            let card = document.getElementById(`step-card-${step}`);
            if (card) {
                const badge = card.querySelector(".step-badge");
                if (badge) {
                    badge.className = "step-badge tool";
                    badge.innerHTML = `🛠️ Step ${step}: Tool Execution`;
                }

                const body = card.querySelector(".step-body");
                const toolName = data.tool_name || "tool_call";
                const args = data.arguments || {};

                const actionHtml = `
                    <div class="action-box">
                        <div class="action-header">
                            <span>🛠️ Action:</span>
                            <span class="tool-name-badge">${toolName}</span>
                        </div>
                        <pre class="json-code">${JSON.stringify(args, null, 2)}</pre>
                    </div>
                `;
                body.innerHTML += actionHtml;
                traceTimeline.scrollTop = traceTimeline.scrollHeight;
            }
            return;
        }

        // 4. OBSERVATION (Từ MCP Server)
        if (type === "observation") {
            const step = data.step || 1;
            let card = document.getElementById(`step-card-${step}`);
            if (card) {
                card.classList.remove("live-pulse");
                const latencyEl = card.querySelector(".step-latency");
                if (latencyEl && data.latency_ms) {
                    latencyEl.textContent = `⏱️ ${data.latency_ms} ms`;
                }

                const body = card.querySelector(".step-body");
                let obsContent = data.observation || {};
                let obsStr = typeof obsContent === "string" ? obsContent : JSON.stringify(obsContent, null, 2);

                const obsHtml = `
                    <div class="obs-box">
                        <div class="obs-header">👁️ Observation (từ MCP Server):</div>
                        <pre class="json-code">${escapeHtml(obsStr)}</pre>
                    </div>
                `;
                body.innerHTML += obsHtml;
                traceTimeline.scrollTop = traceTimeline.scrollHeight;
            }
            return;
        }

        // 5. FINAL ANSWER
        if (type === "final_answer") {
            removeTypingIndicator(currentTypingId);

            // Render tin nhắn Agent ở bên Trái
            appendMessage("agent", data.output);

            // Render Card Final Answer ở bên Phải
            const step = data.step || 1;
            let card = document.getElementById(`step-card-${step}`);
            if (card) {
                card.classList.remove("live-pulse");
                const badge = card.querySelector(".step-badge");
                if (badge) {
                    badge.className = "step-badge final";
                    badge.innerHTML = `🏁 Step ${step}: Final Answer`;
                }

                const latencyEl = card.querySelector(".step-latency");
                if (latencyEl && data.latency_ms) {
                    latencyEl.textContent = `⏱️ ${data.latency_ms} ms`;
                }

                const body = card.querySelector(".step-body");
                const finalHtml = `
                    <div class="obs-box" style="border-left-color: var(--purple); background: rgba(139, 92, 246, 0.08);">
                        <div class="obs-header" style="color: #DDD6FE;">🏁 Phản hồi tổng hợp:</div>
                        <div style="font-size: 13px; line-height: 1.5; color: #F3F4F6;">${formatMarkdown(data.output || "")}</div>
                    </div>
                `;
                body.innerHTML += finalHtml;
                traceTimeline.scrollTop = traceTimeline.scrollHeight;
            }
            return;
        }

        // 6. COMPLETE
        if (type === "complete") {
            removeTypingIndicator(currentTypingId);
            btnSend.disabled = false;
            metricLatency.textContent = `${data.total_latency_ms || 0} ms`;

            if (data.memory) {
                updateMemoryUI(data.memory);
            }
            document.querySelectorAll(".step-card").forEach(c => c.classList.remove("live-pulse"));
        }
    }

    // Append Message to Chat
    function appendMessage(role, text) {
        const row = document.createElement("div");
        row.className = `msg-row ${role}`;

        const avatar = document.createElement("div");
        avatar.className = "msg-avatar";
        avatar.innerHTML = role === "user" ? "👤" : "🌴";

        const bubble = document.createElement("div");
        bubble.className = "msg-bubble";
        bubble.innerHTML = formatMarkdown(text);

        if (role === "user") {
            row.appendChild(bubble);
            row.appendChild(avatar);
        } else {
            row.appendChild(avatar);
            row.appendChild(bubble);
        }

        chatMessages.appendChild(row);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // Typing Indicator
    function showTypingIndicator() {
        const id = "typing-" + Date.now();
        const row = document.createElement("div");
        row.className = "msg-row agent";
        row.id = id;

        const avatar = document.createElement("div");
        avatar.className = "msg-avatar";
        avatar.innerHTML = "🌴";

        const bubble = document.createElement("div");
        bubble.className = "msg-bubble typing-bubble";
        bubble.innerHTML = `
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
            <span style="font-size: 12px; color: var(--text-muted); margin-left: 6px;">Agent đang suy luận ReAct...</span>
        `;

        row.appendChild(avatar);
        row.appendChild(bubble);
        chatMessages.appendChild(row);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        return id;
    }

    function removeTypingIndicator(id) {
        const el = document.getElementById(id);
        if (el) el.remove();
    }

    // Memory UI
    function updateMemoryUI(mem) {
        if (!mem) return;
        memoryStatusBadge.textContent = "🧠 " + (mem.status_text || "3/3 lượt");
        modalSummaryText.textContent = mem.summary ? mem.summary : "Chưa có tóm tắt dài hạn (Chưa vượt quá 3 lượt).";
        
        modalTurnsContainer.innerHTML = "";
        if (mem.recent_turns && mem.recent_turns.length > 0) {
            mem.recent_turns.forEach((turn, i) => {
                const turnCard = document.createElement("div");
                turnCard.style.marginBottom = "10px";
                turnCard.style.padding = "8px";
                turnCard.style.background = "rgba(0,0,0,0.3)";
                turnCard.style.borderRadius = "6px";
                turnCard.innerHTML = `
                    <div style="color: #34D399; font-weight: 600;">Lượt ${i+1}:</div>
                    <div><strong>👤 Khách:</strong> ${escapeHtml(turn.user)}</div>
                    <div><strong>🤖 Trợ lý:</strong> ${escapeHtml(turn.assistant.slice(0, 150))}...</div>
                `;
                modalTurnsContainer.appendChild(turnCard);
            });
        } else {
            modalTurnsContainer.textContent = "Chưa có lượt trao đổi nào.";
        }
    }

    // Clear Memory
    btnClearMemory.addEventListener("click", async () => {
        if (!confirm("Bạn có chắc chắn muốn xóa toàn bộ bộ nhớ hội thoại?")) return;
        try {
            const res = await fetch("/api/reset_memory", { method: "POST" });
            const data = await res.json();
            if (data.memory) updateMemoryUI(data.memory);
            appendMessage("agent", "🧹 Đã xóa sạch bộ nhớ hội thoại. Bạn có thể bắt đầu chủ đề mới!");
        } catch (e) {
            alert("Lỗi khi xóa memory: " + e.message);
        }
    });

    // Modal Handlers
    btnViewMemory.addEventListener("click", () => {
        memoryModal.classList.remove("hidden");
    });
    btnCloseModal.addEventListener("click", () => {
        memoryModal.classList.add("hidden");
    });
    document.querySelector(".modal-backdrop").addEventListener("click", () => {
        memoryModal.classList.add("hidden");
    });

    // Tab Handlers
    tabLive.addEventListener("click", () => {
        tabLive.classList.add("active");
        tabHistory.classList.remove("active");
        traceTimeline.classList.remove("hidden");
        historyTraceView.classList.add("hidden");
    });

    tabHistory.addEventListener("click", () => {
        tabHistory.classList.add("active");
        tabLive.classList.remove("active");
        traceTimeline.classList.add("hidden");
        historyTraceView.classList.remove("hidden");
        loadHistoryTraces();
    });

    btnReloadHistory.addEventListener("click", loadHistoryTraces);

    async function loadHistoryTraces() {
        historyContent.textContent = "Đang tải lịch sử waterfall trace...";
        try {
            const res = await fetch("/api/history_traces");
            const data = await res.json();
            if (data.status === "SUCCESS") {
                historyContent.textContent = JSON.stringify(data.data, null, 2);
            } else {
                historyContent.textContent = "Không tìm thấy lịch sử: " + (data.message || "");
            }
        } catch (e) {
            historyContent.textContent = "Lỗi tải lịch sử: " + e.message;
        }
    }

    // Markdown Parser (với Hyperlink Agoda trực tiếp)
    function formatMarkdown(text) {
        if (!text) return "";
        let html = escapeHtml(text);
        
        // Headings
        html = html.replace(/^### (.*$)/gim, "<h3>$1</h3>");
        html = html.replace(/^## (.*$)/gim, "<h2>$1</h2>");
        html = html.replace(/^# (.*$)/gim, "<h1>$1</h1>");
        
        // Bold
        html = html.replace(/\*\*(.*?)\*\*/gim, "<strong>$1</strong>");
        
        // Markdown Links: [Text](URL)
        html = html.replace(/\[(.*?)\]\((https?:\/\/[^\s)]+)\)/gim, '<a href="$2" target="_blank" rel="noopener noreferrer" style="color: #38BDF8; font-weight: 600; text-decoration: underline;">$1 ↗</a>');
        
        // Lists
        html = html.replace(/^\s*[-*]\s+(.*$)/gim, "<li>$1</li>");
        html = html.replace(/(<li>.*<\/li>)/gims, "<ul>$1</ul>");
        
        // Line breaks
        html = html.replace(/\n/g, "<br>");
        return html;
    }

    function escapeHtml(str) {
        if (!str) return "";
        return str
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
});
