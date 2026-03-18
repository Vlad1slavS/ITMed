<template>
  <section class="how-it-works">
    <div class="blob blob-left"></div>
    <div class="blob blob-right"></div>

    <div class="section-header animate-fade-up">
      <h2 class="section-title">
        Как это <span class="title-accent">работает?</span>
      </h2>
      <p class="section-subtitle">
        Наш сервис позволяет быстро и удобно получить предварительное
        медицинское<br/>
        заключение с помощью искусственного интеллекта, а затем
        подтвердить его у врача.
      </p>
    </div>

    <div class="steps-grid animate-fade-up" style="animation-delay: 0.15s">
      <div class="step-card">
        <div class="step-header">
          <div class="step-icon upload-icon">
            <ImageUp :size="22"/>
          </div>
          <h3 class="step-title">Загрузка изображения</h3>
        </div>
        <p class="step-desc">
          Пользователь выбирает и загружает медицинский снимок
          (рентген, мазок крови).
        </p>
        <div class="step-illustration upload-illustration">
          <div class="upload-card">
            <div class="upload-patient">
              <span class="patient-label">Пациент</span>
            </div>
            <div class="upload-drop">
              <div class="upload-icon-box">
                <ImageUp :size="28"/>
              </div>
              <span class="upload-hint"
              >Загрузите медицинский снимок...</span
              >
            </div>
          </div>
          <div class="dashed-circle circle-1"></div>
          <div class="dashed-circle circle-2"></div>
        </div>
      </div>

      <div class="step-card">
        <div class="step-header">
          <div class="step-icon ai-icon">
            <Sparkles :size="22"/>
          </div>
          <h3 class="step-title">Нейросетевой анализ</h3>
        </div>
        <p class="step-desc">
          Алгоритм искусственного интеллекта анализирует снимок по
          нескольким параметрам. Технология использует обширную базу
          клинических данных для выявления возможных отклонений.
        </p>
        <div class="step-illustration ai-illustration">
          <div class="analysis-list">
            <div
                class="analysis-item"
                v-for="(item, i) in analysisItems"
                :key="i"
                :style="`animation-delay: ${i * 0.1}s`"
            >
                            <span
                                class="analysis-dot"
                                :class="item.color"
                            ></span>
              <span class="analysis-text">{{ item.label }}</span>
            </div>
          </div>
          <div class="dashed-circle circle-1"></div>
        </div>
      </div>

      <div class="step-card">
        <div class="step-header">
          <div class="step-icon gradcam-icon">
            <ScanEye :size="22"/>
          </div>
          <h3 class="step-title">Визуализация</h3>
        </div>
        <p class="step-desc">
          Система выделяет на снимке области, повлиявшие на решение
          модели. Вы видите именно то, что «видит» нейросеть — полная
          прозрачность алгоритма.
        </p>
        <div class="step-illustration gradcam-illustration">
          <div class="gradcam-frame">
            <div class="gradcam-overlay">
              <div class="heat-spot spot-1"></div>
              <div class="heat-spot spot-2"></div>
            </div>
            <div class="gradcam-label">
              <span class="gradcam-dot"></span>
              Grad-CAM активен
            </div>
          </div>
          <div class="dashed-circle circle-1"></div>
        </div>
      </div>

      <div class="step-card">
        <div class="step-header">
          <div class="step-icon result-icon">
            <ClipboardCheck :size="22"/>
          </div>
          <h3 class="step-title">Заключение врача</h3>
        </div>
        <p class="step-desc">
          Медицинский специалист получает предварительный результат
          нейросетевого анализа, проверяет выводы и подтверждает итоговое
          заключение. Это экономит время и снижает риск ошибок.
        </p>
        <div class="step-illustration result-illustration">
          <div class="result-card">
            <div class="result-row">
              <CheckCircle :size="16" class="result-check"/>
              <span>Структурных изменений не выявлено</span>
            </div>
            <div class="result-row">
              <CheckCircle :size="16" class="result-check"/>
              <span>Патологических признаков нет</span>
            </div>
            <div class="result-row warning">
              <AlertCircle :size="16" class="result-warn"/>
              <span>Требует уточнения врачом</span>
            </div>
            <div class="result-badge">
              <span class="badge-dot"></span>
              Анализ завершён
            </div>
          </div>
          <div class="dashed-circle circle-1"></div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import {AlertCircle, CheckCircle, ClipboardCheck, ImageUp, ScanEye, Sparkles,} from "lucide-vue-next";

const analysisItems = [
  {label: "Структурные изменения...", color: "orange"},
  {label: "Патологические признаки...", color: "orange"},
  {label: "Качество изображения...", color: "blue"},
  {label: "Поиск по базе данных...", color: "blue"},
];
</script>

<style scoped>
.how-it-works {
  padding: 100px 2rem;
  background: var(--bg);
  position: relative;
  overflow: hidden;
}

.blob {
  position: absolute;
  border-radius: 50%;
  filter: blur(100px);
  opacity: 0.4;
  pointer-events: none;
}

.blob-left {
  width: 500px;
  height: 500px;
  background: radial-gradient(
      circle,
      rgba(0, 102, 255, 0.1) 0%,
      transparent 70%
  );
  top: 0;
  left: -150px;
}

.blob-right {
  width: 400px;
  height: 400px;
  background: radial-gradient(
      circle,
      rgba(0, 200, 150, 0.1) 0%,
      transparent 70%
  );
  bottom: 0;
  right: -100px;
}


.section-header {
  text-align: center;
  margin-bottom: 4rem;
}

.section-title {
  font-family: var(--font-display);
  font-size: clamp(2rem, 4vw, 3rem);
  font-weight: 800;
  letter-spacing: -0.03em;
  color: var(--text-primary);
  margin-bottom: 1rem;
}

.title-accent {
  background: linear-gradient(135deg, var(--accent) 0%, #00b4d8 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.section-subtitle {
  font-size: 1rem;
  color: var(--text-secondary);
  font-weight: 300;
  line-height: 1.8;
}


.steps-grid {
  max-width: 1100px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
}


.step-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-xl);
  padding: 2rem;
  box-shadow: var(--shadow-sm);
  transition: box-shadow 0.3s,
  transform 0.3s;
  overflow: hidden;
  position: relative;
}

.step-card:hover {
  box-shadow: var(--shadow-md);
  transform: translateY(-3px);
}

.step-header {
  display: flex;
  align-items: center;
  gap: 0.9rem;
  margin-bottom: 0.8rem;
}

.step-icon {
  width: 42px;
  height: 42px;
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.upload-icon {
  background: var(--accent-light);
  color: var(--accent);
}

.ai-icon {
  background: #f3e8ff;
  color: #7c3aed;
}

.gradcam-icon {
  background: var(--success-light);
  color: var(--success);
}

.result-icon {
  background: var(--warning-light);
  color: var(--warning);
}

.step-title {
  font-family: var(--font-display);
  font-size: 1.05rem;
  font-weight: 700;
  color: var(--text-primary);
}

.step-desc {
  font-size: 0.88rem;
  color: var(--text-secondary);
  line-height: 1.7;
  margin-bottom: 1.5rem;
}


.step-illustration {
  position: relative;
  height: 160px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.dashed-circle {
  position: absolute;
  border-radius: 50%;
  border: 1.5px dashed rgba(0, 102, 255, 0.15);
  pointer-events: none;
}

.circle-1 {
  width: 180px;
  height: 180px;
}

.circle-2 {
  width: 230px;
  height: 230px;
}


.upload-card {
  background: white;
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: 1rem 1.2rem;
  width: 200px;
  box-shadow: var(--shadow-md);
  z-index: 1;
}

.upload-patient {
  display: flex;
  flex-direction: column;
  gap: 1px;
  margin-bottom: 0.8rem;
  border-bottom: 1px solid var(--border-subtle);
  padding-bottom: 0.6rem;
}

.patient-label {
  font-size: 0.65rem;
  color: var(--text-muted);
}

.patient-name {
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--text-primary);
}

.upload-drop {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  padding: 0.8rem;
  border: 1.5px dashed var(--border);
  border-radius: var(--radius-sm);
  background: var(--surface-2);
}

.upload-icon-box {
  color: var(--text-muted);
}

.upload-hint {
  font-size: 0.68rem;
  color: var(--text-muted);
  text-align: center;
}


.ai-illustration {
  justify-content: center;
  padding: 0 0.5rem;
}

.ai-scan-widget {
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.scan-dots {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px;
}

.scan-dot {
  width: 28px;
  height: 28px;
  border-radius: 6px;
  background: var(--accent-light);
  border: 1px solid rgba(0, 102, 255, 0.2);
  animation: pulse-ring 2s infinite;
}

.scan-dot:nth-child(2) {
  animation-delay: 0.3s;
}

.scan-dot:nth-child(3) {
  animation-delay: 0.6s;
}

.scan-dot:nth-child(4) {
  animation-delay: 0.9s;
}

.analysis-list {
  display: flex;
  flex-direction: column;
  gap: 0.45rem;
  z-index: 1;
}

.analysis-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  background: white;
  border: 1px solid var(--border);
  border-radius: 99px;
  font-size: 0.75rem;
  color: var(--text-secondary);
  box-shadow: var(--shadow-sm);
  animation: fadeIn 0.4s ease forwards;
}

.analysis-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
}

.analysis-dot.orange {
  background: var(--warning);
}

.analysis-dot.blue {
  background: var(--accent);
}


.gradcam-frame {
  width: 160px;
  height: 130px;
  border-radius: var(--radius-md);
  background: #0a1628;
  border: 1px solid rgba(0, 180, 255, 0.3);
  position: relative;
  overflow: hidden;
  z-index: 1;
  box-shadow: 0 0 24px rgba(0, 102, 255, 0.2);
}

.gradcam-overlay {
  position: absolute;
  inset: 0;
  background: radial-gradient(
      circle at 40% 45%,
      rgba(255, 80, 80, 0.35) 0%,
      transparent 50%
  ),
  radial-gradient(
      circle at 65% 55%,
      rgba(255, 160, 0, 0.25) 0%,
      transparent 40%
  );
}

.heat-spot {
  position: absolute;
  border-radius: 50%;
  filter: blur(12px);
}

.spot-1 {
  width: 60px;
  height: 60px;
  background: rgba(255, 60, 60, 0.5);
  top: 25%;
  left: 25%;
}

.spot-2 {
  width: 40px;
  height: 40px;
  background: rgba(255, 140, 0, 0.4);
  top: 35%;
  left: 50%;
}

.gradcam-label {
  position: absolute;
  bottom: 8px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 4px 10px;
  background: rgba(255, 255, 255, 0.12);
  backdrop-filter: blur(6px);
  border-radius: 99px;
  font-size: 0.65rem;
  color: rgba(255, 255, 255, 0.85);
  white-space: nowrap;
}

.gradcam-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--success);
}


.result-card {
  background: white;
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: 1rem 1.2rem;
  width: 230px;
  box-shadow: var(--shadow-md);
  z-index: 1;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.result-row {
  display: flex;
  align-items: center;
  gap: 7px;
  font-size: 0.75rem;
  color: var(--text-secondary);
}

.result-row.warning {
  color: var(--warning);
}

.result-check {
  color: var(--success);
  flex-shrink: 0;
}

.result-warn {
  color: var(--warning);
  flex-shrink: 0;
}

.result-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 0.3rem;
  padding: 5px 10px;
  background: var(--success-light);
  border-radius: 99px;
  font-size: 0.7rem;
  font-weight: 500;
  color: var(--success);
  width: fit-content;
}

.badge-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--success);
}

@media (max-width: 768px) {
  .steps-grid {
    grid-template-columns: 1fr;
  }
}
</style>
