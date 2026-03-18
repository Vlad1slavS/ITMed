<template>
  <section class="hero">
    <div class="hero-grid"></div>

    <div class="blob blob-1"></div>
    <div class="blob blob-2"></div>
    <div class="blob blob-3"></div>

    <div class="hero-inner">
      <div class="hero-content">
        <div class="hero-badge animate-fade-up">
          <span class="badge-dot"></span>
          Система медицинской нейросетевой диагностики
        </div>

        <h1
            class="hero-title animate-fade-up"
            style="animation-delay: 0.1s"
        >
          Быстрый анализ<br/>
          <span class="title-accent">медицинских</span>
          <div style="display: flex; flex-direction: row; align-items: flex-start;">
            <span class="title-accent">изображений</span>
          </div>
        </h1>

        <p
            class="hero-subtitle animate-fade-up"
            style="animation-delay: 0.2s"
        >
          Анализ рентгеновских снимков при помощи
          компьютерного зрения.<br/>
          Grad-CAM визуализация — видите то, что видит модель.
        </p>

        <div
            class="hero-actions animate-fade-up"
            style="animation-delay: 0.3s"
        >
          <button class="btn-primary" @click="$emit('open-analyzer')">
            <Upload :size="18"/>
            Загрузить снимок
          </button>
          <!--          <button-->
          <!--              class="btn-secondary"-->
          <!--              @click="$emit('open-analyzer')"-->
          <!--          >-->
          <!--            <Scale :size="18"/>-->
          <!--            Сравнить снимки-->
          <!--          </button>-->
        </div>

        <!-- Modality cards -->
        <div
            class="modality-cards animate-fade-up"
            style="animation-delay: 0.5s"
        >
          <div class="modality-card" @click="$emit('open-analyzer')">
            <div class="card-icon xray-icon">
              <Grid2x2 :size="22"/>
            </div>
            <div class="card-info">
              <span class="card-title">Рентген: Пневмония</span>
              <span class="card-desc"
              >EfficientNet-B3 + Grad-CAM</span
              >
            </div>
            <ArrowRight :size="16" class="card-arrow"/>
          </div>
          <div class="modality-card" @click="$emit('open-analyzer')">
            <div class="card-icon hip-icon">
              <ScanLine :size="22"/>
            </div>
            <div class="card-info">
              <span class="card-title">Дисплазия ТБС</span>
              <span class="card-desc">YOLO + EfficientNet</span>
            </div>
            <ArrowRight :size="16" class="card-arrow"/>
          </div>
          <div class="modality-card" @click="$emit('open-analyzer')">
            <div class="card-icon micro-icon">
              <Activity :size="22"/>
            </div>
            <div class="card-info">
              <span class="card-title">Микроскопия</span>
              <span class="card-desc">Cellpose + EfficientNet-B0</span>
            </div>
            <ArrowRight :size="16" class="card-arrow"/>
          </div>
        </div>
      </div>

      <div
          class="hero-visual animate-fade-up"
          style="animation-delay: 0.35s"
      >
        <div class="visual-glow"></div>
        <div class="visual-ring ring-1"></div>
        <div class="visual-ring ring-2"></div>
        <div class="xray-frame">
          <img class="chest-image" src="/public/blue-hip.png"></img>
          <div class="scan-line"></div>
          <span class="corner tl"></span>
          <span class="corner tr"></span>
          <span class="corner bl"></span>
          <span class="corner br"></span>
        </div>

        <div class="float-tag tag-1">
          <span class="tag-dot green"></span>
          Нейросетевой анализ завершён
        </div>
        <div class="float-tag tag-2">
          <span class="tag-dot blue"></span>
          Grad-CAM активен
        </div>
        <div class="float-tag tag-3">
          <span class="tag-icon">🩻</span>
          Патологий не выявлено
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import {Activity, ArrowRight, Grid2x2, ScanLine, Upload} from "lucide-vue-next";

defineEmits(["open-analyzer"]);
</script>

<style scoped>
.hero {
  min-height: 100vh;
  padding: 100px 2rem 60px;
  background: var(--gradient-hero);
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}


.hero-grid {
  position: absolute;
  inset: 0;
  background-image: linear-gradient(rgba(0, 102, 255, 0.06) 1px, transparent 1px),
  linear-gradient(90deg, rgba(0, 102, 255, 0.06) 1px, transparent 1px);
  background-size: 60px 60px;
  mask-image: radial-gradient(
      ellipse 80% 80% at 50% 50%,
      black 40%,
      transparent 100%
  );
  pointer-events: none;
}


.blob {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.5;
  pointer-events: none;
}

.blob-1 {
  width: 600px;
  height: 600px;
  background: radial-gradient(
      circle,
      rgba(0, 102, 255, 0.18) 0%,
      transparent 70%
  );
  top: -120px;
  right: -100px;
  animation: float 8s ease-in-out infinite;
}

.blob-2 {
  width: 400px;
  height: 400px;
  background: radial-gradient(
      circle,
      rgba(0, 200, 150, 0.13) 0%,
      transparent 70%
  );
  bottom: -50px;
  left: -60px;
  animation: float 10s ease-in-out infinite reverse;
}

.blob-3 {
  width: 280px;
  height: 280px;
  background: radial-gradient(
      circle,
      rgba(0, 150, 255, 0.12) 0%,
      transparent 70%
  );
  top: 40%;
  left: 35%;
  animation: float 12s ease-in-out infinite 2s;
}

.chest-image {
  width: 100%;
  height: 100%;
  object-fit: contain;
}


.hero-inner {
  max-width: 1400px;
  width: 100%;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 4rem;
  align-items: center;
  position: relative;
  z-index: 1;
}


.hero-content {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 7px 16px;
  background: white;
  border: 1px solid var(--border);
  border-radius: 99px;
  font-size: 0.82rem;
  font-weight: 500;
  color: var(--text-secondary);
  margin-bottom: 1.8rem;
  box-shadow: var(--shadow-sm);
  width: fit-content;
}

.badge-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--accent);
  animation: pulse-ring 2s infinite;
}

.hero-title {
  font-family: var(--font-display);
  font-size: clamp(2.4rem, 5vw, 4rem);
  font-weight: 800;
  line-height: 1.1;
  letter-spacing: -0.03em;
  color: var(--text-primary);
  margin-bottom: 1.4rem;
}

.title-accent {
  background: linear-gradient(135deg, var(--accent) 0%, #00b4d8 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.title-secondary {
  color: var(--text-secondary);
  font-weight: 600;
}

.hero-subtitle {
  font-size: 1rem;
  color: var(--text-secondary);
  font-weight: 300;
  line-height: 1.8;
  margin-bottom: 2rem;
}

.hero-actions {
  display: flex;
  gap: 0.8rem;
  flex-wrap: wrap;
  margin-bottom: 2rem;
}

.btn-primary {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 13px 24px;
  background: var(--accent);
  color: white;
  border: none;
  border-radius: var(--radius-md);
  font-family: var(--font-body);
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 4px 20px rgba(0, 102, 255, 0.3);
}

.btn-primary:hover {
  background: var(--accent-dark);
  transform: translateY(-2px);
  box-shadow: 0 8px 28px rgba(0, 102, 255, 0.4);
}

.btn-secondary {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 13px 24px;
  background: white;
  color: var(--text-primary);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  font-family: var(--font-body);
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: var(--shadow-sm);
}

.btn-secondary:hover {
  border-color: var(--accent);
  color: var(--accent);
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.hero-stats {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  padding: 1.2rem 2rem;
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(10px);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  margin-bottom: 1.5rem;
  width: fit-content;
}

.stat {
  text-align: center;
}

.stat-value {
  display: block;
  font-family: var(--font-display);
  font-size: 1.2rem;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.02em;
}

.stat-label {
  font-size: 0.7rem;
  color: var(--text-muted);
}

.stat-divider {
  width: 1px;
  height: 32px;
  background: var(--border);
}


.modality-cards {
  display: flex;
  gap: 0.8rem;
  flex-wrap: wrap;
}

.modality-card {
  display: flex;
  align-items: center;
  gap: 0.8rem;
  padding: 0.85rem 1.2rem;
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.25s;
  box-shadow: var(--shadow-sm);
  min-width: 200px;
}

.modality-card:hover {
  transform: translateY(-3px);
  box-shadow: var(--shadow-lg);
  border-color: var(--accent);
}

.card-icon {
  width: 44px;
  height: 44px;
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.xray-icon {
  background: var(--accent-light);
  color: var(--accent);
}

.hip-icon {
  background: #fff8e6;
  color: var(--warning);
}

.micro-icon {
  background: var(--success-light);
  color: var(--success);
}

.card-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex: 1;
}

.card-title {
  font-family: var(--font-display);
  font-weight: 700;
  font-size: 0.9rem;
}

.card-desc {
  font-size: 0.72rem;
  color: var(--text-muted);
}

.card-arrow {
  color: var(--text-muted);
  transition: transform 0.2s;
}

.modality-card:hover .card-arrow {
  transform: translateX(4px);
  color: var(--accent);
}


.hero-visual {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  height: 520px;
}

.visual-glow {
  position: absolute;
  width: 380px;
  height: 380px;
  border-radius: 50%;
  background: radial-gradient(
      circle,
      rgba(0, 102, 255, 0.18) 0%,
      transparent 70%
  );
  filter: blur(40px);
  z-index: 0;
}

.visual-ring {
  position: absolute;
  border-radius: 50%;
  border: 1px solid rgba(0, 102, 255, 0.12);
  animation: spin-slow 20s linear infinite;
}

.ring-1 {
  width: 420px;
  height: 420px;
  border-style: dashed;
}

.ring-2 {
  width: 500px;
  height: 500px;
  animation-direction: reverse;
  animation-duration: 30s;
}

@keyframes spin-slow {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.xray-frame {
  position: relative;
  z-index: 1;
  width: 340px;
  height: 340px;
  border-radius: var(--radius-xl);
  overflow: hidden;
  box-shadow: 0 0 0 1px rgba(0, 102, 255, 0.15),
  0 20px 60px rgba(0, 102, 255, 0.2),
  0 40px 100px rgba(0, 0, 0, 0.12);
}

.xray-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
  filter: brightness(1.05) contrast(1.1) saturate(1.15);
  mix-blend-mode: normal;
}


.scan-line {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(
      90deg,
      transparent,
      rgba(0, 200, 255, 0.8),
      transparent
  );
  box-shadow: 0 0 12px rgba(0, 200, 255, 0.6);
  animation: scan 3s ease-in-out infinite;
}

@keyframes scan {
  0% {
    top: 0%;
    opacity: 1;
  }
  90% {
    top: 100%;
    opacity: 0.3;
  }
  100% {
    top: 100%;
    opacity: 0;
  }
}


.corner {
  position: absolute;
  width: 18px;
  height: 18px;
  border-color: rgba(0, 180, 255, 0.7);
  border-style: solid;
}

.corner.tl {
  top: 8px;
  left: 8px;
  border-width: 2px 0 0 2px;
}

.corner.tr {
  top: 8px;
  right: 8px;
  border-width: 2px 2px 0 0;
}

.corner.bl {
  bottom: 8px;
  left: 8px;
  border-width: 0 0 2px 2px;
}

.corner.br {
  bottom: 8px;
  right: 8px;
  border-width: 0 2px 2px 0;
}


.float-tag {
  position: absolute;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 16px;
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(12px);
  border: 1px solid var(--border);
  border-radius: 99px;
  font-size: 0.78rem;
  font-weight: 500;
  color: var(--text-secondary);
  box-shadow: var(--shadow-md);
  white-space: nowrap;
  z-index: 2;
}

.tag-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  flex-shrink: 0;
}

.tag-dot.green {
  background: var(--success);
}

.tag-dot.blue {
  background: var(--accent);
}

.tag-icon {
  font-size: 0.9rem;
}

.tag-1 {
  top: 60px;
  left: -30px;
  animation: float 6s ease-in-out infinite;
}

.tag-2 {
  bottom: 100px;
  left: -40px;
  animation: float 7s ease-in-out infinite 1s;
}

.tag-3 {
  top: 80px;
  right: -20px;
  animation: float 8s ease-in-out infinite 0.5s;
}

@media (max-width: 900px) {
  .hero-inner {
    grid-template-columns: 1fr;
    gap: 2.5rem;
    text-align: center;
  }

  .hero-badge,
  .hero-stats,
  .modality-cards {
    margin-left: auto;
    margin-right: auto;
  }

  .hero-actions {
    justify-content: center;
  }

  .hero-visual {
    height: 360px;
  }

  .xray-frame {
    width: 260px;
    height: 260px;
  }

  .ring-1 {
    width: 300px;
    height: 300px;
  }

  .ring-2 {
    width: 360px;
    height: 360px;
  }

  .tag-1 {
    left: 0;
  }

  .tag-2 {
    left: 0;
  }
}
</style>
