<template>
    <Teleport to="body">
        <div v-if="open" class="chat-overlay" @click.self="$emit('close')">
            <div
                class="chat-picker"
                style="animation: modalIn 0.3s ease forwards"
            >
                <div class="chat-picker-header">
                    <div>
                        <h3>Сохраненные анализы</h3>
                        <p>Выберите исследования для диалога</p>
                    </div>
                    <button class="icon-btn" @click="$emit('close')">
                        <X :size="18" />
                    </button>
                </div>

                <div class="chat-picker-body">
                    <div v-if="isLoading" class="chat-loading">
                        <span>Загружаем список...</span>
                    </div>
                    <div v-else-if="error" class="chat-error">
                        {{ error }}
                    </div>
                    <div v-else class="analysis-list">
                        <label
                            v-for="item in analyses"
                            :key="item.id"
                            class="analysis-item"
                        >
                            <input
                                type="checkbox"
                                :value="item.id"
                                v-model="localSelectedIds"
                            />
                            <div class="analysis-info">
                                <div class="analysis-title">
                                    {{ item.title }}
                                </div>
                                <div class="analysis-meta">
                                    {{ item.modality }} · {{ item.date }}
                                </div>
                            </div>
                            <span class="analysis-status" :class="item.status">
                                {{ item.statusLabel }}
                            </span>
                        </label>
                    </div>
                </div>

                <div class="chat-picker-footer">
                    <button class="btn-ghost" @click="$emit('close')">
                        Отмена
                    </button>
                    <button
                        class="btn-primary"
                        :disabled="localSelectedIds.length === 0"
                        @click="$emit('confirm')"
                    >
                        Открыть чат
                    </button>
                </div>
            </div>
        </div>
    </Teleport>
</template>

<script setup>
import { computed } from "vue";
import { X } from "lucide-vue-next";

const props = defineProps({
    open: { type: Boolean, default: false },
    isLoading: { type: Boolean, default: false },
    error: { type: String, default: "" },
    analyses: { type: Array, default: () => [] },
    modelValue: { type: Array, default: () => [] },
});

const emit = defineEmits(["close", "confirm", "update:modelValue"]);

const localSelectedIds = computed({
    get: () => props.modelValue,
    set: (v) => emit("update:modelValue", v),
});
</script>

<style scoped>
.chat-overlay {
    position: fixed;
    inset: 0;
    background: rgba(13, 17, 23, 0.55);
    backdrop-filter: blur(6px);
    z-index: 1001;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 1rem;
}

.chat-picker {
    width: min(540px, 96vw);
    background: var(--surface);
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-lg);
    overflow: hidden;
    display: flex;
    flex-direction: column;
}

.chat-picker-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1.25rem 1.5rem 0.75rem;
}
.chat-picker-header h3 {
    font-family: var(--font-display);
    font-size: 1.1rem;
}
.chat-picker-header p {
    font-size: 0.8rem;
    color: var(--text-muted);
}

.chat-picker-body {
    padding: 1rem 1.5rem;
    max-height: 50vh;
    overflow: auto;
}

.chat-error {
    color: var(--danger);
    font-size: 0.9rem;
}

.analysis-list {
    display: flex;
    flex-direction: column;
    gap: 10px;
}
.analysis-item {
    display: grid;
    grid-template-columns: 20px 1fr auto;
    align-items: center;
    gap: 10px;
    padding: 12px;
    border: 1px solid var(--border);
    border-radius: var(--radius-md);
    background: var(--surface-2);
    cursor: pointer;
    transition: all 0.15s ease;
}
.analysis-item:hover {
    border-color: var(--accent);
    background: var(--accent-light);
}
.analysis-item input {
    accent-color: var(--accent);
}
.analysis-title {
    font-weight: 600;
}
.analysis-meta {
    font-size: 0.78rem;
    color: var(--text-muted);
}
.analysis-status {
    font-size: 0.7rem;
    padding: 4px 8px;
    border-radius: 999px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    font-weight: 600;
}
.analysis-status.ok {
    background: var(--success-light);
    color: var(--success);
}
.analysis-status.warn {
    background: var(--warning-light);
    color: var(--warning);
}

.chat-picker-footer {
    display: flex;
    justify-content: flex-end;
    gap: 0.75rem;
    padding: 0.9rem 1.5rem 1.25rem;
    border-top: 1px solid var(--border-subtle);
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
</style>
