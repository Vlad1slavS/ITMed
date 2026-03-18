<template>
  <Teleport to="body">
    <div class="backdrop" @click.self="$emit('close')">
      <div
          v-if="step === 'upload'"
          class="modal modal-upload"
          style="animation: modalIn 0.35s ease forwards"
      >
        <div class="modal-header">
          <div class="modal-title-group">
            <div class="modal-icon">
              <FileText :size="20"/>
            </div>
            <div>
              <h2 class="modal-title">Новое исследование</h2>
              <p class="modal-subtitle">
                Загрузите медицинский снимок для анализа
              </p>
            </div>
          </div>
          <button class="close-btn" @click="$emit('close')">
            <X :size="18"/>
          </button>
        </div>
        <div class="modal-body">
          <div class="field-group">
            <label class="field-label">Тип исследования</label>
            <div class="modality-selector">
              <button
                  v-for="m in modalities"
                  :key="m.value"
                  class="modality-btn"
                  :class="{ active: selectedAnalyzer === m.value }"
                  @click="selectedAnalyzer = m.value; mode = 'doctor'; resetEducational()"
              >
                <component
                    :is="m.icon"
                    :size="20"
                    class="mod-icon"
                />
                <span class="mod-label">{{ m.label }}</span>
                <span class="mod-sub">{{ m.sub }}</span>
              </button>
            </div>
          </div>
          <div v-if="selectedAnalyzer === 'hip_dysplasia'" class="field-group">
            <label class="field-label">Режим работы</label>
            <div class="mode-selector">
              <button
                  class="mode-btn"
                  :class="{ active: mode === 'doctor' }"
                  @click="mode = 'doctor'; resetEducational()"
              >
                <span class="mode-btn-title">Режим врача</span>
                <span class="mode-btn-sub">Диагностика и анализ</span>
              </button>
              <button
                  class="mode-btn"
                  :class="{ active: mode === 'educational' }"
                  @click="mode = 'educational'; resetEducational()"
              >
                <span class="mode-btn-title">Образовательный режим</span>
                <span class="mode-btn-sub">Обучение и проверка знаний</span>
              </button>
            </div>
          </div>
          <div v-if="selectedAnalyzer === 'xray_pneumonia'" class="field-group">
            <label class="field-label">Модель анализа</label>
            <div class="model-selector">
              <button
                  class="model-btn"
                  :class="{ active: xrayModel === 'standard' }"
                  @click="xrayModel = 'standard'"
              >
                                <span class="model-btn-title"
                                >EfficientNet-B3</span
                                >
                <span class="model-btn-sub"
                >Пневмония · Быстро</span
                >
              </button>
              <button
                  class="model-btn"
                  :class="{ active: xrayModel === 'advanced' }"
                  @click="xrayModel = 'advanced'"
              >
                                <span class="model-btn-title">
                                    DenseNet121
                                    <span class="badge-pro">PRO</span>
                                </span>
                <span class="model-btn-sub"
                >18 патологий · Топ-3 Grad-CAM</span
                >
              </button>
            </div>
          </div>
          <div class="field-group">
            <label class="field-label">Снимок</label>
            <div
                class="dropzone"
                :class="{
                                'dropzone--active': isDragging,
                                'dropzone--filled': previewUrl || dicomFile,
                            }"
                @dragover.prevent="isDragging = true"
                @dragleave="isDragging = false"
                @drop.prevent="onDrop"
                @click="fileInput.click()"
            >
              <input
                  ref="fileInput"
                  type="file"
                  accept="image/*, .dcm,application/dicom"
                  style="display: none"
                  @change="onFileChange"
              />
              <div v-if="!previewUrl && !dicomFile" class="dropzone-empty">
                <div class="dz-icon">
                  <Upload :size="32"/>
                </div>
                <p class="dz-primary">
                  Перетащите файл или нажмите для выбора
                </p>
                <p class="dz-secondary">
                  DCM, JPG, PNG, BMP, TIFF до 20 МБ
                </p>
              </div>
              <div v-else-if="previewUrl" class="dropzone-preview">
                <img :src="previewUrl" class="preview-img"/>
                <div class="preview-overlay"><span>Изменить</span></div>
                <div class="preview-badge">
                  <CheckCircle :size="12"/>
                  {{ fileName }}
                </div>
              </div>
              <!-- Заглушка для DICOM без превью -->
              <div
                  v-else-if="dicomFile"
                  class="dropzone-preview"
                  style="display:flex;align-items:center;justify-content:center;min-height:160px;background:#0d1117;"
              >
                <div
                    style="display:flex;flex-direction:column;align-items:center;gap:8px;color:var(--text-muted)"
                >
                  <ScanLine :size="48"/>
                  <span style="font-size:0.85rem;font-weight:500;color:white">
                                        DICOM загружен
                                    </span>
                  <span style="font-size:0.75rem;color:var(--text-muted)">
                                        {{ fileName }}
                                    </span>
                  <span style="font-size:0.72rem;color:var(--text-muted)">
                                        Превью загружается...
                                    </span>
                </div>
              </div>
            </div>
          </div>
          <div v-if="showPatientAgeField" class="field-group">
            <label class="field-label">Возраст пациента</label>
            <div class="age-input-row">
              <input
                  v-model="patientAgeValue"
                  class="age-input"
                  type="number"
                  min="0"
                  step="0.1"
                  placeholder="Введите возраст"
              />
              <select v-model="patientAgeUnit" class="age-select">
                <option value="years">лет</option>
                <option value="months">мес</option>
              </select>
            </div>
            <p v-if="detectedAgeHint" class="age-hint">{{ detectedAgeHint }}</p>
            <p v-else class="age-hint">
              Укажите возраст вручную (годы или месяцы) для более точной оценки.
            </p>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-ghost" @click="$emit('close')">
            Отмена
          </button>
          <button
              class="btn-primary"
              :disabled="!file || !selectedAnalyzer"
              @click="step = 'confirm'"
          >
            Далее
            <ChevronRight :size="16"/>
          </button>
        </div>
      </div>
      <div
          v-if="step === 'confirm'"
          class="modal modal-confirm"
          style="animation: modalIn 0.3s ease forwards"
      >
        <div class="modal-header">
          <div class="modal-title-group">
            <div class="modal-icon confirm-icon">
              <ShieldCheck :size="22"/>
            </div>
            <div>
              <h2 class="modal-title">Подтверждение</h2>
              <p class="modal-subtitle">
                Проверьте данные перед отправкой
              </p>
            </div>
          </div>
          <button class="close-btn" @click="$emit('close')">
            <X :size="18"/>
          </button>
        </div>
        <div class="modal-body">
          <div class="confirm-card">
            <img :src="previewUrl" class="confirm-thumb"/>
            <div class="confirm-details">
              <div class="confirm-row">
                <span class="confirm-key">Файл</span>
                <span class="confirm-val">{{ fileName }}</span>
              </div>
              <div class="confirm-row">
                                <span class="confirm-key"
                                >Тип исследования</span
                                >
                <span
                    class="confirm-val confirm-badge"
                    :class="modality"
                >
                                    {{ modalities.find(m => m.value === selectedAnalyzer)?.label || selectedAnalyzer }}
                                </span>
              </div>
              <div class="confirm-row">
                <span class="confirm-key">Модель</span>
                <span class="confirm-val">{{
                    modelLabel
                  }}</span>
              </div>
              <div v-if="showPatientAgeField" class="confirm-row">
                <span class="confirm-key">Возраст</span>
                <span class="confirm-val">{{
                    patientAgeDisplay || "Не указан"
                  }}</span>
              </div>
            </div>
          </div>
          <p class="confirm-notice">
            <Info :size="14"/>
            Результат носит информационный характер и не является
            медицинским заключением
          </p>
        </div>
        <div class="modal-footer">
          <button class="btn-ghost" @click="step = 'upload'">
            <ChevronLeft :size="16"/>
            Назад
          </button>
          <button
              class="btn-primary"
              @click="mode === 'educational'
                            ? (resetEducational(), step = 'edu_intro')
                            : submitAnalysis()"
          >
            <Search :size="16"/>
            {{ mode === 'educational' ? 'Начать задание' : 'Запустить анализ' }}
          </button>
        </div>
      </div>
      <div
          v-if="step === 'edu_intro'"
          class="modal modal-educational"
          style="animation: modalIn 0.3s ease forwards"
      >
        <div class="modal-header">
          <div class="modal-title-group">
            <div class="modal-icon confirm-icon">
              <ShieldCheck :size="22"/>
            </div>
            <div>
              <h2 class="modal-title">Перед началом — изучите схему</h2>
              <p class="modal-subtitle">
                Разберём четыре ключевые точки для каждого тазобедренного сустава
              </p>
            </div>
          </div>
          <button class="close-btn" @click="$emit('close')">
            <X :size="18"/>
          </button>
        </div>
        <div class="modal-body">
          <div class="edu-intro-grid">
            <div
                v-for="code in ['A', 'B', 'C', 'H']"
                :key="code"
                class="edu-intro-card"
            >
              <div class="edu-intro-header">
                                <span
                                    class="edu-intro-badge"
                                    :style="{ backgroundColor: POINT_COLORS[code] }"
                                >
                                    {{ code }}
                                </span>
                <div class="edu-intro-title">
                                    <span class="edu-intro-name">
                                        {{
                                        code === 'A'
                                            ? 'TCC — центр Y-образного хряща'
                                            : code === 'B'
                                                ? 'ASM — край крыши впадины'
                                                : code === 'C'
                                                    ? 'FHC — центр головки бедра'
                                                    : 'MOFM — медиальный контур метафиза'
                                      }}
                                    </span>
                  <span class="edu-intro-side-hint">Левый и правый суставы — зеркально</span>
                </div>
              </div>
              <p class="edu-intro-description">
                {{
                  code === 'A'
                      ? 'Точка схождения трёх костей таза — самый глубокий центр впадины.'
                      : code === 'B'
                          ? 'Верхний наружный угол костной крыши вертлужной впадины.'
                          : code === 'C'
                              ? 'Геометрический центр округлой тени головки бедренной кости.'
                              : 'Внутренний край шейки бедренной кости у перехода в диафиз.'
                }}
              </p>
              <p class="edu-intro-anatomy">
                {{
                  code === 'A'
                      ? 'Ориентир: самая глубокая точка вертлужной впадины.'
                      : code === 'B'
                          ? 'Ориентир: самая выступающая точка крыши сверху и снаружи.'
                          : code === 'C'
                              ? 'Ориентир: центр округлой тени головки, даже если она хрящевая.'
                              : 'Ориентир: медиальный контур основания шейки бедра.'
                }}
              </p>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-ghost" @click="step = 'confirm'; resetEducational()">
            <ChevronLeft :size="16"/>
            Назад
          </button>
          <button
              class="btn-primary"
              @click="step = 'edu_points'"
          >
            Понятно, начинаем →
          </button>
        </div>
      </div>
      <div
          v-if="step === 'edu_points'"
          class="modal modal-educational"
          style="animation: modalIn 0.3s ease forwards"
      >
        <div class="modal-header">
          <div class="modal-title-group">
            <div class="modal-icon confirm-icon">
              <ShieldCheck :size="22"/>
            </div>
            <div>
              <h2 class="modal-title">Расстановка точек</h2>
              <p class="modal-subtitle">
                Поставьте точки последовательно: сначала левый сустав, затем правый
              </p>
            </div>
          </div>
          <button class="close-btn" @click="$emit('close')">
            <X :size="18"/>
          </button>
        </div>
        <div class="modal-body">
          <div class="edu-instruction">
            <div class="edu-progress-header">
              <div class="edu-progress-label">Прогресс по суставам</div>
              <div class="edu-progress-overall">
                {{ pointsProgress }}
              </div>
            </div>
            <div class="edu-progress-rows">
              <div class="edu-progress-row">
                <div class="edu-progress-side-label">Левый сустав</div>
                <div class="edu-progress-dots">
                                    <span
                                        v-for="p in POINT_ORDER.filter(p => p.side === 'left')"
                                        :key="p.key"
                                        class="edu-dot-small"
                                        :class="{
                                            done:    studentPoints[p.key],
                                            skipped: skippedPoints.has(p.key),
                                            current: p.key === currentPoint?.key,
                                        }"
                                        :style="{
                                            background: studentPoints[p.key]
                                                ? POINT_COLORS[p.code]
                                                : skippedPoints.has(p.key)
                                                    ? 'var(--text-muted)'
                                                    : 'var(--border)',
                                        }"
                                    >
                                        {{ p.code }}
                                    </span>
                </div>
              </div>
              <div class="edu-progress-row">
                <div class="edu-progress-side-label">Правый сустав</div>
                <div class="edu-progress-dots">
                                    <span
                                        v-for="p in POINT_ORDER.filter(p => p.side === 'right')"
                                        :key="p.key"
                                        class="edu-dot-small"
                                        :class="{
                                            done:    studentPoints[p.key],
                                            skipped: skippedPoints.has(p.key),
                                            current: p.key === currentPoint?.key,
                                        }"
                                        :style="{
                                            background: studentPoints[p.key]
                                                ? POINT_COLORS[p.code]
                                                : skippedPoints.has(p.key)
                                                    ? 'var(--text-muted)'
                                                    : 'var(--border)',
                                        }"
                                    >
                                        {{ p.code }}
                                    </span>
                </div>
              </div>
            </div>
            <div class="edu-current-point">
              <div class="edu-current-code" :style="{ borderColor: POINT_COLORS[currentPoint.code] }">
                                <span
                                    class="edu-current-code-badge"
                                    :style="{ backgroundColor: POINT_COLORS[currentPoint.code] }"
                                >
                                    {{ currentPoint.code }}
                                </span>
                <div class="edu-current-main">
                  <div class="edu-current-label">{{ currentPoint.label }}</div>
                  <div
                      class="edu-current-side-badge"
                      :class="currentPoint.side === 'left' ? 'left' : 'right'"
                  >
                    {{ currentPoint.side === 'left' ? '← Левый сустав' : 'Правый сустав →' }}
                  </div>
                </div>
              </div>
              <div class="edu-hints-block">
                <div class="edu-hint-main">
                  <Info :size="16"/>
                  <span>{{ currentPoint.hint }}</span>
                </div>
                <div class="edu-hint-anatomy">
                  <em>{{ currentPoint.anatomy_tip }}</em>
                </div>
                <button class="edu-hint-more" type="button" @click="showHintDetails = !showHintDetails">
                  {{ showHintDetails ? 'Скрыть подробности' : 'Подробнее' }}
                </button>
                <div v-if="showHintDetails" class="edu-hint-extended">
                  {{ currentPoint.hint_extended }}
                </div>
              </div>
            </div>
          </div>
          <div
              class="edu-image-container"
              @click="onImageClick"
              style="cursor: crosshair; position: relative; border: 2px solid var(--border); border-radius: var(--radius-md); overflow: hidden; background: #0d1117;"
          >
            <img :src="previewUrl || (dicomFile ? '/api/utils/preview' : '')" class="edu-image"
                 style="width: 100%; height: auto; display: block;"/>
            <!-- Отображение уже поставленных точек -->
            <div
                v-for="(point, key) in studentPoints"
                :key="key"
                class="edu-point-marker"
                :style="{
                                left: point.x * 100 + '%',
                                top: point.y * 100 + '%',
                            }"
            >
              <div
                  class="edu-point-dot"
                  :style="{ backgroundColor: POINT_COLORS[POINT_ORDER.find(p => p.key === key)?.code || 'A'] }"
              ></div>
              <span class="edu-point-label">
                                {{ POINT_ORDER.find(p => p.key === key)?.label.split('(')[0].trim() }}
                            </span>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-ghost" @click="step = 'confirm'; resetEducational()">
            <ChevronLeft :size="16"/>
            Назад
          </button>

          <!-- Кнопка пропуска — только для опциональных точек (FHC) -->
          <button
              v-if="currentPoint?.optional"
              class="btn-ghost"
              style="color:var(--text-muted)"
              @click="skipCurrentPoint"
          >
            Пропустить — не видно
          </button>

          <button
              class="btn-primary"
              :disabled="Object.keys(studentPoints).length + skippedPoints.size < POINT_ORDER.length"
              @click="step = 'edu_form'"
          >
            Далее
            <ChevronRight :size="16"/>
          </button>
        </div>
      </div>
      <div
          v-if="step === 'edu_form'"
          class="modal modal-educational"
          style="animation: modalIn 0.3s ease forwards"
      >
        <div class="modal-header">
          <div class="modal-title-group">
            <div class="modal-icon confirm-icon">
              <ShieldCheck :size="22"/>
            </div>
            <div>
              <h2 class="modal-title">Качественные признаки</h2>
              <p class="modal-subtitle">
                Оцените признаки и поставьте диагноз
              </p>
            </div>
          </div>
          <button class="close-btn" @click="$emit('close')">
            <X :size="18"/>
          </button>
        </div>
        <div class="modal-body" style="max-height: 60vh; overflow-y: auto;">
          <!-- Линия Шентона -->
          <div class="field-group">
            <label class="field-label">Линия Шентона</label>
            <div class="edu-radio-group">
              <div class="edu-radio-item">
                <label>Левый сустав:</label>
                <div class="edu-radio-buttons">
                  <button
                      class="edu-radio-btn"
                      :class="{ active: studentQualitative.shenton_left === 'непрерывная' }"
                      @click="studentQualitative.shenton_left = 'непрерывная'"
                  >
                    Непрерывная
                  </button>
                  <button
                      class="edu-radio-btn"
                      :class="{ active: studentQualitative.shenton_left === 'прерывается' }"
                      @click="studentQualitative.shenton_left = 'прерывается'"
                  >
                    Прерывается
                  </button>
                </div>
              </div>
              <div class="edu-radio-item">
                <label>Правый сустав:</label>
                <div class="edu-radio-buttons">
                  <button
                      class="edu-radio-btn"
                      :class="{ active: studentQualitative.shenton_right === 'непрерывная' }"
                      @click="studentQualitative.shenton_right = 'непрерывная'"
                  >
                    Непрерывная
                  </button>
                  <button
                      class="edu-radio-btn"
                      :class="{ active: studentQualitative.shenton_right === 'прерывается' }"
                      @click="studentQualitative.shenton_right = 'прерывается'"
                  >
                    Прерывается
                  </button>
                </div>
              </div>
            </div>
          </div>
          <!-- Ядра окостенения -->
          <div class="field-group">
            <label class="field-label">Ядра окостенения</label>
            <div class="edu-radio-group">
              <div class="edu-radio-item">
                <label>Левый сустав:</label>
                <div class="edu-radio-buttons">
                  <button
                      class="edu-radio-btn"
                      :class="{ active: studentQualitative.ossif_left === 'есть' }"
                      @click="studentQualitative.ossif_left = 'есть'"
                  >
                    Есть
                  </button>
                  <button
                      class="edu-radio-btn"
                      :class="{ active: studentQualitative.ossif_left === 'отсутствует' }"
                      @click="studentQualitative.ossif_left = 'отсутствует'"
                  >
                    Отсутствует
                  </button>
                  <button
                      class="edu-radio-btn"
                      :class="{ active: studentQualitative.ossif_left === 'уменьшено' }"
                      @click="studentQualitative.ossif_left = 'уменьшено'"
                  >
                    Уменьшено
                  </button>
                </div>
              </div>
              <div class="edu-radio-item">
                <label>Правый сустав:</label>
                <div class="edu-radio-buttons">
                  <button
                      class="edu-radio-btn"
                      :class="{ active: studentQualitative.ossif_right === 'есть' }"
                      @click="studentQualitative.ossif_right = 'есть'"
                  >
                    Есть
                  </button>
                  <button
                      class="edu-radio-btn"
                      :class="{ active: studentQualitative.ossif_right === 'отсутствует' }"
                      @click="studentQualitative.ossif_right = 'отсутствует'"
                  >
                    Отсутствует
                  </button>
                  <button
                      class="edu-radio-btn"
                      :class="{ active: studentQualitative.ossif_right === 'уменьшено' }"
                      @click="studentQualitative.ossif_right = 'уменьшено'"
                  >
                    Уменьшено
                  </button>
                </div>
              </div>
            </div>
          </div>
          <!-- Диагноз -->
          <div class="field-group">
            <label class="field-label">Итоговый диагноз</label>
            <div class="edu-diagnosis-buttons">
              <button
                  class="edu-diagnosis-btn"
                  :class="{ active: studentDiagnosis === 'норма' }"
                  @click="studentDiagnosis = 'норма'"
              >
                Норма
              </button>
              <button
                  class="edu-diagnosis-btn"
                  :class="{ active: studentDiagnosis === 'предвывих' }"
                  @click="studentDiagnosis = 'предвывих'"
              >
                Предвывих
              </button>
              <button
                  class="edu-diagnosis-btn"
                  :class="{ active: studentDiagnosis === 'подвывих' }"
                  @click="studentDiagnosis = 'подвывих'"
              >
                Подвывих
              </button>
              <button
                  class="edu-diagnosis-btn"
                  :class="{ active: studentDiagnosis === 'вывих' }"
                  @click="studentDiagnosis = 'вывих'"
              >
                Вывих
              </button>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-ghost" @click="step = 'edu_points'; studentPoints = {}; currentPointIndex = 0">
            <ChevronLeft :size="16"/>
            Назад
          </button>
          <button
              class="btn-primary"
              :disabled="!studentDiagnosis"
              @click="submitEducational"
          >
            <Search :size="16"/>
            Проверить
          </button>
        </div>
      </div>
      <div
          v-if="step === 'loading'"
          class="modal modal-loading"
          style="animation: modalIn 0.3s ease forwards"
      >
        <div class="loading-content">
          <div class="loading-visual">
            <div class="loading-ring"></div>
            <div class="loading-ring loading-ring--2"></div>
            <div class="loading-inner">
              <ShieldCheck :size="28" color="var(--accent)"/>
            </div>
          </div>
          <h3 class="loading-title">Анализ выполняется</h3>
          <p class="loading-sub">Нейросеть обрабатывает снимок...</p>
          <div class="loading-steps">
            <div
                class="lstep"
                :class="{
                                active: loadStep >= 1,
                                done: loadStep > 1,
                            }"
            >
              Предобработка изображения
            </div>
            <div
                class="lstep"
                :class="{
                                active: loadStep >= 2,
                                done: loadStep > 2,
                            }"
            >
              Инференс модели
            </div>
            <div
                class="lstep"
                :class="{
                                active: loadStep >= 3,
                                done: loadStep > 3,
                            }"
            >
              {{
                selectedAnalyzer === "hip_dysplasia"
                    ? "Построение линий и углов"
                    : selectedAnalyzer === "blood_cells"
                        ? "Детекция клеток"
                        : "Генерация Grad-CAM"
              }}
            </div>
            <div
                class="lstep"
                :class="{
                                active: loadStep >= 4,
                                done: loadStep > 4,
                            }"
            >
              Формирование отчёта
            </div>
          </div>
        </div>
      </div>
      <div
          v-if="step === 'result' && result"
          class="modal modal-result"
          style="animation: modalIn 0.35s ease forwards"
      >
        <template v-if="result._is_educational">
          <div class="modal-header">
            <div class="modal-title-group">
              <div class="modal-icon"
                   :class="result.total_score >= 70 ? 'success-icon'
                                        : result.total_score >= 50 ? 'confirm-icon'
                                        : 'danger-icon'">
                <CheckCircle v-if="result.total_score >= 70" :size="20"/>
                <AlertCircle v-else :size="20"/>
              </div>
              <div>
                <h2 class="modal-title">Результаты проверки</h2>
                <p class="modal-subtitle">Образовательный режим</p>
              </div>
            </div>
            <button class="close-btn" @click="$emit('close')">
              <X :size="18"/>
            </button>
          </div>

          <div class="modal-body result-body">
            <div class="result-layout">

              <div class="result-left">
                <div class="image-tabs">
                  <button class="img-tab" :class="{ active: imgView === 'original' }"
                          @click="imgView = 'original'">Оригинал
                  </button>
                  <button class="img-tab" :class="{ active: imgView === 'overlay' }"
                          @click="imgView = 'overlay'">Разметка
                  </button>
                  <button class="img-tab" :class="{ active: imgView === 'student' }"
                          @click="imgView = 'student'">Ваши точки
                  </button>
                </div>

                <!-- Оригинал и разметка — обычный image-view -->
                <div v-if="imgView !== 'student'" class="image-view">
                  <img v-if="imgView === 'original'" :src="previewUrl" class="result-img"/>
                  <img v-else-if="imgView === 'overlay'" :src="result.overlay_url || previewUrl" class="result-img"/>
                  <button class="fullscreen-btn" @click="openFullscreen">
                    <Maximize2 :size="16"/>
                  </button>
                  <div class="img-label-badge">
                    {{ imgView === 'original' ? 'Оригинал' : 'Разметка' }}
                  </div>
                </div>

                <div v-else class="image-view"
                     style="height:auto; min-height:340px; position: relative; overflow: hidden;">
                  <!-- Вкладка "Ваши точки" — без фиксированной высоты, SVG overlay -->

                  <div style="position: relative; width: 100%; height: 100%; line-height: 0;">

                    <img
                        :src="previewUrl"
                        style="width:100%; height:100%; object-fit:contain; display:block; pointer-events: none;"
                    />

                    <svg
                        style="position:absolute; top:0; left:0; width:100%; height:100%; pointer-events:none"
                        viewBox="0 0 1000 1000"
                        preserveAspectRatio="none"
                    >
                      <line
                          v-if="studentLines?.hilgenreiner"
                          :x1="0"
                          :y1="studentLines.hilgenreiner.y1 * 1000"
                          :x2="1000"
                          :y2="studentLines.hilgenreiner.y1 * 1000"
                          :stroke="POINT_COLORS.A"
                          stroke-width="3"
                          stroke-dasharray="15 6"
                          opacity="0.9"
                      />

                      <line
                          v-if="studentLines?.perkin_left"
                          :x1="studentLines.perkin_left.x1 * 1000"
                          :y1="0"
                          :x2="studentLines.perkin_left.x1 * 1000"
                          :y2="1000"
                          :stroke="POINT_COLORS.B"
                          stroke-width="2.5"
                          stroke-dasharray="10 5"
                          opacity="0.85"
                      />

                      <line
                          v-if="studentLines?.perkin_right"
                          :x1="studentLines.perkin_right.x1 * 1000"
                          :y1="0"
                          :x2="studentLines.perkin_right.x1 * 1000"
                          :y2="1000"
                          :stroke="POINT_COLORS.B"
                          stroke-width="2.5"
                          stroke-dasharray="10 5"
                          opacity="0.85"
                      />

                      <line
                          v-for="(pt, key) in result.correct_points"
                          :key="'diff_' + key"
                          v-if="studentPoints[key]"
                          :x1="studentPoints[key].x * 1000"
                          :y1="studentPoints[key].y * 1000"
                          :x2="pt.x * 1000"
                          :y2="pt.y * 1000"
                          stroke="#facc15"
                          stroke-width="2"
                          stroke-dasharray="5 3"
                          opacity="0.8"
                      />

                      <circle
                          v-for="(pt, key) in result.correct_points"
                          :key="'c_' + key"
                          :cx="pt.x * 1000"
                          :cy="pt.y * 1000"
                          r="10"
                          :fill="POINT_COLORS[pointCode(key)]"
                          stroke="white"
                          stroke-width="2.5"
                          opacity="0.9"
                      />

                      <circle
                          v-for="(pt, key) in studentPoints"
                          :key="'s_' + key"
                          :cx="pt.x * 1000"
                          :cy="pt.y * 1000"
                          r="10"
                          :fill="POINT_COLORS[pointCode(key)]"
                          stroke="#ef4444"
                          stroke-width="2.5"
                      />
                    </svg>

                    <!-- Легенда внутри position:relative контейнера -->
                    <div class="edu-legend">
                      <div class="edu-legend-row">
                        <span class="edu-legend-dot" :style="{ backgroundColor: POINT_COLORS.A }"></span>
                        <span class="edu-legend-label">A — TCC</span>
                        <span class="edu-legend-dot" :style="{ backgroundColor: POINT_COLORS.B }"></span>
                        <span class="edu-legend-label">B — ASM</span>
                        <span class="edu-legend-dot" :style="{ backgroundColor: POINT_COLORS.C }"></span>
                        <span class="edu-legend-label">C — FHC</span>
                        <span class="edu-legend-dot" :style="{ backgroundColor: POINT_COLORS.H }"></span>
                        <span class="edu-legend-label">H — MOFM</span>
                      </div>
                      <div class="edu-legend-row">
                        <span class="edu-legend-line" :style="{ backgroundColor: POINT_COLORS.A }"></span>
                        <span class="edu-legend-label">━ Хильгенрейнера</span>
                        <span class="edu-legend-line dashed" :style="{ backgroundColor: POINT_COLORS.B }"></span>
                        <span class="edu-legend-label">╌ Перкина</span>
                        <span class="edu-legend-line dashed" style="background-color:#facc15;"></span>
                        <span class="edu-legend-label">╌ Отклонение</span>
                      </div>
                    </div>

                    <!-- Кнопка fullscreen тоже внутри position:relative -->
                    <button class="fullscreen-btn" @click="openFullscreen" style="pointer-events: auto; z-index: 10;">
                      <Maximize2 :size="16"/>
                    </button>

                    <div class="img-label-badge">Ваши точки vs правильные</div>

                  </div>

                </div>
              </div>

              <!-- RIGHT: Results -->
              <div class="result-right">

                <!-- Итоговый балл -->
                <div class="edu-score-card"
                     :class="result.total_score >= 70 ? 'success'
                                    : result.total_score >= 50 ? 'warning' : 'danger'">
                  <div class="edu-score-value">{{ result.total_score }}</div>
                  <div class="edu-score-label">Итоговый балл</div>
                  <div class="edu-score-breakdown">
                    <span>Точки: {{ result.points_accuracy?.score || 0 }}%</span>
                    <span>Признаки: {{
                        result.qual_feedback?.length
                            ? Math.round(result.qual_feedback.filter(q => q.is_correct).length / result.qual_feedback.length * 100)
                            : 0
                      }}%</span>
                    <span>Диагноз: {{ result.diagnosis?.is_correct ? '100%' : '0%' }}</span>
                  </div>
                  <div v-if="hasPointsWithoutReference"
                       style="margin-top:0.5rem;font-size:0.72rem;color:var(--text-muted);text-align:center">
                    * Балл считается без точек C (FHC) — головка хрящевая
                  </div>
                </div>

                <!-- Точность точек -->
                <div class="zones-section">
                  <h4 class="section-title">Точки ({{ result.points_accuracy?.score || 0 }}%)</h4>
                  <div class="zones-list">
                    <div
                        v-for="(point, key) in result.points_accuracy?.points"
                        :key="key"
                        class="zone-item"
                    >
                      <!-- Точка с эталоном — обычная оценка -->
                      <template v-if="point.has_reference !== false">
                                                <span
                                                    class="zone-severity"
                                                    :class="point.grade === 'excellent' ? 'low'
                                                        : point.grade === 'good' ? 'medium' : 'high'"
                                                >
                                                    {{ point.grade_label }}
                                                </span>
                        <div class="zone-info">
                          <span style="font-weight:500">{{ point.label }}</span>
                          <span
                              v-if="point.distance_px != null"
                              style="font-size:0.75rem;color:var(--text-muted)"
                          >
                                                        {{ Math.round(point.distance_px) }}px
                                                    </span>
                        </div>
                      </template>

                      <!-- Точка без эталона — FHC хрящевая головка -->
                      <template v-else>
                                                <span
                                                    class="zone-severity"
                                                    style="background:var(--warning-light);color:var(--warning);white-space:nowrap"
                                                >
                                                    Без эталона
                                                </span>
                        <div class="zone-info">
                          <span style="font-weight:500">{{ point.label }}</span>
                          <span
                              style="font-size:0.75rem;color:var(--text-muted);line-height:1.4"
                          >
                                                        {{
                              point.student
                                  ? "Точка принята. Головка бедра хрящевая — автоматическая проверка недоступна. Алгоритм использует метод IHDI без этой точки."
                                  : "Точка пропущена. Головка бедра хрящевая — не видна на рентгене. Диагноз рассчитан без FHC по методу IHDI."
                            }}
                                                    </span>
                        </div>
                      </template>
                    </div>
                  </div>
                </div>

                <!-- Качественные признаки -->
                <div class="zones-section">
                  <h4 class="section-title">Качественные признаки</h4>
                  <div class="zones-list">
                    <div v-for="(q, idx) in result.qual_feedback" :key="idx" class="zone-item">
                                        <span class="zone-severity" :class="q.is_correct ? 'low' : 'high'">
                                        {{ q.is_correct ? 'Верно' : 'Неверно' }}
                                        </span>
                      <div class="zone-info">
                        <span style="font-weight:500">{{ q.field }}</span>
                        <span style="font-size:0.75rem;color:var(--text-muted)">
                                            Вы: {{ q.student || '(не указано)' }} → {{ q.correct }}
                                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- Диагноз — без дублирования -->
                <div class="zones-section">
                  <h4 class="section-title">Диагноз</h4>
                  <div class="diagnosis-card"
                       :class="result.diagnosis?.is_correct ? 'normal' : 'pathology'"
                       style="margin-bottom:0.75rem">
                    <div class="diag-left">
                      <span class="diag-status-label">Ваш ответ</span>
                      <span class="diag-label" style="font-size:1.1rem">
                                        {{ result.diagnosis?.student }}
                                        </span>
                    </div>
                    <div class="diag-left">
                      <span class="diag-status-label">Правильный</span>
                      <span class="diag-label" style="font-size:1.1rem">
                                        {{ result.diagnosis?.correct }}
                                        </span>
                    </div>
                  </div>
                  <!-- Развёрнутое описание — отдельно, не дублирует -->
                  <div v-if="result.diagnosis?.full_description"
                       class="clinical-note"
                       style="white-space:pre-line;font-size:0.78rem">
                    {{ result.diagnosis.full_description }}
                  </div>
                </div>

              </div>

            </div>
            <div class="modal-footer">
              <button class="btn-ghost" @click="$emit('close')">Закрыть</button>
            </div>
          </div>
        </template>
        <template v-else>
          <div class="modal-header">
            <div class="modal-title-group">
              <div
                  class="modal-icon"
                  :class="
                                    result.diagnosis.is_pathology
                                        ? 'danger-icon'
                                        : 'success-icon'
                                "
              >
                <AlertCircle
                    v-if="result.diagnosis.is_pathology"
                    :size="20"
                />
                <CheckCircle v-else :size="20"/>
              </div>
              <div>
                <h2 class="modal-title">Результат анализа</h2>
                <p class="modal-subtitle">
                  ID: {{ result.request_id }} ·
                  {{ modalities.find(m => m.value === selectedAnalyzer)?.label || modality }}
                </p>
              </div>
            </div>
            <button class="close-btn" @click="$emit('close')">
              <X :size="18"/>
            </button>
          </div>
          <div class="modal-body result-body">
            <div class="result-layout">
              <div class="result-left">
                <div class="image-tabs">
                  <button
                      class="img-tab"
                      :class="{ active: imgView === 'original' }"
                      @click="imgView = 'original'"
                  >
                    Оригинал
                  </button>
                  <!-- Advanced: табы GradCAM — только если есть патологии -->
                  <template v-if="result.analyzer_id === 'xray_advanced' && result.diagnosis.is_pathology">
                    <button v-for="(gc, idx) in result.extra?.gradcam_multi"
                            :key="gc.pathology"
                            class="img-tab"
                            :class="{
                                            active:
                                                imgView === 'gradcam_' + idx,
                                        }"
                            @click="imgView = 'gradcam_' + idx"
                    >
                                        <span
                                            class="tab-severity-dot"
                                            :class="gc.severity"
                                        ></span>
                      {{ gc.pathology_ru }}
                    </button>
                  </template>
                  <!-- Standard xray / microscopy / hip dysplasia -->
                  <template v-else-if="result.analyzer_id !== 'xray_advanced'">
                    <button
                        v-if="
                                            result.gradcam || result.microscopy || result.hip_dysplasia
                                        "
                        class="img-tab"
                        :class="{
                                            active: imgView === 'overlay',
                                        }"
                        @click="imgView = 'overlay'"
                    >
                      {{ result.hip_dysplasia ? "Разметка" : "Наложение" }}
                    </button>
                    <button
                        v-if="result.gradcam"
                        class="img-tab"
                        :class="{
                                            active: imgView === 'heatmap',
                                        }"
                        @click="imgView = 'heatmap'"
                    >
                      Карта
                    </button>
                  </template>
                </div>
                <div class="image-view">
                  <img
                      v-if="imgView === 'original'"
                      :src="previewUrl"
                      class="result-img"
                  />
                  <!-- Advanced GradCAM viewer -->
                  <template v-else-if="result.analyzer_id === 'xray_advanced' && imgView.startsWith('gradcam_')">
                    <div class="gradcam-view-toggle">
                      <button
                          class="gcv-btn"
                          :class="{
                                                active: gcSubView === 'overlay',
                                            }"
                          @click="gcSubView = 'overlay'"
                      >
                        Наложение
                      </button>
                      <button
                          class="gcv-btn"
                          :class="{
                                                active: gcSubView === 'heatmap',
                                            }"
                          @click="gcSubView = 'heatmap'"
                      >
                        Карта
                      </button>
                    </div>
                    <img
                        :src="
                                                gcSubView === 'overlay'
                                                    ? result.extra?.gradcam_multi?.[activeGradcamIdx]?.overlay_url
                                                    : result.extra?.gradcam_multi?.[activeGradcamIdx]?.heatmap_url
                                            "
                        class="result-img"
                    />
                  </template>
                  <!-- Standard / Hip dysplasia -->
                  <img
                      v-else-if="imgView === 'overlay'"
                      :src="
                                        result.gradcam?.overlay_url ||
                                        result.microscopy?.overlay_url ||
                                        result.hip_dysplasia?.overlay_url
                                    "
                      class="result-img"
                  />
                  <img
                      v-else-if="imgView === 'heatmap'"
                      :src="
                                        result.gradcam?.heatmap_url ||
                                        result.hip_dysplasia?.heatmap_url
                                    "
                      class="result-img"
                  />
                  <button class="fullscreen-btn" @click="openFullscreen">
                    <Maximize2 :size="16"/>
                  </button>
                  <div class="img-label-badge">
                    {{ imgViewLabel }}
                  </div>
                </div>
              </div>
              <div class="result-right">
                <div
                    class="diagnosis-card"
                    :class="
                                    result.diagnosis.is_pathology
                                        ? 'pathology'
                                        : 'normal'
                                "
                >
                  <div class="diag-left">
                                    <span class="diag-status-label"
                                    >Диагноз</span
                                    >
                    <span class="diag-label">{{
                        result.diagnosis.label
                      }}</span>
                  </div>
                  <div
                      class="diag-right"
                      v-if="result.diagnosis.confidence !== null"
                  >
                    <div class="confidence-ring">
                      <svg
                          viewBox="0 0 36 36"
                          class="conf-svg"
                      >
                        <path
                            class="conf-bg"
                            d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                        />
                        <path
                            class="conf-fill"
                            :style="{
                                                    strokeDasharray: `${result.diagnosis.confidence * 100}, 100`,
                                                }"
                            d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                        />
                      </svg>
                      <span class="conf-value">
                                            {{
                          Math.round(
                              result.diagnosis
                                  .confidence * 100,
                          )
                        }}%
                                        </span>
                    </div>
                    <span class="conf-label">Уверенность</span>
                  </div>
                </div>
                <!-- Advanced: чистый снимок -->
                <div v-if="result.analyzer_id === 'xray_advanced' && !result.diagnosis.is_pathology"
                     class="clean-notice">
                  <CheckCircle :size="16"/>
                  Признаков патологий не обнаружено. Все
                  показатели ниже порога уверенности.
                </div>
                <!-- Advanced: топ-3 GradCAM + detected — только если патологии есть -->
                <div v-if="result.analyzer_id === 'xray_advanced' && result.diagnosis.is_pathology"
                     class="zones-section">
                  <h4 class="section-title">
                    Grad-CAM · Топ-3 патологии
                  </h4>
                  <div class="gradcam-cards">
                    <div v-for="(gc, idx) in result.extra?.gradcam_multi"
                         :key="gc.pathology"
                         class="gradcam-card"
                         :class="{
                                            active:
                                                imgView === 'gradcam_' + idx,
                                            [gc.severity]: true,
                                        }"
                         @click="imgView = 'gradcam_' + idx"
                    >
                      <div class="gc-card-left">
                                            <span class="gc-rank"
                                            >#{{ idx + 1 }}</span
                                            >
                        <div class="gc-info">
                                                <span class="gc-name">{{
                                                    gc.pathology_ru
                                                  }}</span>
                          <span class="gc-score"
                          >{{
                              Math.round(
                                  gc.score * 100,
                              )
                            }}%</span
                          >
                        </div>
                      </div>
                      <span
                          class="zone-severity"
                          :class="gc.severity"
                      >
                                            {{ severityLabel(gc.severity) }}
                                        </span>
                    </div>
                  </div>
                  <template v-if="result.extra?.detected?.length">
                    <h4
                        class="section-title"
                        style="margin-top: 1rem"
                    >
                      Все обнаруженные ({{ result.extra?.detected_count }})
                    </h4>
                    <div class="zones-list">
                      <div v-for="p in result.extra?.detected"
                           :key="p.name"
                           class="zone-item"
                      >
                                            <span class="zone-id"
                                            >{{
                                                Math.round(p.score * 100)
                                              }}%</span
                                            >
                        <div class="zone-info">
                                                <span
                                                    style="font-weight: 500"
                                                >{{ p.name_ru }}</span
                                                >
                        </div>
                        <span
                            class="zone-severity"
                            :class="p.severity"
                        >
                                                {{ severityLabel(p.severity) }}
                                            </span>
                      </div>
                    </div>
                  </template>
                </div>
                <div
                    v-else-if="
                                    result.gradcam?.pathology_zones?.length
                                "
                    class="zones-section"
                >
                  <h4 class="section-title">
                    Зоны патологий ({{
                      result.gradcam.zones_count
                    }})
                  </h4>
                  <div class="zones-list">
                    <div
                        v-for="zone in result.gradcam
                                            .pathology_zones"
                        :key="zone.zone_id"
                        class="zone-item"
                    >
                                        <span class="zone-id"
                                        >#{{ zone.zone_id }}</span
                                        >
                      <div class="zone-info">
                                            <span class="zone-area"
                                            >{{ zone.area_percent }}%
                                                площади</span
                                            >
                      </div>
                      <span
                          class="zone-severity"
                          :class="zone.severity"
                      >
                                            {{ severityLabel(zone.severity) }}
                                        </span>
                    </div>
                  </div>
                </div>
                <div v-else-if="result.hip_dysplasia" class="zones-section">
                  <h4 class="section-title">
                    Результаты анализа дисплазии ТБС
                  </h4>
                  <div class="hip-metrics">
                    <div
                        v-for="metric in result.hip_dysplasia.metrics"
                        :key="metric.name"
                        class="hip-metric-row"
                    >
                      <span class="hip-metric-label">{{ metric.name_ru }}</span>
                      <div class="hip-metric-right">
                        <span class="hip-metric-value">{{ metric.value }}</span>
                        <span
                            class="hip-metric-classification"
                            :class="metric.color"
                        >
                                                {{ metric.classification }}
                                            </span>
                      </div>
                    </div>
                  </div>
                  <div class="clinical-note" style="margin-top: 0.75rem; white-space: pre-line">
                    {{ result.hip_dysplasia.overall_diagnosis }}
                  </div>
                  <div
                      v-if="result.hip_dysplasia.educational_info"
                      class="clinical-note"
                      style="margin-top: 0.5rem; white-space: pre-line; font-size: 0.78rem"
                  >
                    {{ result.hip_dysplasia.educational_info }}
                  </div>
                </div>
                <div v-if="result.microscopy" class="zones-section">
                  <h4 class="section-title">
                    Клетки обнаружены ({{
                      result.microscopy.total_cells
                    }})
                  </h4>
                  <div class="cell-table">
                    <div class="cell-row cell-row--head">
                      <span>Тип</span><span>Кол-во</span
                    ><span>%</span>
                    </div>
                    <div
                        v-for="cc in cellCountsList"
                        :key="cc.cell_type"
                        class="cell-row"
                    >
                                        <span class="cell-type">
                                            <span
                                                class="cell-dot"
                                                :style="{
                                                    background: cellColor(
                                                        cc.cell_type,
                                                    ),
                                                }"
                                            ></span>
                                            {{ cc.cell_type }}
                                        </span>
                      <span class="cell-count">{{
                          cc.count
                        }}</span>
                      <span class="cell-pct"
                      >{{ cc.percent }}%</span
                      >
                    </div>
                  </div>
                  <div
                      class="ratio-badge"
                      v-if="result.microscopy.wbc_rbc_ratio"
                  >
                    WBC/RBC:
                    <strong>{{
                        result.microscopy.wbc_rbc_ratio
                      }}</strong>
                  </div>
                  <div
                      class="clinical-note"
                      v-if="result.microscopy.clinical_note"
                  >
                    {{ result.microscopy.clinical_note }}
                  </div>
                  <div
                      v-if="microscopySummary.length"
                      class="microscopy-summary"
                  >
                    <div
                        v-for="item in microscopySummary"
                        :key="item.key"
                        class="microscopy-summary-item"
                        :class="item.status"
                    >
                      <div class="microscopy-summary-row">
                        <span class="microscopy-summary-label">{{ item.label }}</span>
                        <span class="microscopy-summary-value">{{ item.value }}</span>
                      </div>
                      <div class="microscopy-summary-row">
                        <span class="microscopy-summary-details">{{ item.details }}</span>
                        <span class="microscopy-summary-status">{{ item.statusText }}</span>
                      </div>
                    </div>
                  </div>
                </div>
                <div class="comment-section">
                  <label class="field-label"
                  >Комментарий врача</label
                  >
                  <textarea
                      v-model="comment"
                      class="comment-input"
                      placeholder="Введите комментарий по результатам исследования..."
                      rows="4"
                  ></textarea>
                </div>
              </div>
            </div>
          </div>
          <div class="modal-footer">
            <button class="btn-ghost" @click="$emit('close')">
              Закрыть
            </button>
            <button
                v-if="!result._is_educational"
                class="btn-save"
                :class="{ saving: saving, saved: saved }"
                @click="saveExamination"
                :disabled="saving || saved"
            >
              <Save v-if="!saved" :size="16"/>
              <Check v-else :size="16"/>
              {{
                saved
                    ? "Сохранено"
                    : saving
                        ? "Сохранение..."
                        : "Сохранить"
              }}
            </button>
          </div>
        </template>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import {computed, onMounted, ref, watch} from "vue";
import axios from "axios";
import {
  Activity,
  AlertCircle,
  Check,
  CheckCircle,
  ChevronLeft,
  ChevronRight,
  FileText,
  Grid2x2,
  Info,
  Maximize2,
  Save,
  ScanLine,
  Search,
  ShieldCheck,
  Upload,
  X,
  Zap,
} from "lucide-vue-next";

const emit = defineEmits(["close"]);

const step = ref("upload");
const selectedAnalyzer = ref("hip_dysplasia");
const xrayModel = ref("standard"); // "standard" | "advanced"
const mode = ref("doctor"); // "doctor" | "educational"
const eduPhase = ref("intro"); // intro | points | form

// Вычисляемая модальность для совместимости с существующими v-if в шаблоне
const modality = computed(() => {
  const found = modalities.value.find(m => m.value === selectedAnalyzer.value);
  return found?.modality || "xray";
});

const file = ref(null);
const fileName = ref("");
const previewUrl = ref("");
const dicomFile = ref(false);
const dicomDetected = ref(false);
const patientAgeValue = ref("");
const patientAgeUnit = ref("years");
const detectedPatientAgeMonths = ref(null);
const detectedPatientAgeSource = ref("");
const fileInput = ref(null);
const isDragging = ref(false);
const result = ref(null);
const comment = ref("");
const saving = ref(false);
const saved = ref(false);
const imgView = ref("overlay");
const gcSubView = ref("overlay"); // "overlay" | "heatmap" внутри advanced gradcam
const loadStep = ref(0);

// Образовательный режим
const studentPoints = ref({}); // {point_name: {x, y}}
const skippedPoints = ref(new Set()); // опциональные точки, которые студент пропустил
const currentPointIndex = ref(0);
const studentQualitative = ref({
  shenton_left: "",
  shenton_right: "",
  ossif_left: "",
  ossif_right: "",
});
const studentDiagnosis = ref("");
const eduResult = ref(null);
const showHintDetails = ref(false);

// Порядок точек для расстановки
const POINT_ORDER = [
  {
    key: "tcc_left", code: "A", side: "left",
    label: "A — TCC левый",
    hint: "Центр Y-образного хряща слева",
    hint_extended: "Найдите место где сходятся три кости таза. Тёмная точка внутри вертлужной впадины — пересечение подвздошной, лобковой и седалищной костей.",
    anatomy_tip: "Ориентир: самая глубокая точка впадины",
  },
  {
    key: "asm_left", code: "B", side: "left",
    label: "B — ASM левый",
    hint: "Верхний наружный край крыши вертлужной впадины слева",
    hint_extended: "Самая верхняя наружная точка крыши впадины — угол где заканчивается костная крыша.",
    anatomy_tip: "Ориентир: самая выступающая точка крыши сверху",
  },
  {
    key: "fhc_left", code: "C", side: "left", optional: true,
    label: "C — FHC левый",
    hint: "Центр головки бедра слева",
    hint_extended: "Геометрический центр округлой головки бедренной кости. У маленьких детей головка может быть хрящевой и плохо видна на рентгене.",
    anatomy_tip: "Ориентир: центр округлой тени головки бедра",
  },
  {
    key: "mofm_left", code: "H", side: "left",
    label: "H — MOFM левый",
    hint: "Медиальный контур метафиза бедренной кости слева",
    hint_extended: "Внутренний край шейки бедренной кости у её основания — там где шейка переходит в тело кости.",
    anatomy_tip: "Ориентир: внутренний край шейки у основания",
  },
  {
    key: "tcc_right", code: "A", side: "right",
    label: "A — TCC правый",
    hint: "Центр Y-образного хряща справа",
    hint_extended: "Та же точка что слева, но зеркально — центр Y-хряща правой вертлужной впадины.",
    anatomy_tip: "Ориентир: симметрично левому суставу",
  },
  {
    key: "asm_right", code: "B", side: "right",
    label: "B — ASM правый",
    hint: "Верхний наружный край крыши правой вертлужной впадины",
    hint_extended: "Верхний наружный угол правой крыши впадины — симметрично левому.",
    anatomy_tip: "Ориентир: самая выступающая точка крыши справа",
  },
  {
    key: "fhc_right", code: "C", side: "right", optional: true,
    label: "C — FHC правый",
    hint: "Центр головки бедра справа",
    hint_extended: "Геометрический центр правой головки бедренной кости.",
    anatomy_tip: "Ориентир: центр округлой тени справа",
  },
  {
    key: "mofm_right", code: "H", side: "right",
    label: "H — MOFM правый",
    hint: "Медиальный контур метафиза бедренной кости справа",
    hint_extended: "Внутренний край шейки правой бедренной кости у основания.",
    anatomy_tip: "Ориентир: внутренний край шейки справа",
  },
];

const POINT_COLORS = {
  A: "#378ADD",
  B: "#7F77DD",
  C: "#00c896",
  H: "#f59e0b",
};

const currentPoint = computed(() => POINT_ORDER[currentPointIndex.value]);
const pointsProgress = computed(() => `${Object.keys(studentPoints.value).length} / ${POINT_ORDER.length}`);
const showPatientAgeField = computed(
    () =>
        selectedAnalyzer.value === "hip_dysplasia"
        && !!file.value,
);
const detectedAgeHint = computed(() => {
  if (!detectedPatientAgeMonths.value) return "";
  const sourceMap = {
    PatientAge: "Patient Age",
    "PatientBirthDate+StudyDate": "Patient Birth Date + Study Date",
  };
  const source = sourceMap[detectedPatientAgeSource.value] || detectedPatientAgeSource.value || "DICOM";
  return `Возраст найден в DICOM (${source}). Можно изменить при необходимости.`;
});
const patientAgeDisplay = computed(() => {
  if (!patientAgeValue.value) return "";
  return patientAgeUnit.value === "months"
      ? `${patientAgeValue.value} мес`
      : `${patientAgeValue.value} лет`;
});

const modalities = ref([]);
const SKIP_IN_MODAL = new Set(["xray_advanced"]);
const FALLBACK_MODALITIES = [
  {
    value: "xray_pneumonia",
    modality: "xray",
    label: "Рентген лёгких",
    sub: "Пневмония · EfficientNet-B3",
    icon: Grid2x2
  },
  {value: "hip_dysplasia", modality: "xray", label: "Дисплазия ТБС", sub: "YOLO + EfficientNet-B3", icon: ScanLine},
  {
    value: "blood_cells",
    modality: "microscopy",
    label: "Микроскопия крови",
    sub: "Cellpose + EfficientNet-B0",
    icon: Activity
  },
];

function getIconForAnalyzer(analyzerId, analyzerModality) {
  if (analyzerId === "hip_dysplasia") return ScanLine;
  if (analyzerId === "blood_cells" || analyzerModality === "microscopy") return Activity;
  if (analyzerId === "xray_advanced") return Zap;
  return Grid2x2;
}

function getSubtitleForAnalyzer(analyzerId) {
  const subtitles = {
    hip_dysplasia: "YOLO + EfficientNet-B3",
    xray_pneumonia: "Пневмония · EfficientNet-B3",
    blood_cells: "Cellpose + EfficientNet-B0",
    xray_advanced: "DenseNet121 · 18 патологий",
  };
  return subtitles[analyzerId] || "Нейросетевой анализ";
}

function applyModalities(nextModalities) {
  modalities.value = nextModalities;
  if (!modalities.value.length) {
    selectedAnalyzer.value = "";
    return;
  }
  const exists = modalities.value.some((m) => m.value === selectedAnalyzer.value);
  if (!exists) {
    selectedAnalyzer.value = modalities.value[0].value;
  }
}

async function loadAnalyzers() {
  try {
    const res = await axios.get("/api/analyzers");
    const data = res.data || {};
    const loaded = Object.values(data)
        .filter((a) => a && a.id && !SKIP_IN_MODAL.has(a.id))
        .map((a) => ({
          value: a.id,
          modality: a.modality || "xray",
          label: a.name || a.id,
          sub: getSubtitleForAnalyzer(a.id),
          icon: getIconForAnalyzer(a.id, a.modality),
        }));
    applyModalities(loaded.length ? loaded : FALLBACK_MODALITIES);
  } catch (e) {
    console.error("[Modal] Ошибка загрузки анализаторов:", e);
    applyModalities(FALLBACK_MODALITIES);
  }
}

const modelLabel = computed(() => {
  if (selectedAnalyzer.value === "hip_dysplasia") return "YOLO + EfficientNet-B3";
  if (selectedAnalyzer.value === "blood_cells") return "Cellpose + EfficientNet-B0";
  return xrayModel.value === "advanced"
      ? "DenseNet121 · 18 патологий"
      : "EfficientNet-B3 + Grad-CAM";
});

const activeGradcamIdx = computed(() => {
  if (!imgView.value.startsWith("gradcam_")) return 0;
  return parseInt(imgView.value.split("_")[1]) || 0;
});

const imgViewLabel = computed(() => {
  if (imgView.value === "original") return "Оригинал";
  if (imgView.value === "overlay") {
    if (result.value?.microscopy) return "Детекция клеток";
    if (result.value?.hip_dysplasia) return "Разметка YOLO";
    return "Наложение Grad-CAM";
  }
  if (imgView.value === "heatmap") {
    if (result.value?.hip_dysplasia) return "Оригинал";
    return "Тепловая карта";
  }
  if (imgView.value.startsWith("gradcam_") && result.value?.analyzer_id === "xray_advanced") {
    const gc = result.value.extra?.gradcam_multi?.[activeGradcamIdx.value];
    const sub = gcSubView.value === "heatmap" ? "Карта" : "Наложение";
    return gc ? `${sub} · ${gc.pathology_ru}` : sub;
  }
  return "";
});

function severityLabel(s) {
  return {low: "Низкая", medium: "Средняя", high: "Высокая"}[s] || s;
}

const CELL_COLORS = {
  Basophil: "#8b5cf6",
  Eosinophil: "#f59e0b",
  Neutrophils: "#ef4444",
  Platelets: "#00c896",
  RBC: "#ec4899",
};

function cellColor(cellType) {
  return CELL_COLORS[cellType] || "#888";
}

const cellCountsList = computed(() => {
  const cc = result.value?.microscopy?.cell_counts;
  if (!cc) return [];
  return Object.entries(cc)
      .filter(([, count]) => count > 0)
      .map(([cell_type, count]) => ({
        cell_type,
        count,
        percent:
            result.value.microscopy.total_cells > 0
                ? Math.round(
                (count / result.value.microscopy.total_cells) * 1000,
            ) / 10
                : 0,
      }))
      .sort((a, b) => b.count - a.count);
});

const microscopySummary = computed(() => {
  const backendSummary = result.value?.extra?.microscopy_summary;
  if (Array.isArray(backendSummary) && backendSummary.length) {
    return backendSummary.map((item) => ({
      key: item.key || item.label,
      label: item.label || "Показатель",
      value: item.value ?? "-",
      details: item.details || "",
      status: item.status === "normal" ? "normal" : "abnormal",
      statusText: item.status_text || (item.status === "normal" ? "В норме" : "Вне нормы"),
    }));
  }

  const microscopy = result.value?.microscopy;
  if (!microscopy) return [];
  const counts = microscopy.cell_counts || {};
  const total = microscopy.total_cells || 0;
  const rbc = counts.RBC || 0;
  const wbc = counts.WBC || 0;
  const platelets = counts.Platelets || 0;
  const hasRatio = rbc > 0 && wbc > 0;
  const ratio = hasRatio ? rbc / wbc : 0;

  return [
    {
      key: "cells_detected",
      label: "Клетки на изображении",
      value: total,
      details: total > 0 ? "Клетки обнаружены" : "Клетки не обнаружены",
      status: total > 0 ? "normal" : "abnormal",
      statusText: total > 0 ? "В норме" : "Вне нормы",
    },
    {
      key: "wbc_rbc_ratio",
      label: "Соотношение RBC/WBC",
      value: hasRatio ? `${ratio.toFixed(1)}:1` : "Нет данных",
      details: hasRatio
          ? (ratio >= 100 ? "Лейкоциты не повышены относительно эритроцитов" : "Относительно много лейкоцитов")
          : "Недостаточно данных для расчета",
      status: hasRatio && ratio >= 100 ? "normal" : "abnormal",
      statusText: hasRatio && ratio >= 100 ? "В норме" : "Вне нормы",
    },
    {
      key: "platelets",
      label: "Тромбоциты",
      value: platelets,
      details: platelets > 0 ? "Тромбоциты определены" : "Тромбоциты не обнаружены",
      status: platelets > 0 ? "normal" : "abnormal",
      statusText: platelets > 0 ? "В норме" : "Вне нормы",
    },
  ];
});

const studentLines = computed(() => {
  const pts = studentPoints.value;
  // Для построения линий нужны TCC слева/справа и ASM слева/справа
  if (!pts.tcc_left || !pts.tcc_right) return null;

  const hilgY = (pts.tcc_left.y + pts.tcc_right.y) / 2;
  return {
    hilgenreiner: {x1: 0, y1: hilgY, x2: 1, y2: hilgY},
    perkin_left: pts.asm_left ? {x1: pts.asm_left.x, y1: 0, x2: pts.asm_left.x, y2: 1} : null,
    perkin_right: pts.asm_right ? {x1: pts.asm_right.x, y1: 0, x2: pts.asm_right.x, y2: 1} : null,
  };
});

function pointCode(key) {
  const found = POINT_ORDER.find(p => p.key === key);
  return found?.code || "A";
}

watch(currentPointIndex, () => {
  showHintDetails.value = false;
});

watch(step, (newStep) => {
  if (newStep === "upload") {
    loadAnalyzers();
  }
});

const hasPointsWithoutReference = computed(() => {
  const points = result.value?.points_accuracy?.points;
  if (!points) return false;
  return Object.values(points).some((p) => !p.has_reference);
});

function skipCurrentPoint() {
  const currentKey = currentPoint.value.key;
  skippedPoints.value.add(currentKey);

  if (currentPointIndex.value < POINT_ORDER.length - 1) {
    currentPointIndex.value++;
  } else {
    setTimeout(() => {
      step.value = "edu_form";
    }, 300);
  }
}

function onFileChange(e) {
  const f = e.target.files[0];
  if (f) setFile(f);
}

function onDrop(e) {
  isDragging.value = false;
  const f = e.dataTransfer.files[0];
  if (f) setFile(f);
}

function resetPatientAgeState() {
  patientAgeValue.value = "";
  patientAgeUnit.value = "years";
  detectedPatientAgeMonths.value = null;
  detectedPatientAgeSource.value = "";
}

function applyDetectedAgeMonths(ageMonths) {
  if (ageMonths === null || ageMonths === undefined) return;
  detectedPatientAgeMonths.value = ageMonths;
  if (ageMonths < 24) {
    patientAgeUnit.value = "months";
    patientAgeValue.value = String(ageMonths);
    return;
  }
  const years = ageMonths / 12;
  const rounded = Math.round(years * 10) / 10;
  patientAgeUnit.value = "years";
  patientAgeValue.value = Number.isInteger(rounded) ? String(Math.trunc(rounded)) : String(rounded);
}

async function setFile(f) {
  file.value = f
  fileName.value = f.name
  resetPatientAgeState()

  const ext = f.name.includes(".")
      ? f.name.split(".").pop().toLowerCase()
      : ""

  const imageExts = ["jpg", "jpeg", "png", "bmp", "tiff", "webp"]
  const isDefinitelyImage = imageExts.includes(ext) && f.type.startsWith("image/")

  if (isDefinitelyImage) {
    dicomFile.value = false
    dicomDetected.value = false
    const reader = new FileReader()
    reader.onload = (e) => {
      previewUrl.value = e.target.result
    }
    reader.readAsDataURL(f)
  } else {
    // DICOM или файл без расширения — запрашиваем превью с бэка
    dicomFile.value = true
    dicomDetected.value = true
    previewUrl.value = ""

    const formData = new FormData()
    formData.append("file", f)
    try {
      const res = await axios.post("/api/utils/preview", formData)
      if (res.data.preview) {
        previewUrl.value = res.data.preview
        dicomFile.value = false
      }
      if (res.data.patient_age_months !== null && res.data.patient_age_months !== undefined) {
        detectedPatientAgeSource.value = res.data.patient_age_source || ""
        applyDetectedAgeMonths(res.data.patient_age_months)
      }
    } catch (err) {
      console.error("Preview error:", err.response?.data || err.message)
      previewUrl.value = ""
      dicomFile.value = true
    }
  }
}

function normalizeAdvancedResult(data) {
  return {
    request_id: data.request_id,
    modality: "xray",
    model: data.model,
    diagnosis: {
      label: data.top_diagnosis,
      confidence: data.is_pathology ? data.top_score : null,
      is_pathology: data.is_pathology,
    },
    gradcam: data.is_pathology ? data.gradcam : [],
    advanced: {
      detected: data.detected,
      detected_count: data.detected_count,
      pathologies: data.pathologies,
      is_pathology: data.is_pathology,
    },
  };
}

async function submitAnalysis() {
  step.value = "loading";
  loadStep.value = 1;
  const interval = setInterval(() => {
    if (loadStep.value < 3) loadStep.value++;
  }, 800);
  try {
    let res;
    const formData = new FormData();
    formData.append("file", file.value);
    formData.append("modality", modality.value);
    formData.append("analyzer_id", selectedAnalyzer.value);
    if (showPatientAgeField.value && patientAgeValue.value !== "") {
      formData.append("patient_age_value", patientAgeValue.value);
      formData.append("patient_age_unit", patientAgeUnit.value);
    }
    res = await axios.post("/api/analysis/", formData);
    result.value = res.data;
    clearInterval(interval);
    loadStep.value = 4;
    if (result.value.analyzer_id === "xray_advanced") {
      imgView.value = result.value.diagnosis.is_pathology ? "gradcam_0" : "original";
    } else if (result.value.hip_dysplasia) {
      imgView.value = "overlay";
    } else if (result.value.gradcam || result.value.microscopy) {
      imgView.value = "overlay";
    } else {
      imgView.value = "original";
    }
    setTimeout(() => {
      step.value = "result";
    }, 600);
  } catch (err) {
    clearInterval(interval);
    alert("Ошибка анализа: " + (err.response?.data?.detail || err.message));
    step.value = "upload";
  }
}

function resetEducational() {
  studentPoints.value = {};
  skippedPoints.value = new Set();
  currentPointIndex.value = 0;
  studentQualitative.value = {
    shenton_left: "",
    shenton_right: "",
    ossif_left: "",
    ossif_right: "",
  };
  studentDiagnosis.value = "";
  eduResult.value = null;
  eduPhase.value = "intro";
}

function onImageClick(event) {
  if (currentPointIndex.value >= POINT_ORDER.length) return;

  const rect = event.currentTarget.getBoundingClientRect();
  const x = (event.clientX - rect.left) / rect.width;
  const y = (event.clientY - rect.top) / rect.height;

  const currentKey = currentPoint.value.key;
  studentPoints.value[currentKey] = {x, y};

  if (currentPointIndex.value < POINT_ORDER.length - 1) {
    currentPointIndex.value++;
  } else {
    setTimeout(() => {
      step.value = "edu_form";
    }, 300);
  }
}

async function submitEducational() {
  step.value = "loading";
  loadStep.value = 1;
  const interval = setInterval(() => {
    if (loadStep.value < 3) loadStep.value++;
  }, 800);
  try {
    const formData = new FormData();
    formData.append("file", file.value);
    formData.append("analyzer_id", selectedAnalyzer.value);
    formData.append("student_points", JSON.stringify(studentPoints.value));
    formData.append("student_qualitative", JSON.stringify(studentQualitative.value));
    formData.append("student_diagnosis", studentDiagnosis.value);
    if (showPatientAgeField.value && patientAgeValue.value !== "") {
      formData.append("patient_age_value", patientAgeValue.value);
      formData.append("patient_age_unit", patientAgeUnit.value);
    }
    const res = await axios.post("/api/educational/evaluate", formData);
    eduResult.value = res.data;
    eduResult.value._is_educational = true;
    clearInterval(interval);
    loadStep.value = 4;
    setTimeout(() => {
      step.value = "result";
      result.value = eduResult.value;
      imgView.value = "student";
    }, 600);
  } catch (err) {
    clearInterval(interval);
    alert("Ошибка проверки: " + (err.response?.data?.detail || err.message));
    step.value = "edu_form";
  }
}

async function saveExamination() {
  saving.value = true;
  try {
    await axios.post("/api/analysis/save", {
      request_id: result.value.request_id,
      modality: result.value.modality,
      diagnosis_label: result.value.diagnosis.label,
      confidence: result.value.diagnosis.confidence,
      is_pathology: result.value.diagnosis.is_pathology,
      comment: comment.value,
      overlay_url:
          result.value.gradcam?.overlay_url ||
          result.value.microscopy?.overlay_url ||
          result.value.hip_dysplasia?.overlay_url ||
          null,
      zones_count:
          result.value.gradcam?.zones_count ??
          result.value.microscopy?.total_cells ??
          0,
    });
    saved.value = true;
  } catch (err) {
    alert(
        "Ошибка сохранения: " + (err.response?.data?.detail || err.message),
    );
  } finally {
    saving.value = false;
  }
}

function openFullscreen() {
  const view = document.querySelector('.image-view')
  if (!view) return

  if (view.requestFullscreen) {
    view.requestFullscreen()
  } else if (view.webkitRequestFullscreen) {
    view.webkitRequestFullscreen()
  } else if (view.msRequestFullscreen) {
    view.msRequestFullscreen()
  }
}

function openFullscreenEl(el) {
  if (!el) return
  if (el.requestFullscreen) el.requestFullscreen()
  else if (el.webkitRequestFullscreen) el.webkitRequestFullscreen()
}

onMounted(async () => {
  await loadAnalyzers();
  if (modalities.value.length > 0 && !selectedAnalyzer.value) {
    selectedAnalyzer.value = modalities.value[0].value;
  }
});

</script>

<style scoped>
.fullscreen-btn {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 32px;
  height: 32px;
  background: rgba(0, 0, 0, 0.55);
  border: none;
  border-radius: 6px;
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2;
  transition: background 0.15s;
}

.fullscreen-btn:hover {
  background: rgba(0, 0, 0, 0.8);
}
</style>
<style scoped>
/* Главный класс для ВСЕХ медицинских снимков */
.result-img,
.edu-image {
  width: 100% !important;
  height: 100% !important;
  object-fit: contain !important; /* сохраняет пропорции */
  image-rendering: -webkit-optimize-contrast;
  image-rendering: crisp-edges;
  image-rendering: pixelated; /* fallback для старых браузеров */
  image-rendering: crisp-edges; /* Firefox */
  transform: translateZ(0); /* GPU-ускорение */
  will-change: transform;
}

/* Контейнер изображения */
.image-view {
  background: #000 !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  overflow: hidden !important;
  position: relative !important;
}

/* Fullscreen стили */
.image-view:fullscreen,
.image-view:-webkit-full-screen,
.image-view:-moz-full-screen {
  width: 100vw !important;
  height: 100vh !important;
  padding: 0 !important;
  margin: 0 !important;
  background: #000 !important;
}

.backdrop {
  position: fixed;
  inset: 0;
  background: rgba(13, 17, 23, 0.6);
  backdrop-filter: blur(8px);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
  animation: fadeIn 0.2s ease;
}

.modal {
  background: var(--surface);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-lg);
  width: 100%;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.modal-upload {
  max-width: 580px;
}

.modal-confirm {
  max-width: 480px;
}

.modal-loading {
  max-width: 400px;
  padding: 3rem 2rem;
  align-items: center;
}

.modal-result {
  max-width: 900px;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.5rem 1.5rem 0;
  margin-bottom: 15px;
}

.modal-title-group {
  display: flex;
  align-items: center;
  gap: 0.875rem;
}

.modal-icon {
  width: 40px;
  height: 40px;
  background: var(--accent-light);
  color: var(--accent);
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.confirm-icon {
  background: #fff8e6;
  color: var(--warning);
}

.danger-icon {
  background: var(--danger-light);
  color: var(--danger);
}

.success-icon {
  background: var(--success-light);
  color: var(--success);
}

.modal-title {
  font-family: var(--font-display);
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--text-primary);
}

.modal-subtitle {
  font-size: 0.8rem;
  color: var(--text-muted);
  margin-top: 1px;
}

.close-btn {
  width: 34px;
  height: 34px;
  border: 1px solid var(--border);
  background: transparent;
  border-radius: var(--radius-sm);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-muted);
  transition: all 0.15s;
}

.close-btn:hover {
  background: var(--surface-2);
  color: var(--text-primary);
}

.modal-body {
  padding: 1.25rem 1.5rem;
  overflow-y: auto;
  flex: 1;
}

.result-body {
  padding: 0;
}

.modal-footer {
  padding: 1rem 1.5rem;
  border-top: 1px solid var(--border-subtle);
  display: flex;
  gap: 0.75rem;
  justify-content: flex-end;
  background: var(--surface);
}

.field-group {
  margin-bottom: 1.25rem;
}

.field-label {
  display: block;
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 0.5rem;
}

.modality-selector {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.75rem;
}

.modality-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 1rem;
  border: 2px solid var(--border);
  border-radius: var(--radius-md);
  background: var(--surface-2);
  cursor: pointer;
  transition: all 0.2s;
  font-family: var(--font-body);
}

.modality-btn:hover,
.modality-btn.active {
  border-color: var(--accent);
  background: var(--accent-light);
}

.mod-icon {
  color: var(--text-secondary);
}

.modality-btn.active .mod-icon {
  color: var(--accent);
}

.mod-label {
  font-weight: 600;
  font-size: 0.9rem;
  color: var(--text-primary);
}

.mod-sub {
  font-size: 0.72rem;
  color: var(--text-muted);
}

.dropzone {
  border: 2px dashed var(--border);
  border-radius: var(--radius-md);
  min-height: 160px;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}

.dropzone:hover,
.dropzone--active {
  border-color: var(--accent);
  background: var(--accent-light);
}

.dropzone--filled {
  border-style: solid;
  border-color: var(--accent);
}

.dropzone-empty {
  text-align: center;
  padding: 2rem;
}

.dz-icon {
  color: var(--text-muted);
  margin-bottom: 0.75rem;
}

.dz-primary {
  font-weight: 500;
  color: var(--text-secondary);
  margin-bottom: 4px;
}

.dz-secondary {
  font-size: 0.78rem;
  color: var(--text-muted);
}

.dropzone-preview {
  width: 100%;
  min-height: 160px;
  max-height: 300px;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #0d1117;
  overflow: hidden;
}

.preview-img {
  width: 100%;
  height: 100%;
  max-height: 300px;
  object-fit: contain;
  display: block;
}

.preview-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.2s;
  color: white;
  font-weight: 600;
}

.dropzone:hover .preview-overlay {
  opacity: 1;
}

.preview-badge {
  position: absolute;
  bottom: 8px;
  left: 8px;
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  background: rgba(0, 0, 0, 0.7);
  color: white;
  border-radius: 99px;
  font-size: 0.75rem;
  max-width: calc(100% - 16px);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.confirm-card {
  display: flex;
  gap: 1rem;
  padding: 1rem;
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  margin-bottom: 1rem;
}

.confirm-thumb {
  width: 80px;
  height: 80px;
  object-fit: cover;
  border-radius: var(--radius-sm);
  flex-shrink: 0;
}

.confirm-details {
  flex: 1;
}

.confirm-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.4rem 0;
  border-bottom: 1px solid var(--border-subtle);
  font-size: 0.85rem;
  gap: 0.75rem;
}

.confirm-row:last-child {
  border-bottom: none;
}

.age-input-row {
  display: flex;
  gap: 8px;
  align-items: center;
}

.age-input {
  flex: 1;
  min-width: 0;
  padding: 10px 12px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--surface-2);
  color: var(--text-primary);
  font-size: 0.9rem;
}

.age-select {
  width: 110px;
  padding: 10px 12px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--surface-2);
  color: var(--text-primary);
  font-size: 0.9rem;
}

.age-hint {
  margin-top: 6px;
  font-size: 0.76rem;
  color: var(--text-muted);
}

.confirm-key {
  color: var(--text-muted);
  flex: 0 0 auto;
}

.confirm-val {
  font-weight: 500;
  text-align: right;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 150px;
}

.confirm-badge {
  padding: 2px 10px;
  border-radius: 99px;
  font-size: 0.78rem;
}

.confirm-badge.xray {
  background: var(--accent-light);
  color: var(--accent);
}

.confirm-badge.usg {
  background: var(--success-light);
  color: var(--success);
}

.confirm-notice {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  font-size: 0.78rem;
  color: var(--text-muted);
  padding: 0.75rem;
  background: var(--warning-light);
  border-radius: var(--radius-sm);
  line-height: 1.5;
}

.loading-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  text-align: center;
}

.loading-visual {
  position: relative;
  width: 80px;
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 0.5rem;
}

.loading-ring {
  position: absolute;
  width: 80px;
  height: 80px;
  border-radius: 50%;
  border: 2px solid transparent;
  border-top-color: var(--accent);
  animation: spin 1s linear infinite;
}

.loading-ring--2 {
  width: 64px;
  height: 64px;
  border-top-color: rgba(0, 102, 255, 0.3);
  animation-duration: 0.7s;
  animation-direction: reverse;
}

.loading-inner {
  position: absolute;
  width: 44px;
  height: 44px;
  background: var(--accent-light);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.loading-title {
  font-family: var(--font-display);
  font-size: 1.1rem;
  font-weight: 700;
}

.loading-sub {
  font-size: 0.85rem;
  color: var(--text-muted);
}

.loading-steps {
  display: flex;
  flex-direction: column;
  gap: 6px;
  width: 100%;
  margin-top: 0.5rem;
}

.lstep {
  padding: 8px 14px;
  border-radius: var(--radius-sm);
  font-size: 0.82rem;
  color: var(--text-muted);
  background: var(--surface-2);
  text-align: left;
  transition: all 0.3s;
}

.lstep.active {
  background: var(--accent-light);
  color: var(--accent);
  font-weight: 500;
}

.lstep.done {
  background: var(--success-light);
  color: var(--success);
}

.result-layout {
  display: grid;
  grid-template-columns: 340px 1fr;
  gap: 1.25rem;
  align-items: start;
}

.result-left {
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  overflow: hidden;
  flex-shrink: 0;
}

.result-right {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  min-width: 0;
}

.image-tabs {
  display: flex;
  border-bottom: 1px solid var(--border);
  background: var(--surface-2);
  flex-wrap: wrap;
}

.img-tab {
  padding: 7px 12px;
  border: none;
  background: transparent;
  font-family: var(--font-body);
  font-size: 0.78rem;
  color: var(--text-muted);
  cursor: pointer;
  transition: all 0.15s;
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
  white-space: nowrap;
  display: flex;
  align-items: center;
  gap: 5px;
}

.img-tab.active {
  color: var(--accent);
  border-bottom-color: var(--accent);
  font-weight: 500;
}

.img-tab:hover:not(.active) {
  color: var(--text-secondary);
}

.image-view {
  position: relative;
  width: 100%;
  height: 340px;
  background: #0d1117;
  display: flex;
  align-items: center;
  justify-content: center;
}

.result-img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.img-label-badge {
  position: absolute;
  bottom: 8px;
  right: 8px;
  padding: 3px 10px;
  background: rgba(0, 0, 0, 0.6);
  color: white;
  border-radius: 99px;
  font-size: 0.72rem;
}

.diagnosis-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.25rem;
  border-radius: var(--radius-md);
  border: 1px solid;
}

.diagnosis-card.normal {
  background: var(--success-light);
  border-color: rgba(0, 200, 150, 0.3);
}

.diagnosis-card.pathology {
  background: var(--danger-light);
  border-color: rgba(239, 68, 68, 0.3);
}

.diag-status-label {
  font-size: 0.75rem;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  display: block;
  margin-bottom: 4px;
}

.diag-label {
  font-family: var(--font-display);
  font-size: 1.4rem;
  font-weight: 700;
}

.diagnosis-card.normal .diag-label {
  color: var(--success);
}

.diagnosis-card.pathology .diag-label {
  color: var(--danger);
}

.diag-right {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.confidence-ring {
  position: relative;
  width: 60px;
  height: 60px;
}

.conf-svg {
  transform: rotate(-90deg);
  width: 60px;
  height: 60px;
}

.conf-bg {
  fill: none;
  stroke: rgba(0, 0, 0, 0.08);
  stroke-width: 3;
}

.conf-fill {
  fill: none;
  stroke-width: 3;
  stroke-linecap: round;
  transition: stroke-dasharray 1s ease;
}

.diagnosis-card.normal .conf-fill {
  stroke: var(--success);
}

.diagnosis-card.pathology .conf-fill {
  stroke: var(--danger);
}

.conf-value {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-family: var(--font-display);
  font-size: 0.85rem;
  font-weight: 700;
}

.conf-label {
  font-size: 0.72rem;
  color: var(--text-muted);
}

.section-title {
  font-family: var(--font-display);
  font-size: 0.85rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--text-secondary);
  margin-bottom: 0.5rem;
}

.zones-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.zone-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  background: var(--surface-2);
  border-radius: var(--radius-sm);
  font-size: 0.82rem;
}

.zone-id {
  font-weight: 700;
  color: var(--text-muted);
  min-width: 24px;
}

.zone-info {
  flex: 1;
}

.zone-area {
  color: var(--text-secondary);
}

.zone-severity {
  padding: 2px 10px;
  border-radius: 99px;
  font-size: 0.75rem;
  font-weight: 600;
}

.zone-severity.low {
  background: var(--success-light);
  color: var(--success);
}

.zone-severity.medium {
  background: var(--warning-light);
  color: var(--warning);
}

.zone-severity.high {
  background: var(--danger-light);
  color: var(--danger);
}

.cell-table {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: 0.75rem;
}

.cell-row {
  display: grid;
  grid-template-columns: 1fr 60px 50px;
  align-items: center;
  padding: 6px 10px;
  background: var(--surface-2);
  border-radius: var(--radius-sm);
  font-size: 0.82rem;
}

.cell-row--head {
  background: transparent;
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  padding: 2px 10px;
}

.cell-type {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
}

.cell-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.cell-count {
  font-weight: 600;
  color: var(--text-primary);
}

.cell-pct {
  color: var(--text-muted);
  font-size: 0.78rem;
}

.ratio-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 5px 12px;
  background: var(--accent-light);
  color: var(--accent);
  border-radius: 99px;
  font-size: 0.8rem;
  margin-bottom: 0.5rem;
}

.clinical-note {
  padding: 10px 12px;
  background: var(--warning-light);
  border-left: 3px solid var(--warning);
  border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
  font-size: 0.82rem;
  color: var(--text-secondary);
  line-height: 1.5;
}

.comment-input {
  width: 100%;
  padding: 10px 14px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  font-family: var(--font-body);
  font-size: 0.9rem;
  color: var(--text-primary);
  background: var(--surface-2);
  resize: vertical;
  min-height: 80px;
  transition: border-color 0.2s;
  outline: none;
}

.comment-input:focus {
  border-color: var(--accent);
  background: white;
}

.btn-primary {
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 10px 22px;
  background: var(--accent);
  color: white;
  border: none;
  border-radius: var(--radius-sm);
  font-family: var(--font-body);
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary:hover:not(:disabled) {
  background: var(--accent-dark);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-ghost {
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 10px 18px;
  background: transparent;
  color: var(--text-secondary);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  font-family: var(--font-body);
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-ghost:hover {
  background: var(--surface-2);
}

.btn-save {
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 10px 22px;
  background: var(--text-primary);
  color: white;
  border: none;
  border-radius: var(--radius-sm);
  font-family: var(--font-body);
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-save:hover:not(:disabled) {
  background: #1a2332;
}

.btn-save.saved {
  background: var(--success);
}

.btn-save:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.model-selector {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.model-btn {
  display: flex;
  flex-direction: column;
  gap: 3px;
  padding: 10px 14px;
  border: 1.5px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--surface-2);
  cursor: pointer;
  text-align: left;
  transition: all 0.18s;
}

.model-btn:hover,
.model-btn.active {
  border-color: var(--accent);
  background: var(--accent-light);
}

.model-btn-title {
  font-size: 0.88rem;
  font-weight: 600;
  color: var(--text-primary);
  display: flex;
  align-items: center;
  gap: 6px;
}

.model-btn-sub {
  font-size: 0.75rem;
  color: var(--text-muted);
}

.badge-pro {
  font-size: 0.65rem;
  font-weight: 700;
  padding: 1px 6px;
  background: var(--accent);
  color: white;
  border-radius: 99px;
  letter-spacing: 0.04em;
}


.gradcam-cards {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.gradcam-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 9px 12px;
  border: 1.5px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--surface-2);
  cursor: pointer;
  transition: all 0.18s;
}

.gradcam-card:hover,
.gradcam-card.active {
  border-color: var(--accent);
  background: var(--accent-light);
}

.gc-card-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.gc-rank {
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--text-muted);
  min-width: 20px;
}

.gc-info {
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.gc-name {
  font-size: 0.84rem;
  font-weight: 600;
  color: var(--text-primary);
}

.gc-score {
  font-size: 0.75rem;
  color: var(--text-muted);
}


.gradcam-view-toggle {
  position: absolute;
  top: 10px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 2;
  display: flex;
  background: rgba(0, 0, 0, 0.55);
  border-radius: 99px;
  padding: 3px;
  gap: 2px;
}

.gcv-btn {
  padding: 4px 12px;
  border: none;
  border-radius: 99px;
  font-size: 0.75rem;
  font-weight: 500;
  cursor: pointer;
  background: transparent;
  color: rgba(255, 255, 255, 0.7);
  transition: all 0.15s;
}

.gcv-btn.active {
  background: white;
  color: var(--text-primary);
}


.tab-severity-dot {
  display: inline-block;
  width: 7px;
  height: 7px;
  border-radius: 50%;
  flex-shrink: 0;
}

.tab-severity-dot.high {
  background: var(--danger);
}

.tab-severity-dot.medium {
  background: var(--warning);
}

.tab-severity-dot.low {
  background: var(--success);
}


.hip-metrics {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.hip-metric-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  background: var(--surface-2);
  border-radius: var(--radius-sm);
  font-size: 0.82rem;
  gap: 0.75rem;
}

.hip-metric-label {
  color: var(--text-secondary);
  flex: 1;
}

.hip-metric-right {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.hip-metric-value {
  font-weight: 600;
  color: var(--text-primary);
  min-width: 50px;
  text-align: right;
}

.hip-metric-classification {
  padding: 2px 8px;
  border-radius: 99px;
  font-size: 0.75rem;
  font-weight: 500;
  white-space: nowrap;
}

.hip-metric-classification.green {
  background: var(--success-light);
  color: var(--success);
}

.hip-metric-classification.orange {
  background: var(--warning-light);
  color: var(--warning);
}

.hip-metric-classification.darkorange {
  background: #ff8c42;
  color: #cc5a00;
}

.hip-metric-classification.red {
  background: var(--danger-light);
  color: var(--danger);
}

.hip-metric-classification.gray {
  background: var(--surface-2);
  color: var(--text-muted);
}


.clean-notice {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 14px;
  background: var(--success-light);
  color: var(--success);
  border-radius: var(--radius-sm);
  font-size: 0.84rem;
  font-weight: 500;
  border: 1px solid rgba(0, 200, 150, 0.25);
}


.mode-selector {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.75rem;
}

.mode-btn {
  display: flex;
  flex-direction: column;
  gap: 3px;
  padding: 12px 16px;
  border: 1.5px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--surface-2);
  cursor: pointer;
  text-align: left;
  transition: all 0.18s;
}

.mode-btn:hover,
.mode-btn.active {
  border-color: var(--accent);
  background: var(--accent-light);
}

.mode-btn-title {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--text-primary);
}

.mode-btn-sub {
  font-size: 0.75rem;
  color: var(--text-muted);
}

.modal-educational {
  max-width: 700px;
}

.edu-instruction {
  margin-bottom: 1rem;
}

.edu-progress-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.75rem;
}

.edu-progress-label {
  font-size: 0.8rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--text-muted);
  font-weight: 600;
}

.edu-progress-overall {
  padding: 4px 10px;
  border-radius: 99px;
  background: var(--accent-light);
  color: var(--accent);
  font-size: 0.78rem;
  font-weight: 600;
}

.edu-progress-rows {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  margin-bottom: 0.75rem;
}

.edu-progress-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.edu-progress-side-label {
  font-size: 0.8rem;
  color: var(--text-secondary);
  min-width: 88px;
}

.edu-progress-dots {
  display: flex;
  gap: 0.25rem;
}

.edu-dot-small {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  border-radius: 999px;
  font-size: 0.72rem;
  font-weight: 600;
  color: #fff;
  opacity: 0.4;
  transition: transform 0.15s, box-shadow 0.15s, opacity 0.15s;
}

.edu-dot-small.done {
  opacity: 1;
}

.edu-dot-small.skipped {
  opacity: 0.7;
  color: #111827;
}

.edu-dot-small.current {
  opacity: 1;
  box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.16);
  animation: pulse-dot 1.4s ease-in-out infinite;
}

.edu-current-point {
  margin-top: 0.75rem;
  margin-bottom: 0.75rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.edu-current-code {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.6rem 0.75rem;
  border-radius: var(--radius-md);
  border: 1.5px solid var(--border);
  background: var(--surface-2);
}

.edu-current-code-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  border-radius: 999px;
  color: #fff;
  font-weight: 700;
  font-size: 0.9rem;
}

.edu-current-main {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.edu-current-label {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--text-primary);
}

.edu-current-side-badge {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 0.72rem;
  font-weight: 500;
}

.edu-current-side-badge.left {
  background: rgba(55, 138, 221, 0.12);
  color: #2b76c8;
}

.edu-current-side-badge.right {
  background: rgba(0, 200, 150, 0.12);
  color: #009b72;
}

.edu-hints-block {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.edu-hint-main {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 10px;
  background: var(--warning-light);
  border-radius: var(--radius-sm);
  font-size: 0.86rem;
  color: var(--text-secondary);
}

.edu-hint-anatomy {
  font-size: 0.78rem;
  color: var(--text-muted);
}

.edu-hint-more {
  align-self: flex-start;
  margin-top: 2px;
  padding: 2px 0;
  border: none;
  background: none;
  font-size: 0.78rem;
  color: var(--accent);
  cursor: pointer;
}

.edu-hint-extended {
  margin-top: 4px;
  padding: 8px 10px;
  border-radius: var(--radius-sm);
  background: var(--surface-2);
  font-size: 0.8rem;
  color: var(--text-secondary);
}

.edu-image-container {
  position: relative;
  min-height: 400px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.edu-image {
  max-width: 100%;
  max-height: 500px;
  object-fit: contain;
}

.edu-point-marker {
  position: absolute;
  transform: translate(-50%, -50%);
  pointer-events: none;
  z-index: 10;
}

.edu-point-dot {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: #ef4444;
  border: 2px solid white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
}

.edu-point-label {
  position: absolute;
  top: 20px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(0, 0, 0, 0.8);
  color: white;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.7rem;
  white-space: nowrap;
}

.edu-intro-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.75rem;
}

.edu-intro-card {
  padding: 0.85rem 1rem;
  border-radius: var(--radius-md);
  background: var(--surface-2);
  border: 1px solid var(--border);
}

.edu-intro-header {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  margin-bottom: 0.4rem;
}

.edu-intro-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 999px;
  color: #fff;
  font-weight: 700;
  font-size: 0.9rem;
}

.edu-intro-title {
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
}

.edu-intro-name {
  font-size: 0.88rem;
  font-weight: 600;
  color: var(--text-primary);
}

.edu-intro-side-hint {
  font-size: 0.75rem;
  color: var(--text-muted);
}

.edu-intro-description {
  font-size: 0.8rem;
  color: var(--text-secondary);
  margin-bottom: 0.3rem;
}

.edu-intro-anatomy {
  font-size: 0.78rem;
  color: var(--text-muted);
}

.edu-legend {
  position: absolute;
  bottom: 8px;
  left: 8px;
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 4px 6px;
  background: rgba(0, 0, 0, 0.7);
  border-radius: 8px;
  font-size: 0.68rem;
  color: #fff;
  pointer-events: none;
}

.edu-legend-row {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-wrap: wrap;
}

.edu-legend-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.edu-legend-line {
  width: 20px;
  height: 2px;
  border-radius: 999px;
  flex-shrink: 0;
}

.edu-legend-line.dashed {
  background-image: linear-gradient(to right, currentColor 50%, transparent 0);
  background-size: 4px 2px;
  background-repeat: repeat-x;
}

.edu-legend-label {
  opacity: 0.95;
}

@keyframes pulse-dot {
  0%, 100% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.3);
    opacity: 0.8;
  }
}

.edu-radio-group {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.edu-radio-item {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.edu-radio-item label {
  font-size: 0.85rem;
  font-weight: 500;
  color: var(--text-secondary);
}

.edu-radio-buttons {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.edu-radio-btn {
  padding: 8px 16px;
  border: 1.5px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--surface-2);
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.15s;
}

.edu-radio-btn:hover {
  border-color: var(--accent);
}

.edu-radio-btn.active {
  border-color: var(--accent);
  background: var(--accent-light);
  color: var(--accent);
  font-weight: 500;
}

.edu-diagnosis-buttons {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.75rem;
}

.edu-diagnosis-btn {
  padding: 12px 16px;
  border: 1.5px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--surface-2);
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
}

.edu-diagnosis-btn:hover {
  border-color: var(--accent);
}

.edu-diagnosis-btn.active {
  border-color: var(--accent);
  background: var(--accent-light);
  color: var(--accent);
}

.edu-score-card {
  padding: 2rem;
  border-radius: var(--radius-md);
  text-align: center;
  margin-bottom: 1.5rem;
  border: 2px solid;
}

.edu-score-card.success {
  background: var(--success-light);
  border-color: var(--success);
}

.edu-score-card.warning {
  background: var(--warning-light);
  border-color: var(--warning);
}

.edu-score-card.danger {
  background: var(--danger-light);
  border-color: var(--danger);
}

.edu-score-value {
  font-family: var(--font-display);
  font-size: 4rem;
  font-weight: 800;
  line-height: 1;
  margin-bottom: 0.5rem;
}

.edu-score-card.success .edu-score-value {
  color: var(--success);
}

.edu-score-card.warning .edu-score-value {
  color: var(--warning);
}

.edu-score-card.danger .edu-score-value {
  color: var(--danger);
}

.edu-score-label {
  font-size: 1rem;
  font-weight: 600;
  margin-bottom: 0.75rem;
  color: var(--text-secondary);
}

.edu-score-breakdown {
  display: flex;
  justify-content: space-around;
  gap: 1rem;
  font-size: 0.8rem;
  color: var(--text-muted);
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid var(--border);
}

.edu-diagnosis-result {
  padding: 1rem;
  background: var(--surface-2);
  border-radius: var(--radius-sm);
}

.edu-diagnosis-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 0;
  font-size: 0.9rem;
}

.zone-id.good {
  color: var(--success);
  font-weight: 700;
}

.zone-id.poor {
  color: var(--danger);
  font-weight: 700;
}

.zone-id.excellent {
  color: var(--success);
  font-weight: 700;
}

.warning-icon {
  background: var(--warning-light);
  color: var(--warning);
}

.image-view:fullscreen img,
.image-view:-webkit-full-screen img {
  object-fit: contain;
  width: 100%;
  height: 100%;
}

.image-view:fullscreen svg,
.image-view:-webkit-full-screen svg {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
}

.microscopy-summary {
  margin-top: 0.75rem;
  display: grid;
  gap: 0.5rem;
}

.microscopy-summary-item {
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 0.6rem 0.75rem;
  background: rgba(255, 255, 255, 0.02);
}

.microscopy-summary-item.normal {
  border-color: rgba(16, 185, 129, 0.45);
  background: rgba(16, 185, 129, 0.1);
}

.microscopy-summary-item.abnormal {
  border-color: rgba(239, 68, 68, 0.45);
  background: rgba(239, 68, 68, 0.1);
}

.microscopy-summary-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
}

.microscopy-summary-label {
  font-size: 0.85rem;
  color: var(--text-primary);
  font-weight: 600;
}

.microscopy-summary-value {
  font-size: 0.82rem;
  color: var(--text-primary);
  font-weight: 700;
}

.microscopy-summary-details {
  font-size: 0.76rem;
  color: var(--text-secondary);
}

.microscopy-summary-status {
  font-size: 0.74rem;
  font-weight: 700;
}

.microscopy-summary-item.normal .microscopy-summary-status {
  color: #10b981;
}

.microscopy-summary-item.abnormal .microscopy-summary-status {
  color: #ef4444;
}

</style>
