<template>
  <div v-if="loading" class="muted center-pad">Считаем закупку…</div>
  <div v-else-if="error" class="error">{{ error }}</div>
  <template v-else>

    <!-- Итоги -->
    <div class="summary-grid">
      <div class="summary-card bark">
        <div class="label">📦 Долгосрочное</div>
        <div class="value">{{ fmt(summary.long_total) }} ₽</div>
      </div>
      <div class="summary-card">
        <div class="label">🥬 Краткосрочное</div>
        <div class="value">{{ fmt(summary.short_total) }} ₽</div>
      </div>
      <div class="summary-card accent">
        <div class="label">💰 Всего</div>
        <div class="value">{{ fmt(summary.grand_total) }} ₽</div>
      </div>
    </div>

    <!-- Переключатель режима -->
    <div class="mode-bar">
      <button
        :class="['mode-btn', { active: mode === 'summary' }]"
        @click="mode = 'summary'"
      >📋 Сводный</button>
      <button
        :class="['mode-btn', { active: mode === 'by-dish' }]"
        @click="mode = 'by-dish'"
      >🍲 По блюдам</button>
    </div>

    <!-- ===== СВОДНЫЙ режим ===== -->
    <template v-if="mode === 'summary'">
      <div v-if="summary.long_term.length">
        <div class="section-title">📦 Долгосрочное — берём заранее</div>
        <div class="product-cards">
          <div
            v-for="r in summary.long_term"
            :key="r.product_id"
            class="product-card"
          >
            <div class="pc-name">
              <a v-if="r.product_link" :href="r.product_link" target="_blank">{{ r.product_name }}</a>
              <span v-else>{{ r.product_name }}</span>
            </div>
            <div class="pc-meta">
              <span class="pc-qty">{{ r.packages_needed }} {{ r.unit }}</span>
              <span v-if="r.total_grams" class="muted">{{ fmt(r.total_grams) }} г</span>
              <span v-if="r.price_per_unit" class="muted">{{ fmt(r.price_per_unit) }} ₽/уп</span>
              <span class="pc-price">{{ fmt(r.total_price) }} ₽</span>
            </div>
          </div>
        </div>
      </div>

      <div v-if="summary.short_term.length" style="margin-top:16px">
        <div class="section-title">🥬 Краткосрочное — за 1–2 дня до выезда</div>
        <div class="product-cards">
          <div
            v-for="r in summary.short_term"
            :key="r.product_id"
            class="product-card"
          >
            <div class="pc-name">
              <a v-if="r.product_link" :href="r.product_link" target="_blank">{{ r.product_name }}</a>
              <span v-else>{{ r.product_name }}</span>
            </div>
            <div class="pc-meta">
              <span class="pc-qty">{{ r.packages_needed }} {{ r.unit }}</span>
              <span v-if="r.total_grams" class="muted">{{ fmt(r.total_grams) }} г</span>
              <span v-if="r.price_per_unit" class="muted">{{ fmt(r.price_per_unit) }} ₽/уп</span>
              <span class="pc-price">{{ fmt(r.total_price) }} ₽</span>
            </div>
          </div>
        </div>
      </div>

      <div v-if="!summary.long_term.length && !summary.short_term.length" class="muted center-pad">
        Ничего не нужно — добавьте блюда и ингредиенты в меню.
      </div>
    </template>

    <!-- ===== ПО БЛЮДАМ режим ===== -->
    <template v-if="mode === 'by-dish'">
      <div v-if="!fullData || !fullData.days.length" class="muted center-pad">
        Нет дней и приёмов пищи.
      </div>
      <template v-else>
        <div
          v-for="day in fullData.days"
          :key="day.id"
          class="day-section"
        >
          <div class="day-title">📅 {{ day.name }}</div>

          <div
            v-for="meal in day.meals"
            :key="meal.id"
            class="meal-section"
          >
            <div class="meal-title">
              {{ mealIcon(meal.name) }} {{ meal.name }}
              <span class="portions-badge">{{ portions(meal) }} порц.</span>
            </div>

            <div v-if="!meal.dishes.length" class="muted" style="padding:6px 0 6px 12px; font-size:13px">
              Нет блюд
            </div>

            <div
              v-for="dish in meal.dishes"
              :key="dish.id"
              class="dish-section"
            >
              <div class="dish-title">• {{ dish.name }}</div>

              <div v-if="!dish.ingredients.length" class="muted ing-row" style="font-size:12px">
                Нет ингредиентов
              </div>

              <label
                v-for="ing in dish.ingredients"
                :key="ing.id"
                class="ing-row"
                :class="{ taken: ing.taken }"
              >
                <input
                  type="checkbox"
                  class="ing-check"
                  :checked="ing.taken"
                  @change="toggleIngredient(ing, $event.target.checked)"
                />
                <span class="ing-name" :class="{ 'line-through': ing.taken }">
                  {{ ing.product.name }}
                </span>
                <span class="ing-detail muted">
                  {{ totalGrams(ing, meal) }} г
                  <template v-if="ing.product.grams_in_package">
                    · {{ pkgs(ing, meal) }} {{ ing.product.unit }}
                  </template>
                </span>
              </label>
            </div>
          </div>

          <!-- Прочее дня не показываем — оно в сводном -->
        </div>

        <!-- Прочее (misc) -->
        <div v-if="fullData.misc_items && fullData.misc_items.length" class="day-section">
          <div class="day-title">🧂 Прочее</div>
          <label
            v-for="item in fullData.misc_items"
            :key="item.id"
            class="ing-row"
            :class="{ taken: item.taken }"
          >
            <input
              type="checkbox"
              class="ing-check"
              :checked="item.taken"
              @change="toggleMisc(item, $event.target.checked)"
            />
            <span class="ing-name" :class="{ 'line-through': item.taken }">
              {{ item.product.name }}
            </span>
            <span class="ing-detail muted">
              {{ item.quantity }} {{ item.product.unit }}
            </span>
          </label>
        </div>
      </template>
    </template>

  </template>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { api } from '../api.js'

const props = defineProps({ eventId: { type: Number, required: true } })

const loading = ref(true)
const error = ref('')
const mode = ref('by-dish')

const summary = ref({ long_term: [], short_term: [], long_total: 0, short_total: 0, grand_total: 0 })
const fullData = ref(null)

function fmt(n) {
  return new Intl.NumberFormat('ru-RU', { maximumFractionDigits: 2 }).format(n || 0)
}

function mealIcon(name) {
  const n = (name || '').toLowerCase()
  if (n.includes('завтрак')) return '🍳'
  if (n.includes('обед')) return '🥣'
  if (n.includes('ужин')) return '🍲'
  if (n.includes('перекус')) return '🥪'
  return '🍴'
}

function portions(meal) {
  return meal.participant_ids.length + (meal.guests_count || 0)
}

function totalGrams(ing, meal) {
  return Math.round((ing.grams_per_portion || 0) * portions(meal))
}

function pkgs(ing, meal) {
  const g = totalGrams(ing, meal)
  const pkg = ing.product.grams_in_package || 1000
  return (g / pkg).toFixed(2)
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    const [s, f] = await Promise.all([
      api.getShoppingList(props.eventId),
      api.getEventFull(props.eventId),
    ])
    summary.value = s
    fullData.value = f
  } catch (e) { error.value = e.message }
  finally { loading.value = false }
}

async function toggleIngredient(ing, checked) {
  ing.taken = checked
  await api.toggleTaken(ing.id, checked)
}

async function toggleMisc(item, checked) {
  item.taken = checked
  await api.updateMisc(item.id, {
    product_id: item.product_id,
    quantity: item.quantity,
    taken: checked,
  })
}

watch(() => props.eventId, load)
onMounted(load)
defineExpose({ reload: load })
</script>

<style>
/* ===== Summary grid ===== */
.summary-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
  margin-bottom: 14px;
}
@media (max-width: 480px) {
  .summary-grid { grid-template-columns: 1fr; gap: 6px; }
}

/* ===== Mode bar ===== */
.mode-bar {
  display: flex;
  gap: 8px;
  margin-bottom: 14px;
}
.mode-btn {
  flex: 1;
  background: #fff;
  color: var(--green-800);
  border: 1px solid var(--border);
  box-shadow: none;
  border-radius: 8px;
  padding: 10px;
  font-size: 14px;
  font-weight: 500;
}
.mode-btn:hover { background: var(--green-50); transform: none; }
.mode-btn.active {
  background: var(--green-700);
  color: #fff;
  border-color: var(--green-700);
}

/* ===== Section title ===== */
.section-title {
  font-weight: 700;
  font-size: 14px;
  color: var(--green-900);
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

/* ===== Product cards (сводный) ===== */
.product-cards { display: flex; flex-direction: column; gap: 6px; }
.product-card {
  background: #fff;
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 12px 14px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}
.pc-name { font-weight: 500; font-size: 15px; flex: 1; min-width: 120px; }
.pc-meta { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; font-size: 13px; }
.pc-qty { font-weight: 700; font-size: 16px; color: var(--green-800); }
.pc-price { font-weight: 700; color: var(--green-900); }

/* ===== By-dish view ===== */
.day-section { margin-bottom: 16px; }
.day-title {
  font-weight: 700;
  font-size: 16px;
  color: var(--green-900);
  padding: 10px 14px;
  background: var(--green-100);
  border-radius: 10px 10px 0 0;
  border: 1px solid var(--green-200);
}

.meal-section {
  border: 1px solid var(--border);
  border-top: 0;
  background: #fff;
}
.meal-section:last-child { border-radius: 0 0 10px 10px; }

.meal-title {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  font-weight: 600;
  font-size: 14px;
  background: var(--green-50);
  border-bottom: 1px solid var(--border);
}
.portions-badge {
  margin-left: auto;
  background: var(--green-100);
  color: var(--green-800);
  border-radius: 999px;
  padding: 2px 8px;
  font-size: 12px;
  font-weight: 500;
}

.dish-section { border-bottom: 1px solid var(--green-50); }
.dish-section:last-child { border-bottom: 0; }
.dish-title {
  padding: 8px 14px 4px;
  font-weight: 600;
  font-size: 13px;
  color: var(--green-800);
}

.ing-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  border-bottom: 1px solid var(--green-50);
  cursor: pointer;
  min-height: 44px; /* удобно тыкать пальцем */
}
.ing-row:last-child { border-bottom: 0; }
.ing-row:hover { background: var(--green-50); }
.ing-row.taken { opacity: 0.5; }

.ing-check {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
  accent-color: var(--green-600);
  cursor: pointer;
}
.ing-name { flex: 1; font-size: 14px; }
.ing-detail { font-size: 12px; text-align: right; white-space: nowrap; }
.line-through { text-decoration: line-through; }

.center-pad { padding: 32px; text-align: center; }

/* Print */
@media print {
  .sidebar, .toolbar button, .tabs, .mode-bar { display: none !important; }
  .main { padding: 0; }
  body { background: #fff; }
  .summary-card { box-shadow: none; }
  .ing-check { display: none; }
}

/* Mobile */
@media (max-width: 600px) {
  .product-card { padding: 10px 12px; }
  .pc-name { font-size: 14px; }
  .ing-row { padding: 12px 10px; }
  .day-title { font-size: 14px; }
}
</style>
