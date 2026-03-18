<template>
    <div class="chat-panel">
        <div class="chat-header">
            <div>
                <h4>Чат по исследованиям</h4>
                <div class="chat-context">
                    <span
                        v-for="item in selectedAnalyses"
                        :key="item.id"
                        class="context-chip"
                    >
                        {{ item.title }}
                    </span>
                </div>
            </div>
            <div class="chat-actions">
                <button class="subtle-btn" @click="$emit('choose-context')">
                    Выбрать
                </button>
                <button class="icon-btn" @click="$emit('close')">
                    <X :size="18" />
                </button>
            </div>
        </div>

        <div class="chat-messages" ref="messagesEl">
            <div
                v-for="msg in messages"
                :key="msg.id"
                class="chat-message"
                :class="msg.role"
            >
                <div class="bubble">
                    {{ msg.text }}
                </div>
                <span class="msg-time">{{ msg.time }}</span>
            </div>
            <div v-if="isTyping" class="chat-message assistant">
                <div class="bubble typing">
                    <span></span><span></span><span></span>
                </div>
            </div>
        </div>

        <div class="chat-input">
            <input
                :value="modelValue"
                type="text"
                placeholder="Спросите о результатах..."
                @input="$emit('update:modelValue', $event.target.value)"
                @keydown.enter.exact.prevent="$emit('send')"
            />
            <button
                class="btn-send"
                :disabled="!modelValue.trim()"
                @click="$emit('send')"
                aria-label="Отправить"
            >
                <Send :size="16" />
            </button>
        </div>
    </div>
</template>

<script setup>
import { ref, watch, nextTick, onMounted } from "vue";
import { X, Send } from "lucide-vue-next";

const props = defineProps({
    selectedAnalyses: { type: Array, default: () => [] },
    messages: { type: Array, default: () => [] },
    isTyping: { type: Boolean, default: false },
    modelValue: { type: String, default: "" }, // input
});

defineEmits(["close", "choose-context", "send", "update:modelValue"]);

const messagesEl = ref(null);

function scrollToBottom() {
    nextTick(() => {
        if (!messagesEl.value) return;
        messagesEl.value.scrollTop = messagesEl.value.scrollHeight;
    });
}

watch(
    () => props.messages.length,
    () => scrollToBottom(),
);

watch(
    () => props.isTyping,
    () => scrollToBottom(),
);

onMounted(() => scrollToBottom());
</script>

<style scoped>
.chat-panel {
    position: fixed;
    right: 24px;
    bottom: 92px;
    width: min(380px, 92vw);
    height: min(520px, 75vh);
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-lg);
    display: flex;
    flex-direction: column;
    overflow: hidden;
    z-index: 1000;
}

.chat-header {
    padding: 1rem 1.2rem;
    border-bottom: 1px solid var(--border-subtle);
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 12px;
    background: var(--surface-2);
}
.chat-header h4 {
    font-family: var(--font-display);
    font-size: 1rem;
}
.chat-context {
    display: flex;
    gap: 6px;
    flex-wrap: wrap;
    margin-top: 6px;
}
.context-chip {
    font-size: 0.72rem;
    padding: 4px 8px;
    border-radius: 999px;
    background: var(--accent-light);
    color: var(--accent-dark);
}

.chat-actions {
    display: flex;
    gap: 6px;
}

.icon-btn {
    width: 32px;
    height: 32px;
    border-radius: 8px;
    border: 1px solid var(--border);
    background: var(--surface);
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
}

.subtle-btn {
    border: 1px solid var(--border);
    background: var(--surface);
    padding: 6px 10px;
    border-radius: 10px;
    font-size: 0.78rem;
    cursor: pointer;
}

.chat-messages {
    padding: 1rem;
    flex: 1;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 10px;
    background: linear-gradient(180deg, #ffffff 0%, #f7fbff 100%);
}

.chat-message {
    display: flex;
    flex-direction: column;
    max-width: 85%;
}
.chat-message.user {
    align-self: flex-end;
    text-align: right;
}
.chat-message.assistant {
    align-self: flex-start;
}

.bubble {
    padding: 10px 12px;
    border-radius: 14px;
    background: var(--surface-2);
    border: 1px solid var(--border);
    font-size: 0.88rem;
}
.chat-message.user .bubble {
    background: var(--accent);
    color: white;
    border-color: var(--accent);
}

.msg-time {
    margin-top: 4px;
    font-size: 0.65rem;
    color: var(--text-muted);
}

.bubble.typing {
    display: inline-flex;
    gap: 4px;
    align-items: center;
    justify-content: center;
    min-width: 48px;
}
.bubble.typing span {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: var(--text-muted);
    animation: blink 1.2s infinite;
}
.bubble.typing span:nth-child(2) {
    animation-delay: 0.2s;
}
.bubble.typing span:nth-child(3) {
    animation-delay: 0.4s;
}

@keyframes blink {
    0%,
    80%,
    100% {
        opacity: 0.2;
    }
    40% {
        opacity: 1;
    }
}

.chat-input {
    padding: 0.8rem 1rem;
    border-top: 1px solid var(--border-subtle);
    display: flex;
    gap: 8px;
    align-items: center;
    background: var(--surface);
}
.chat-input input {
    flex: 1;
    border: 1px solid var(--border);
    border-radius: 999px;
    padding: 10px 14px;
    font-size: 0.88rem;
}
.chat-input input:focus {
    outline: none;
    border-color: var(--accent);
    box-shadow: 0 0 0 3px rgba(0, 102, 255, 0.1);
}

.btn-send {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    border: none;
    background: var(--accent);
    color: white;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    justify-content: center;
}
.btn-send:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}
</style>
