<template>
    <div class="admin-page">
        <header class="admin-header">
            <div class="admin-header-left">
                <h1 class="admin-title">Админ-панель</h1>
                <p class="admin-subtitle">Статистика, история анализов, логи и конфигурация</p>
            </div>
            <div class="admin-header-right">
                <label class="auto-refresh-toggle">
                    <input type="checkbox" v-model="autoRefresh" />
                    <span>Автообновление каждые 30 сек</span>
                </label>
                <button class="btn-ghost" @click="goHome">← На главную</button>
            </div>
        </header>

        <div class="admin-tabs">
            <button class="admin-tab" :class="{ active: activeTab === 'stats' }" @click="activeTab = 'stats'">Статистика</button>
            <button class="admin-tab" :class="{ active: activeTab === 'history' }" @click="activeTab = 'history'">История</button>
            <button class="admin-tab" :class="{ active: activeTab === 'logs' }" @click="activeTab = 'logs'">Логи</button>
            <button class="admin-tab" :class="{ active: activeTab === 'config' }" @click="activeTab = 'config'">Конфигурация</button>
            <button class="admin-tab" :class="{ active: activeTab === 'plugins' }" @click="activeTab = 'plugins'">Плагины</button>
        </div>

        <main class="admin-content">
            <section v-if="activeTab === 'stats'">
                <div class="section-header">
                    <h2 class="section-title">Общая статистика</h2>
                    <button class="btn-ghost small" @click="fetchStats">Обновить</button>
                </div>

                <div v-if="loading.stats" class="skeleton-grid skeleton-4"></div>

                <div v-else-if="stats" class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-label">Анализов всего</div>
                        <div class="stat-value">{{ formatInt(stats.total_analyses) }}</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">% патологий</div>
                        <div class="stat-value">{{ formatPercent(stats.pathology_rate) }}</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Ср. время обработки</div>
                        <div class="stat-value">{{ formatDuration(stats.avg_processing_ms) }}</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Ср. балл EDU</div>
                        <div class="stat-value">{{ formatPercent(stats.edu_avg_score || 0) }}</div>
                    </div>
                </div>

                <div v-if="stats" class="section-block">
                    <div class="section-header">
                        <h3 class="section-subtitle">По анализаторам</h3>
                    </div>
                    <div v-if="!stats.by_analyzer || !stats.by_analyzer.length" class="empty-state">
                        Нет данных по анализаторам.
                    </div>
                    <table v-else class="admin-table">
                        <thead>
                            <tr>
                                <th>Анализатор</th>
                                <th>Кол-во</th>
                                <th>% патологий</th>
                                <th>Ср. уверенность</th>
                                <th>Ср. время</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr v-for="row in stats.by_analyzer" :key="row.analyzer_id">
                                <td>{{ row.analyzer_id }}</td>
                                <td>{{ formatInt(row.count) }}</td>
                                <td>{{ formatPercent(row.pathology_rate) }}</td>
                                <td>{{ formatPercent((row.avg_confidence || 0) * 100) }}</td>
                                <td>{{ formatDuration(row.avg_processing_ms) }}</td>
                            </tr>
                        </tbody>
                    </table>
                </div>

                <div class="section-block">
                    <div class="section-header">
                        <h3 class="section-subtitle">Система</h3>
                        <button class="btn-ghost small" @click="Promise.all([fetchAnalyzers(), fetchHealth()])">Обновить</button>
                    </div>
                    <div class="system-grid">
                        <div>
                            <div class="mini-title">Анализаторы</div>
                            <ul v-if="analyzers.length" class="list-simple">
                                <li v-for="a in analyzers" :key="a.id" class="list-item">
                                    <span class="status-dot online"></span>
                                    <div class="list-main">
                                        <div class="list-title">{{ a.name }}</div>
                                        <div class="list-sub">{{ a.id }} · {{ a.modality }}</div>
                                    </div>
                                </li>
                            </ul>
                            <div v-else class="empty-state">Нет зарегистрированных анализаторов.</div>
                        </div>
                        <div>
                            <div class="mini-title">Статус моделей</div>
                            <div v-if="health" class="health-grid">
                                <div class="health-item">
                                    <span>X-ray</span>
                                    <span class="health-value"><span class="status-dot" :class="health.models_loaded?.xray ? 'online' : 'offline'"></span>{{ health.models_loaded?.xray ? 'Загружена' : 'Не загружена' }}</span>
                                </div>
                                <div class="health-item">
                                    <span>Microscopy</span>
                                    <span class="health-value"><span class="status-dot" :class="health.models_loaded?.microscopy ? 'online' : 'offline'"></span>{{ health.models_loaded?.microscopy ? 'Загружена' : 'Не загружена' }}</span>
                                </div>
                                <div class="health-item">
                                    <span>Устройство</span>
                                    <span class="health-value">{{ health.device }}</span>
                                </div>
                            </div>
                            <div v-else class="empty-state">Нет данных health-check.</div>
                        </div>
                    </div>
                </div>
            </section>

            <section v-else-if="activeTab === 'history'">
                <div class="section-header">
                    <h2 class="section-title">История анализов</h2>
                    <div class="filters-row">
                        <select v-model="filtersHistory.analyzer_id">
                            <option value="">Все анализаторы</option>
                            <option v-for="a in analyzers" :key="a.id" :value="a.id">{{ a.name }}</option>
                        </select>
                        <select v-model="filtersHistory.result">
                            <option value="">Все результаты</option>
                            <option value="pathology">Патология</option>
                            <option value="normal">Норма</option>
                        </select>
                        <button class="btn-ghost small" @click="fetchAnalyses">Обновить</button>
                    </div>
                </div>

                <div v-if="loading.analyses" class="skeleton-table"></div>
                <div v-else-if="!analyses.length" class="empty-state">История пуста.</div>

                <table v-else class="admin-table">
                    <thead>
                        <tr>
                            <th>Дата/время</th>
                            <th>Анализатор</th>
                            <th>Диагноз</th>
                            <th>Уверенность</th>
                            <th>Время</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-for="row in analyses" :key="row.id" @click="openAnalysis(row)" class="clickable-row">
                            <td>{{ formatDate(row.created_at) }}</td>
                            <td>{{ row.analyzer_id }}</td>
                            <td>{{ row.diagnosis_label }}</td>
                            <td>{{ row.confidence != null ? formatPercent((row.confidence || 0) * 100) : '-' }}</td>
                            <td>{{ formatDuration(row.processing_ms) }}</td>
                        </tr>
                    </tbody>
                </table>

                <div v-if="selectedAnalysis" class="modal-backdrop" @click.self="selectedAnalysis = null">
                    <div class="modal">
                        <div class="modal-header">
                            <h3 class="section-subtitle">Детали анализа</h3>
                            <button class="btn-ghost small" @click="selectedAnalysis = null">Закрыть</button>
                        </div>
                        <div class="modal-body">
                            <p class="modal-meta">{{ formatDate(selectedAnalysis.created_at) }} · {{ selectedAnalysis.analyzer_id }}</p>
                            <p><strong>Диагноз:</strong> {{ selectedAnalysis.diagnosis_label }}</p>
                            <p><strong>Уверенность:</strong> {{ selectedAnalysis.confidence != null ? formatPercent((selectedAnalysis.confidence || 0) * 100) : '-' }}</p>
                            <p><strong>Время обработки:</strong> {{ formatDuration(selectedAnalysis.processing_ms) }}</p>
                            <div class="overlay-preview">
                                <div class="overlay-title">Overlay</div>
                                <img v-if="selectedAnalysis.overlay_url" :src="selectedAnalysis.overlay_url" alt="overlay" class="overlay-img" />
                                <div v-else class="empty-state">Overlay недоступен.</div>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            <section v-else-if="activeTab === 'logs'">
                <div class="section-header">
                    <h2 class="section-title">Системные логи</h2>
                    <div class="filters-row">
                        <select v-model="filtersLogs.level">
                            <option value="">Все уровни</option>
                            <option value="INFO">INFO</option>
                            <option value="WARNING">WARNING</option>
                            <option value="ERROR">ERROR</option>
                        </select>
                        <button class="btn-ghost small" @click="fetchLogs">Обновить</button>
                    </div>
                </div>

                <div v-if="loading.logs" class="skeleton-table"></div>
                <div v-else-if="!logs.length" class="empty-state">Логов пока нет.</div>
                <table v-else class="admin-table">
                    <thead>
                        <tr>
                            <th>Время</th>
                            <th>Уровень</th>
                            <th>Эндпоинт</th>
                            <th>Сообщение</th>
                            <th>мс</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-for="row in logs" :key="row.id">
                            <td>{{ formatDate(row.created_at) }}</td>
                            <td><span class="log-level" :class="row.level.toLowerCase()">{{ row.level }}</span></td>
                            <td>{{ row.endpoint }}</td>
                            <td class="log-message">{{ row.message }}</td>
                            <td>{{ row.processing_ms ?? 0 }}</td>
                        </tr>
                    </tbody>
                </table>
            </section>

            <section v-else-if="activeTab === 'config'">
                <div class="section-header">
                    <h2 class="section-title">Конфигурация</h2>
                    <button class="btn-ghost small" @click="fetchConfig">Обновить</button>
                </div>

                <div class="config-warning">
                    Изменения применяются немедленно без перезапуска сервера и сохраняются между перезапусками.
                </div>

                <div class="config-warning" :class="{ danger: Math.abs(eduWeightsSum - 1.0) > 0.001 }">
                    Сумма EDU весов: <strong>{{ eduWeightsSum.toFixed(3) }}</strong>
                    <span v-if="Math.abs(eduWeightsSum - 1.0) > 0.001"> (рекомендуется 1.0)</span>
                </div>

                <div v-if="loading.config" class="skeleton-table"></div>
                <div v-else-if="!configEntries.length" class="empty-state">Нет редактируемых параметров.</div>

                <div v-else class="config-groups">
                    <div class="section-block" v-for="group in configGroups" :key="group.title">
                        <div class="section-header">
                            <h3 class="section-subtitle">{{ group.title }}</h3>
                        </div>

                        <div class="config-item" v-for="entry in group.items" :key="entry.key">
                            <div class="config-meta">
                                <div class="config-label">{{ entry.label_ru }}</div>
                                <div class="config-desc">{{ entry.description }}</div>
                            </div>

                            <div class="config-controls">
                                <input
                                    class="config-input"
                                    type="number"
                                    :min="entry.min"
                                    :max="entry.max"
                                    :step="entry.value_type === 'int' ? 1 : 0.001"
                                    v-model.number="configDraft[entry.key]"
                                />
                                <button
                                    class="btn-primary small"
                                    :disabled="isOutOfRange(entry)"
                                    @click="saveConfig(entry)"
                                >
                                    Сохранить
                                </button>
                                <button class="btn-ghost small" @click="resetConfig(entry)">Сбросить</button>
                                <span v-if="savedMarks[entry.key]" class="saved-check">✓</span>
                            </div>

                            <div v-if="isOutOfRange(entry)" class="config-error">
                                Значение должно быть в диапазоне {{ entry.min }} - {{ entry.max }}
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            <section v-else>
                <div class="section-header">
                    <h2 class="section-title">Плагины и веса</h2>
                    <button class="btn-ghost small" @click="Promise.all([fetchWeightsStatus(), fetchPlugins()])">Обновить</button>
                </div>

                <div class="config-warning">
                    Старые веса будут сохранены как backup. Модель перезагрузится автоматически без перезапуска сервера.
                </div>

                <div class="section-block">
                    <div class="section-header">
                        <h3 class="section-subtitle">Статус весов моделей</h3>
                        <button class="btn-ghost small" @click="fetchWeightsStatus">Обновить статус</button>
                    </div>
                    <div v-if="!weightsStatus" class="empty-state">Нет данных о статусе весов.</div>
                    <div v-else class="weights-status-grid">
                        <div class="weights-card">
                            <div class="weights-title">xray</div>
                            <div class="weights-meta">Путь: {{ weightsStatus.xray?.path }}</div>
                            <div class="weights-meta">Размер: {{ weightsStatus.xray?.size_mb }} МБ</div>
                            <div class="weights-meta">Статус: {{ weightsStatus.xray?.loaded ? "Загружена" : "Не загружена" }}</div>
                            <div class="weights-meta">Backup: {{ weightsStatus.xray?.backup_exists ? "Есть" : "Нет" }}</div>
                        </div>
                        <div class="weights-card">
                            <div class="weights-title">microscopy</div>
                            <div class="weights-meta">Путь: {{ weightsStatus.microscopy?.path }}</div>
                            <div class="weights-meta">Размер: {{ weightsStatus.microscopy?.size_mb }} МБ</div>
                            <div class="weights-meta">Статус: {{ weightsStatus.microscopy?.loaded ? "Загружена" : "Не загружена" }}</div>
                            <div class="weights-meta">Backup: {{ weightsStatus.microscopy?.backup_exists ? "Есть" : "Нет" }}</div>
                        </div>
                    </div>
                </div>

                <div class="section-block">
                    <div class="section-header">
                        <h3 class="section-subtitle">Загрузка новых весов</h3>
                    </div>
                    <div class="weights-upload-grid">
                        <div class="weights-card">
                            <div class="weights-title">Рентген (xray)</div>
                            <div class="weights-meta">Файл: xray_model.pth/.pt</div>
                            <button class="btn-primary small" :disabled="uploadingWeights.xray" @click="xrayWeightsInput?.click()">Загрузить новые веса</button>
                            <input ref="xrayWeightsInput" type="file" accept=".pth,.pt" class="hidden-input" @change="onWeightsFileChange('xray', $event)" />
                            <div v-if="uploadingWeights.xray" class="upload-progress">Загрузка: {{ uploadProgress.xray }}%</div>
                            <div v-if="weightsMessage.xray" class="upload-message" :class="{ error: !weightsMessage.xray.ok }">{{ weightsMessage.xray.text }}</div>
                        </div>
                        <div class="weights-card">
                            <div class="weights-title">Микроскопия</div>
                            <div class="weights-meta">Файл: microscopy_model.pt/.pth</div>
                            <button class="btn-primary small" :disabled="uploadingWeights.microscopy" @click="microscopyWeightsInput?.click()">Загрузить новые веса</button>
                            <input ref="microscopyWeightsInput" type="file" accept=".pth,.pt" class="hidden-input" @change="onWeightsFileChange('microscopy', $event)" />
                            <div v-if="uploadingWeights.microscopy" class="upload-progress">Загрузка: {{ uploadProgress.microscopy }}%</div>
                            <div v-if="weightsMessage.microscopy" class="upload-message" :class="{ error: !weightsMessage.microscopy.ok }">{{ weightsMessage.microscopy.text }}</div>
                        </div>
                    </div>
                </div>

                <div class="section-block">
                    <div class="section-header">
                        <h3 class="section-subtitle">Управление плагинами-анализаторами</h3>
                        <button class="btn-primary small" @click="pluginFileInput?.click()">Загрузить плагин (.py)</button>
                        <input ref="pluginFileInput" type="file" accept=".py" class="hidden-input" @change="onPluginFileChange" />
                    </div>
                    <div v-if="pluginStatus" class="upload-message" :class="{ error: !pluginStatus.ok }">{{ pluginStatus.text }}</div>
                    <div class="plugins-grid">
                        <div>
                            <div class="mini-title">Файлы плагинов</div>
                            <ul v-if="pluginsList.plugins?.length" class="list-simple">
                                <li v-for="name in pluginsList.plugins" :key="name" class="list-item">
                                    <span class="status-dot online"></span>
                                    <div class="list-main">
                                        <div class="list-title">{{ name }}</div>
                                    </div>
                                </li>
                            </ul>
                            <div v-else class="empty-state">Плагины пока не загружены.</div>
                        </div>
                        <div>
                            <div class="mini-title">Активные анализаторы</div>
                            <ul v-if="pluginsList.active_analyzers?.length" class="list-simple">
                                <li v-for="analyzerId in pluginsList.active_analyzers" :key="analyzerId" class="list-item list-item-actions">
                                    <div class="list-main">
                                        <div class="list-title">{{ analyzerId }}</div>
                                    </div>
                                    <button class="btn-ghost small" @click="removePlugin(analyzerId)">Отключить</button>
                                </li>
                            </ul>
                            <div v-else class="empty-state">Нет активных плагинов.</div>
                        </div>
                    </div>

                    <div class="plugin-example">
                        <div class="mini-title">Пример структуры плагина</div>
<pre><code># Пример структуры плагина
from PIL import Image
from backend.core.base import BaseAnalyzer, AnalysisContext
from backend.core.registry import register

@register("my_analyzer")
class MyAnalyzer(BaseAnalyzer):
    def __init__(self):
        super().__init__(id="my_analyzer",
                        name="Мой анализатор",
                        modality="xray")

    async def analyze(self, image, *, context, **_):
        ...
</code></pre>
                    </div>
                </div>
            </section>
        </main>
    </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from "vue";
import axios from "axios";

const activeTab = ref("stats");
const autoRefresh = ref(true);
const stats = ref(null);
const analyzers = ref([]);
const health = ref(null);
const analyses = ref([]);
const logs = ref([]);
const selectedAnalysis = ref(null);

const configEntries = ref([]);
const configDraft = reactive({});
const savedMarks = reactive({});
const weightsStatus = ref(null);
const pluginsList = ref({ plugins: [], active_analyzers: [] });
const uploadingWeights = reactive({ xray: false, microscopy: false });
const uploadProgress = reactive({ xray: 0, microscopy: 0 });
const weightsMessage = reactive({ xray: null, microscopy: null });
const pluginStatus = ref(null);
const xrayWeightsInput = ref(null);
const microscopyWeightsInput = ref(null);
const pluginFileInput = ref(null);

const loading = reactive({
    stats: false,
    analyzers: false,
    health: false,
    analyses: false,
    logs: false,
    config: false,
    plugins: false,
    weights: false,
});

const filtersHistory = reactive({ analyzer_id: "", result: "" });
const filtersLogs = reactive({ level: "" });

const MODEL_KEYS = ["HIP_CONFIDENCE_PATHOLOGY", "HIP_CONFIDENCE_NORMAL", "XRAY_ADVANCED_THRESHOLD"];
const EDU_KEYS = [
    "EDU_POINTS_EXCELLENT_PX",
    "EDU_POINTS_GOOD_PX",
    "EDU_WEIGHT_POINTS",
    "EDU_WEIGHT_QUAL",
    "EDU_WEIGHT_DIAGNOSIS",
];
const SYSTEM_KEYS = ["MAX_FILE_SIZE_MB", "IMAGE_SIZE"];

let timerId = null;

function goHome() {
    window.location.href = "/";
}

function formatInt(v) {
    if (!v) return "0";
    return v.toString().replace(/\B(?=(\d{3})+(?!\d))/g, " ");
}

function formatPercent(v) {
    const num = Number(v) || 0;
    return `${num.toFixed(1)}%`;
}

function formatDuration(ms) {
    const num = Number(ms) || 0;
    if (num < 1000) return `${Math.round(num)} мс`;
    return `${(num / 1000).toFixed(1)} с`;
}

function formatDate(iso) {
    if (!iso) return "";
    const d = new Date(iso);
    const months = ["янв", "фев", "мар", "апр", "май", "июн", "июл", "авг", "сен", "окт", "ноя", "дек"];
    const day = String(d.getDate()).padStart(2, "0");
    const mon = months[d.getMonth()];
    const hours = String(d.getHours()).padStart(2, "0");
    const mins = String(d.getMinutes()).padStart(2, "0");
    return `${day} ${mon}, ${hours}:${mins}`;
}

async function fetchStats() {
    loading.stats = true;
    try {
        const res = await axios.get("/api/admin/stats");
        stats.value = res.data;
    } catch {
        alert("Не удалось загрузить статистику");
    } finally {
        loading.stats = false;
    }
}

async function fetchAnalyzers() {
    loading.analyzers = true;
    try {
        const res = await axios.get("/api/analyzers");
        const payload = res.data || {};
        analyzers.value = Array.isArray(payload) ? payload : Object.values(payload);
        console.info(`[Админка] Загружено анализаторов: ${analyzers.value.length}`);
    } catch (e) {
        console.error("[Админка] Ошибка загрузки списка анализаторов", e);
        analyzers.value = [];
    } finally {
        loading.analyzers = false;
    }
}

async function fetchHealth() {
    loading.health = true;
    try {
        const res = await axios.get("/health");
        health.value = res.data;
        console.info("[Админка] Health получен", res.data);
    } catch (e) {
        console.error("[Админка] Ошибка загрузки health", e);
        health.value = null;
    } finally {
        loading.health = false;
    }
}

async function fetchAnalyses() {
    loading.analyses = true;
    try {
        const params = { limit: 20 };
        if (filtersHistory.analyzer_id) params.analyzer_id = filtersHistory.analyzer_id;
        if (filtersHistory.result === "pathology") params.is_pathology = true;
        else if (filtersHistory.result === "normal") params.is_pathology = false;

        const res = await axios.get("/api/admin/analyses", { params });
        analyses.value = res.data || [];
    } catch {
        analyses.value = [];
    } finally {
        loading.analyses = false;
    }
}

async function fetchLogs() {
    loading.logs = true;
    try {
        const params = { limit: 50 };
        if (filtersLogs.level) params.level = filtersLogs.level;
        const res = await axios.get("/api/admin/logs", { params });
        logs.value = res.data || [];
    } catch {
        logs.value = [];
    } finally {
        loading.logs = false;
    }
}

async function fetchConfig() {
    loading.config = true;
    try {
        const res = await axios.get("/api/admin/config");
        configEntries.value = res.data || [];
        for (const entry of configEntries.value) {
            configDraft[entry.key] = Number(entry.current_value);
            savedMarks[entry.key] = false;
        }
    } catch {
        configEntries.value = [];
    } finally {
        loading.config = false;
    }
}

async function fetchWeightsStatus() {
    loading.weights = true;
    try {
        const res = await axios.get("/api/admin/weights/status");
        weightsStatus.value = res.data;
    } catch (e) {
        console.error("[Админка] Ошибка загрузки статуса весов", e);
        weightsStatus.value = null;
    } finally {
        loading.weights = false;
    }
}

async function fetchPlugins() {
    loading.plugins = true;
    try {
        const res = await axios.get("/api/admin/plugins");
        pluginsList.value = res.data || { plugins: [], active_analyzers: [] };
    } catch (e) {
        console.error("[Админка] Ошибка загрузки плагинов", e);
        pluginsList.value = { plugins: [], active_analyzers: [] };
    } finally {
        loading.plugins = false;
    }
}

async function uploadWeights(modelType, file) {
    uploadingWeights[modelType] = true;
    uploadProgress[modelType] = 0;
    weightsMessage[modelType] = null;

    const formData = new FormData();
    formData.append("file", file);
    formData.append("model_type", modelType);

    try {
        const res = await axios.post("/api/admin/weights/upload", formData, {
            onUploadProgress: (e) => {
                const total = e.total || file.size || 1;
                uploadProgress[modelType] = Math.round((e.loaded / total) * 100);
            },
        });
        weightsMessage[modelType] = { ok: true, text: `✓ Модель перезагружена. Размер: ${res.data.size_mb} МБ` };
        await fetchWeightsStatus();
        await fetchHealth();
    } catch (err) {
        weightsMessage[modelType] = { ok: false, text: `✗ ${err.response?.data?.detail || err.message}` };
    } finally {
        uploadingWeights[modelType] = false;
    }
}

async function uploadPlugin(file) {
    const formData = new FormData();
    formData.append("file", file);
    try {
        const res = await axios.post("/api/admin/plugins/upload", formData);
        const ids = res.data?.registered || [];
        pluginStatus.value = { ok: true, text: `✓ Зарегистрирован: ${ids.join(", ")}` };
        await fetchPlugins();
        await fetchAnalyzers();
    } catch (err) {
        pluginStatus.value = { ok: false, text: `✗ ${err.response?.data?.detail || err.message}` };
    }
    setTimeout(() => {
        pluginStatus.value = null;
    }, 4000);
}

async function removePlugin(analyzerId) {
    if (!confirm(`Отключить анализатор ${analyzerId}?`)) return;
    await axios.delete(`/api/admin/plugins/${analyzerId}`);
    await fetchPlugins();
    await fetchAnalyzers();
}

async function onWeightsFileChange(modelType, event) {
    const input = event.target;
    const file = input?.files?.[0];
    if (!file) return;
    await uploadWeights(modelType, file);
    input.value = "";
}

async function onPluginFileChange(event) {
    const input = event.target;
    const file = input?.files?.[0];
    if (!file) return;
    await uploadPlugin(file);
    input.value = "";
}

function isOutOfRange(entry) {
    const value = Number(configDraft[entry.key]);
    if (!Number.isFinite(value)) return true;
    return value < Number(entry.min) || value > Number(entry.max);
}

async function saveConfig(entry) {
    if (isOutOfRange(entry)) return;
    const value = Number(configDraft[entry.key]);
    await axios.put(`/api/admin/config/${entry.key}`, { value });
    entry.current_value = value;
    savedMarks[entry.key] = true;
    setTimeout(() => {
        savedMarks[entry.key] = false;
    }, 2000);
}

async function resetConfig(entry) {
    const res = await axios.get(`/api/admin/config/reset/${entry.key}`);
    const current = Number(res.data.current_value);
    entry.current_value = current;
    configDraft[entry.key] = current;
    savedMarks[entry.key] = true;
    setTimeout(() => {
        savedMarks[entry.key] = false;
    }, 2000);
}

function openAnalysis(row) {
    selectedAnalysis.value = row;
}

function setupAutoRefresh() {
    if (timerId) {
        clearInterval(timerId);
        timerId = null;
    }
    if (!autoRefresh.value) return;
    timerId = setInterval(() => {
        if (activeTab.value === "stats") {
            fetchStats();
            fetchAnalyzers();
            fetchHealth();
        } else if (activeTab.value === "history") {
            fetchAnalyses();
        } else if (activeTab.value === "logs") {
            fetchLogs();
        }
    }, 30000);
}

const configByKey = computed(() => {
    const map = {};
    for (const entry of configEntries.value) map[entry.key] = entry;
    return map;
});

const configGroups = computed(() => {
    const pick = (keys) => keys.map((k) => configByKey.value[k]).filter(Boolean);
    return [
        { title: "Модели и анализ", items: pick(MODEL_KEYS) },
        { title: "Образовательный режим", items: pick(EDU_KEYS) },
        { title: "Система", items: pick(SYSTEM_KEYS) },
    ];
});

const eduWeightsSum = computed(() => {
    const p = Number(configDraft.EDU_WEIGHT_POINTS || 0);
    const q = Number(configDraft.EDU_WEIGHT_QUAL || 0);
    const d = Number(configDraft.EDU_WEIGHT_DIAGNOSIS || 0);
    return p + q + d;
});

watch(autoRefresh, setupAutoRefresh);
watch(activeTab, () => {
    if (activeTab.value === "history" && !analyses.value.length) fetchAnalyses();
    if (activeTab.value === "logs" && !logs.value.length) fetchLogs();
    if (activeTab.value === "config" && !configEntries.value.length) fetchConfig();
    if (activeTab.value === "plugins") {
        fetchWeightsStatus();
        fetchPlugins();
    }
});

onMounted(async () => {
    await Promise.all([fetchStats(), fetchAnalyzers(), fetchHealth(), fetchConfig()]);
    setupAutoRefresh();
});

onBeforeUnmount(() => {
    if (timerId) clearInterval(timerId);
});
</script>

<style scoped>
.admin-page {
    min-height: 100vh;
    background: var(--bg);
    padding: 1.5rem 1.5rem 2rem;
    font-family: var(--font-body);
}
.admin-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
}
.admin-header-left {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
}
.admin-title {
    font-family: var(--font-display);
    font-size: 1.4rem;
    font-weight: 700;
}
.admin-subtitle {
    font-size: 0.85rem;
    color: var(--text-muted);
}
.admin-header-right {
    display: flex;
    align-items: center;
    gap: 0.75rem;
}
.auto-refresh-toggle {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    font-size: 0.8rem;
    color: var(--text-secondary);
}
.auto-refresh-toggle input {
    accent-color: var(--accent);
}
.admin-tabs {
    display: inline-flex;
    border-radius: 999px;
    padding: 4px;
    background: var(--surface-2);
    border: 1px solid var(--border-subtle);
    margin-bottom: 1rem;
    flex-wrap: wrap;
}
.admin-tab {
    border: none;
    background: transparent;
    padding: 6px 14px;
    border-radius: 999px;
    font-size: 0.85rem;
    cursor: pointer;
    color: var(--text-secondary);
}
.admin-tab.active {
    background: var(--surface);
    color: var(--accent);
    box-shadow: var(--shadow-sm);
}
.admin-content {
    max-width: 1100px;
    margin: 0 auto;
}
.section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.5rem;
}
.section-title {
    font-family: var(--font-display);
    font-size: 1rem;
    font-weight: 700;
}
.section-subtitle {
    font-size: 0.9rem;
    font-weight: 600;
}
.stats-grid {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 0.75rem;
    margin-bottom: 1rem;
}
.stat-card {
    padding: 0.85rem 1rem;
    border-radius: var(--radius-md);
    background: var(--surface);
    border: 1px solid var(--border);
    box-shadow: var(--shadow-sm);
}
.stat-label {
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--text-muted);
    margin-bottom: 0.25rem;
}
.stat-value {
    font-family: var(--font-display);
    font-size: 1.3rem;
    font-weight: 700;
}
.section-block {
    margin-top: 1.25rem;
    padding: 1rem;
    border-radius: var(--radius-md);
    background: var(--surface);
    border: 1px solid var(--border);
    box-shadow: var(--shadow-sm);
}
.admin-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.85rem;
}
.admin-table th,
.admin-table td {
    padding: 0.45rem 0.5rem;
    border-bottom: 1px solid var(--border-subtle);
    text-align: left;
}
.admin-table th {
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--text-muted);
}
.system-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1rem;
}
.mini-title {
    font-size: 0.8rem;
    color: var(--text-muted);
    margin-bottom: 0.5rem;
    text-transform: uppercase;
}
.list-simple {
    list-style: none;
    margin: 0;
    padding: 0;
    display: flex;
    flex-direction: column;
    gap: 0.35rem;
}
.list-item {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    font-size: 0.85rem;
}
.list-main {
    display: flex;
    flex-direction: column;
}
.list-title {
    font-weight: 600;
}
.list-sub {
    font-size: 0.78rem;
    color: var(--text-muted);
}
.health-grid {
    display: grid;
    gap: 0.5rem;
}
.health-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.85rem;
}
.health-value {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
}
.filters-row {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    align-items: center;
}
.filters-row select {
    padding: 6px 10px;
    border-radius: var(--radius-sm);
    border: 1px solid var(--border);
    background: var(--surface-2);
    font-size: 0.85rem;
}
.btn-ghost,
.btn-primary {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    padding: 8px 14px;
    border-radius: var(--radius-sm);
    font-size: 0.85rem;
    cursor: pointer;
}
.btn-ghost {
    border: 1px solid var(--border);
    background: var(--surface);
    color: var(--text-secondary);
}
.btn-primary {
    border: 1px solid transparent;
    background: var(--accent);
    color: #fff;
}
.btn-primary:disabled {
    opacity: 0.55;
    cursor: not-allowed;
}
.btn-ghost.small,
.btn-primary.small {
    padding: 6px 10px;
    font-size: 0.8rem;
}
.empty-state {
    padding: 0.75rem 0.5rem;
    font-size: 0.85rem;
    color: var(--text-muted);
}
.skeleton-grid {
    display: grid;
    gap: 0.75rem;
    margin-bottom: 1rem;
}
.skeleton-4 {
    grid-template-columns: repeat(4, minmax(0, 1fr));
}
.skeleton-grid::before,
.skeleton-line,
.skeleton-table {
    content: "";
    display: block;
    width: 100%;
    height: 48px;
    border-radius: var(--radius-md);
    background: linear-gradient(90deg, #edf2f7 0%, #f8fafc 40%, #edf2f7 80%);
    background-size: 200% 100%;
    animation: shimmer 1.2s infinite linear;
}
.skeleton-table {
    height: 140px;
    border-radius: var(--radius-md);
}
.modal-backdrop {
    position: fixed;
    inset: 0;
    background: rgba(15, 23, 42, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 50;
}
.modal {
    background: var(--surface);
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-lg);
    max-width: 520px;
    width: 100%;
    padding: 1rem 1.25rem 1.25rem;
}
.modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.5rem;
}
.modal-body {
    font-size: 0.85rem;
    color: var(--text-secondary);
}
.modal-meta {
    font-size: 0.8rem;
    color: var(--text-muted);
    margin-bottom: 0.5rem;
}
.overlay-preview {
    margin-top: 0.75rem;
}
.overlay-title {
    font-size: 0.8rem;
    font-weight: 600;
    margin-bottom: 0.35rem;
}
.overlay-img {
    width: 100%;
    border-radius: var(--radius-sm);
    border: 1px solid var(--border);
}
.clickable-row {
    cursor: pointer;
}
.clickable-row:hover {
    background: var(--surface-2);
}
.log-level {
    display: inline-flex;
    padding: 2px 8px;
    border-radius: 999px;
    font-size: 0.75rem;
}
.log-level.info {
    background: var(--surface-2);
    color: var(--text-secondary);
}
.log-level.warning {
    background: var(--warning-light);
    color: var(--warning);
}
.log-level.error {
    background: var(--danger-light);
    color: var(--danger);
}
.log-message {
    max-width: 380px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.status-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: var(--text-muted);
}
.status-dot.online {
    background: var(--success);
}
.status-dot.offline {
    background: var(--danger);
}
.config-warning {
    margin-bottom: 0.75rem;
    padding: 0.75rem 0.9rem;
    border-radius: var(--radius-sm);
    background: var(--accent-light);
    color: var(--text-secondary);
    font-size: 0.85rem;
    border: 1px solid var(--border);
}
.config-warning.danger {
    background: var(--danger-light);
    color: var(--danger);
}
.config-groups {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
}
.config-item {
    border-top: 1px solid var(--border-subtle);
    padding-top: 0.75rem;
    margin-top: 0.75rem;
}
.config-meta {
    margin-bottom: 0.5rem;
}
.config-label {
    font-size: 0.9rem;
    font-weight: 600;
    margin-bottom: 0.2rem;
}
.config-desc {
    color: var(--text-muted);
    font-size: 0.8rem;
}
.config-controls {
    display: flex;
    gap: 0.5rem;
    align-items: center;
    flex-wrap: wrap;
}
.config-input {
    width: 140px;
    padding: 7px 10px;
    border-radius: var(--radius-sm);
    border: 1px solid var(--border);
    background: var(--surface-2);
    font-size: 0.85rem;
}
.config-error {
    margin-top: 0.4rem;
    color: var(--danger);
    font-size: 0.78rem;
}
.saved-check {
    color: var(--success);
    font-weight: 700;
    font-size: 1rem;
}
.hidden-input {
    display: none;
}
.weights-status-grid,
.weights-upload-grid,
.plugins-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 0.75rem;
}
.weights-card {
    border: 1px solid var(--border);
    border-radius: var(--radius-md);
    padding: 0.75rem;
    display: flex;
    flex-direction: column;
    gap: 0.45rem;
    background: var(--surface);
}
.weights-title {
    font-size: 0.92rem;
    font-weight: 700;
}
.weights-meta {
    font-size: 0.8rem;
    color: var(--text-secondary);
    word-break: break-word;
}
.upload-progress {
    font-size: 0.8rem;
    color: var(--accent);
}
.upload-message {
    margin-top: 0.5rem;
    border-radius: var(--radius-sm);
    padding: 0.5rem 0.7rem;
    font-size: 0.8rem;
    color: var(--success);
    background: #ecfdf5;
    border: 1px solid #bbf7d0;
}
.upload-message.error {
    color: var(--danger);
    background: var(--danger-light);
    border-color: #fecaca;
}
.list-item-actions {
    justify-content: space-between;
}
.plugin-example {
    margin-top: 0.9rem;
    border: 1px solid var(--border);
    border-radius: var(--radius-md);
    background: var(--surface-2);
    padding: 0.75rem;
}
.plugin-example pre {
    margin: 0.5rem 0 0;
    overflow-x: auto;
    font-size: 0.78rem;
}

@media (max-width: 960px) {
    .stats-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }
    .system-grid {
        grid-template-columns: 1fr;
    }
    .admin-header {
        flex-direction: column;
        align-items: flex-start;
        gap: 0.5rem;
    }
    .weights-status-grid,
    .weights-upload-grid,
    .plugins-grid {
        grid-template-columns: 1fr;
    }
}
</style>
