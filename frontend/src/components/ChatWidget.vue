<template>
    <div class="chat-widget">
        <button class="chat-fab" @click="openPicker" aria-label="Открыть чат">
            <MessageCircle :size="18" />
            <span>Чат</span>
        </button>

        <ChatAnalysisPicker
            :open="isPickerOpen"
            :is-loading="isLoading"
            :error="loadError"
            :analyses="savedAnalyses"
            v-model="selectedIds"
            @close="closePicker"
            @confirm="openChat"
        />

        <ChatPanel
            v-if="isChatOpen"
            :selected-analyses="selectedAnalyses"
            :messages="messages"
            :is-typing="isTyping"
            v-model="input"
            @send="sendMessage"
            @choose-context="openPicker"
            @close="closeChat"
        />
    </div>
</template>

<script setup>
import { ref, computed } from "vue";
import { MessageCircle } from "lucide-vue-next";
import ChatAnalysisPicker from "./ChatAnalysisPicker.vue";
import ChatPanel from "./ChatPanel.vue";

const isPickerOpen = ref(false);
const isChatOpen = ref(false);
const isLoading = ref(false);
const loadError = ref("");
const savedAnalyses = ref([]);
const selectedIds = ref([]);
const messages = ref([
    {
        id: 1,
        role: "assistant",
        text: "Выберите исследования и задайте вопрос. Ответы появятся после подключения LLM на backend.",
        time: "сейчас",
    },
]);
const input = ref("");
const isTyping = ref(false);
const activeContextIds = ref([]);

const selectedAnalyses = computed(() =>
    savedAnalyses.value.filter((a) => selectedIds.value.includes(a.id)),
);

function openPicker() {
    isPickerOpen.value = true;
    if (savedAnalyses.value.length === 0 && !isLoading.value) {
        fetchSavedAnalyses();
    }
}

function closePicker() {
    selectedIds.value = [...activeContextIds.value];
    isPickerOpen.value = false;
}

function openChat() {
    const changed =
        [...selectedIds.value].sort().join(",") !==
        [...activeContextIds.value].sort().join(",");

    activeContextIds.value = [...selectedIds.value];

    if (changed) {
        messages.value = [
            {
                id: Date.now(),
                role: "assistant",
                text: "Контекст обновлён. Задайте вопрос по выбранным исследованиям.",
                time: new Date().toLocaleTimeString("ru-RU", {
                    hour: "2-digit",
                    minute: "2-digit",
                }),
            },
        ];
    }

    isChatOpen.value = true;
    isPickerOpen.value = false;
}

function closeChat() {
    isChatOpen.value = false;
}

function fetchSavedAnalyses() {
    isLoading.value = true;
    loadError.value = "";

    setTimeout(() => {
        try {
            savedAnalyses.value = [
                {
                    id: "a-101",
                    title: "Рентген: грудная клетка",
                    modality: "X-ray",
                    date: "10.03.2026",
                    status: "ok",
                    statusLabel: "Норма",
                },
                {
                    id: "a-102",
                    title: "Микроскопия: мазок крови",
                    modality: "Microscopy",
                    date: "08.03.2026",
                    status: "warn",
                    statusLabel: "Риск",
                },
                {
                    id: "a-103",
                    title: "Рентген: грудная клетка",
                    modality: "X-ray",
                    date: "02.03.2026",
                    status: "ok",
                    statusLabel: "Норма",
                },
            ];
        } catch (e) {
            loadError.value = "Не удалось загрузить список.";
        } finally {
            isLoading.value = false;
        }
    }, 600);
}

function sendMessage() {
    const text = input.value.trim();
    if (!text) return;

    messages.value.push({
        id: Date.now(),
        role: "user",
        text,
        time: new Date().toLocaleTimeString("ru-RU", {
            hour: "2-digit",
            minute: "2-digit",
        }),
    });
    input.value = "";
    simulateAssistantReply();
}

function simulateAssistantReply() {
    isTyping.value = true;
    setTimeout(() => {
        isTyping.value = false;
        messages.value.push({
            id: Date.now() + 1,
            role: "assistant",
            text: "LLM будет отвечать после подключения backend. Сейчас это заглушка.",
            time: new Date().toLocaleTimeString("ru-RU", {
                hour: "2-digit",
                minute: "2-digit",
            }),
        });
    }, 700);
}
</script>

<style scoped>
.chat-widget {
    position: fixed;
    right: 24px;
    bottom: 24px;
    z-index: 900;
}

.chat-fab {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 12px 16px;
    border-radius: 999px;
    border: 1px solid var(--border);
    background: var(--surface);
    color: var(--text-primary);
    box-shadow: var(--shadow-md);
    cursor: pointer;
    transition: all 0.2s ease;
    font-weight: 600;
}
.chat-fab:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-lg);
    border-color: var(--accent);
}
</style>
