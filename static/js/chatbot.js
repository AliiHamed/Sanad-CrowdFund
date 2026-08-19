const chatbotToggle = document.getElementById("chatbot-toggle");
const chatbotWindow = document.getElementById("chatbot-window");
const chatbotClose = document.getElementById("chatbot-close");
const chatbotInput = document.getElementById("chatbot-input");
const chatbotSend = document.getElementById("chatbot-send");
const chatbotMessages = document.getElementById("chatbot-messages");
const imageUpload = document.getElementById("chat-image-upload");
const imagePreviewContainer = document.getElementById("image-preview-container");
const imagePreview = document.getElementById("image-preview");
const removeImageBtn = document.getElementById("remove-image");

const API_BASE = "/api/chatbot/"; 

// ==========================================
// 🧠 إدارة الـ History الذكية (حسب حالة المستخدم: Guest vs Logged-in)
// ==========================================
const isUserLoggedIn = window.USER_NAME && window.USER_NAME !== "Guest";

// لو مسجل دخول بنخزن في localStorage (دائم)، لو زائر بنخزن في sessionStorage (يتمسح بقفل التاب)
const storageType = isUserLoggedIn ? localStorage : sessionStorage;
const STORAGE_KEY = isUserLoggedIn ? "sanad_user_chat_history" : "sanad_guest_chat_history";

let chatHistory = JSON.parse(storageType.getItem(STORAGE_KEY)) || [];

function saveChatHistory() {
    storageType.setItem(STORAGE_KEY, JSON.stringify(chatHistory));
}

let currentMode = "chat"; 
let step = 0;
let collected = {};
let currentImageData = null;

const FLOWS = {
    campaign: [{key: "title", q: "What's the campaign title? 📝"}, {key: "description", q: "Short description?"}, {key: "story", q: "Full story?"}],
    prediction: [{key: "title", q: "Campaign title? 📝"}, {key: "description", q: "Description?"}, {key: "category", q: "Category?"}, {key: "target_amount", q: "Target amount?"}, {key: "start_date", q: "Start date?"}, {key: "end_date", q: "End date?"}]
};

// استرجاع الرسائل القديمة وعرضها فوراً عند فتح أي صفحة
function renderSavedHistory() {
    if (!chatbotMessages) return;
    chatbotMessages.innerHTML = "";
    
    const userName = isUserLoggedIn ? window.USER_NAME : "there";

    if (chatHistory.length === 0) {
        let welcomeMsg = `Hi ${userName}! 👋 I'm Sanad AI. I can help you find projects, improve your campaign, or answer any questions.`;
        if (window.CURRENT_PROJECT_CONTEXT) {
            welcomeMsg = `Hi ${userName}! 👋 I see you are looking at the <strong>${window.CURRENT_PROJECT_CONTEXT}</strong> campaign. Would you like me to tell you more about it or help you donate? 💝`;
        }
        
        // لو زائر، نضيف تلميح ظريف يحثه على تسجيل الدخول لحفظ الهيستوري دائماً
        if (!isUserLoggedIn) {
            welcomeMsg += `<br><br><small style="color: #64748b; font-style: italic;">💡 Tip: <a href="/accounts/login/" style="color: #2563eb; text-decoration: underline;">Log in</a> to keep your chat history saved permanently!</small>`;
        }

        // استخدام true لتطبيق تأثير الكتابة (Typing Effect) على رسالة الترحيب الأولى
        addBotMessage(welcomeMsg, false, true);
    } else {
        chatHistory.forEach(msg => {
            if (msg.role === "user") {
                let msgContent = "";
                if (msg.imageData) msgContent += `<img src="${msg.imageData}" style="max-width: 100%; border-radius: 8px; margin-bottom: 5px;"><br>`;
                if (msg.content) msgContent += escapeHtml(msg.content);
                chatbotMessages.innerHTML += `<div class="message user-message" style="align-self: flex-end;"><div class="message-bubble" style="background:#10b981; color:white; border-bottom-right-radius:4px;">${msgContent}</div></div>`;
            } else {
                chatbotMessages.innerHTML += `
                    <div class="message bot-message">
                        <div class="message-avatar">✦</div>
                        <div class="message-bubble" style="background:#ffffff; border-top-left-radius:4px; border:1px solid #e2e8f0;">
                            ${formatBotText(msg.content)}
                        </div>
                    </div>`;
            }
        });
        scrollToBottom();
    }
}

// تشغيل الـ History واستعراضه عند التحميل الأول
document.addEventListener("DOMContentLoaded", () => {
    renderSavedHistory();
});

// ==========================================
// 🚀 المساعد الاستباقي (يفتح الشات تلقائياً مرة واحدة في الجلسة)
// ==========================================
setTimeout(() => {
    const hasBeenWelcomed = sessionStorage.getItem("sanad_ai_welcomed");
    if(!chatbotWindow.classList.contains("active") && !hasBeenWelcomed) {
        chatbotWindow.classList.add("active");
        sessionStorage.setItem("sanad_ai_welcomed", "true");
    }
}, 4500);

chatbotToggle.addEventListener("click", () => {
    chatbotWindow.classList.add("active");
    renderSavedHistory(); 
});

chatbotClose.addEventListener("click", () => chatbotWindow.classList.remove("active"));

function scrollToBottom() { 
    if (chatbotMessages) {
        chatbotMessages.scrollTop = chatbotMessages.scrollHeight; 
    }
}

// ==========================================
// 📸 التعامل مع رفع الصور
// ==========================================
imageUpload.addEventListener("change", function(e) {
    const file = e.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function(event) {
            currentImageData = event.target.result;
            imagePreview.src = currentImageData;
            imagePreviewContainer.style.display = "block";
            scrollToBottom();
        };
        reader.readAsDataURL(file);
    }
});

removeImageBtn.addEventListener("click", function() {
    currentImageData = null;
    imageUpload.value = "";
    imagePreviewContainer.style.display = "none";
});

function addUserMessage(message, imgData) {
    // 📌 حفظ الرسالة والصورة في الـ History لتظهر دائماً
    chatHistory.push({ role: "user", content: message, imageData: imgData });
    saveChatHistory();

    let msgContent = "";
    if (imgData) msgContent += `<img src="${imgData}" style="max-width: 100%; border-radius: 8px; margin-bottom: 5px;"><br>`;
    if (message) msgContent += escapeHtml(message);
    
    chatbotMessages.innerHTML += `<div class="message user-message" style="align-self: flex-end;"><div class="message-bubble" style="background:#10b981; color:white; border-bottom-right-radius:4px;">${msgContent}</div></div>`;
    scrollToBottom();
}

function addBotMessage(message, isLoading = false, typeEffect = false) {
    const msgId = "msg-" + Date.now();
    let initialHtml = isLoading ? "Typing... ⏳" : (typeEffect ? "" : formatBotText(message));
    
    chatbotMessages.innerHTML += `
        <div class="message bot-message" id="${msgId}">
            <div class="message-avatar">✦</div>
            <div class="message-bubble" style="background:#ffffff; border-top-left-radius:4px; border:1px solid #e2e8f0;" id="text-${msgId}">
                ${initialHtml}
            </div>
        </div>`;
    scrollToBottom();

    if (typeEffect && !isLoading) {
        let i = 0;
        const elem = document.getElementById(`text-${msgId}`);
        const formattedText = formatBotText(message);
        if (elem) elem.innerHTML = "";
        
        function typing() {
            if (elem && i < formattedText.length) {
                if(formattedText.charAt(i) === '<') {
                    let tag = "";
                    while(formattedText.charAt(i) !== '>' && i < formattedText.length){
                        tag += formattedText.charAt(i); i++;
                    }
                    tag += '>'; elem.innerHTML += tag;
                } else {
                    elem.innerHTML += formattedText.charAt(i); i++;
                }
                scrollToBottom();
                setTimeout(typing, 15);
            }
        }
        typing();
    }
    
    if(!isLoading && message) {
        chatHistory.push({ role: "model", content: message });
        saveChatHistory();
    }
    return document.getElementById(msgId);
}

function escapeHtml(str) {
    const div = document.createElement("div"); div.textContent = str; return div.innerHTML;
}

function formatBotText(text) {
    // لو النص بيحتوي على رابط تسجيل الدخول الخاص بالزوار، نعرضه بتنسيق HTML سليم
    if (text.includes("Log in")) {
        return text; 
    }
    return escapeHtml(text).replace(/\n/g, "<br>").replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
}

async function sendMessage() {
    const message = chatbotInput.value.trim();
    if (!message && !currentImageData) return;

    const imgToSend = currentImageData;
    addUserMessage(message, imgToSend);
    
    chatbotInput.value = "";
    removeImageBtn.click();

    if (currentMode !== "chat") {
        collected[FLOWS[currentMode][step].key] = message;
        step++;
        if (step < FLOWS[currentMode].length) {
            addBotMessage(FLOWS[currentMode][step].q, false, true);
        } else {
            const loadingMsg = addBotMessage("", true);
            try {
                const res = await fetch(API_BASE + (currentMode === "campaign" ? "improve-campaign/" : "funding-prediction/"), {
                    method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(collected)
                });
                const data = await res.json();
                loadingMsg.remove();
                addBotMessage(data.result || data.error, false, true);
            } catch (e) {
                loadingMsg.remove(); addBotMessage("⚠️ Connection error.");
            }
            currentMode = "chat"; step = 0; collected = {};
        }
        return;
    }

    const loadingMsg = addBotMessage("", true);
    try {
        const payload = { 
            message: message, 
            history: chatHistory.slice(0, -2) 
        };
        if (imgToSend) payload.image = imgToSend;

        const res = await fetch(API_BASE + "chat/", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(payload) 
        });
        const data = await res.json();
        loadingMsg.remove();
        
        const replyText = data.answer || data.error || "⚠️ Server returned an empty response.";
        addBotMessage(replyText, false, true);
    } catch (e) {
        loadingMsg.remove();
        addBotMessage("⚠️ Connection error. Please try again.");
    }
}

chatbotSend.addEventListener("click", sendMessage);
chatbotInput.addEventListener("keydown", (e) => { if (e.key === "Enter") sendMessage(); });

document.querySelectorAll(".quick-actions button").forEach(btn => {
    btn.addEventListener("click", () => {
        const action = btn.dataset.action;
        currentMode = action === "donation" ? "chat" : action;
        step = 0; collected = {};
        if (action === "donation") addBotMessage("What kind of project are you looking to support? 💝", false, true);
        else addBotMessage(FLOWS[currentMode][0].q, false, true);
        chatbotInput.focus();
    });
});