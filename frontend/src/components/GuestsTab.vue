<template>
  <div v-if="loading" class="muted">Загрузка…</div>
  <div v-else-if="error" class="error">{{ error }}</div>
  <template v-else>
    <div class="card">
      <div class="hint-block">
        🎟 «Гости» — едоки <b>дополнительно</b> к участникам-оргам. Их число прибавляется к участникам приёма пищи
        и влияет на расчёт порций, списка покупок и общей суммы. Не платят персонально, не учитываются во взносах.
      </div>

      <div class="bulk-bar">
        <span>Поставить</span>
        <input type="number" v-model.number="bulkN" class="w-sm" min="0" />
        <span>гостей на ВСЕ приёмы:</span>
        <button @click="applyBulk">Применить</button>
        <button class="secondary small" @click="bulkN = 0; applyBulk()" title="Сбросить">Сбросить</button>
      </div>
    </div>

    <div v-for="day in days" :key="day.id" class="card day-card">
      <div class="day-header">
        <h3 style="margin:0">📅 {{ day.name }}</h3>
        <div class="row">
          <input type="number" v-model.number="dayBulkValues[day.id]" placeholder="N" class="w-sm" min="0" />
          <button class="secondary small" @click="applyForDay(day)">Задать всему дню</button>
        </div>
      </div>

      <table v-if="day.meals.length">
        <thead>
          <tr>
            <th>Приём пищи</th>
            <th class="right">Орги (по списку)</th>
            <th class="right">🎟 Гости</th>
            <th class="right">= Всего порций</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="m in day.meals" :key="m.id">
            <td>{{ mealIcon(m.name) }} {{ m.name }}</td>
            <td class="right">{{ m.participant_ids.length }}</td>
            <td class="right">
              <input
                type="number" min="0"
                :value="m.guests_count || 0"
                class="w-sm right"
                @change="updateGuests(m, $event.target.value)"
              />
            </td>
            <td class="right"><b>{{ m.participant_ids.length + (m.guests_count || 0) }}</b></td>
          </tr>
        </tbody>
      </table>
      <div v-else class="muted center" style="padding:8px">Нет приёмов пищи.</div>
    </div>

    <div v-if="!days.length" class="empty">
      <div class="big">📅</div>
      Сначала добавьте дни и приёмы пищи на вкладке «🍲 Меню»
    </div>
  </template>
</template>

<script setup>
import { ref, watch, reactive, onMounted } from 'vue'
import { api } from '../api.js'

const props = defineProps({ eventId: { type: Number, required: true } })
const emit = defineEmits(['changed'])

const days = ref([])
const loading = ref(true)
const error = ref('')
const bulkN = ref(0)
const dayBulkValues = reactive({})

function mealIcon(name) {
  const n = (name || '').toLowerCase()
  if (n.includes('завтрак')) return '🍳'
  if (n.includes('обед')) return '🥣'
  if (n.includes('ужин')) return '🍲'
  if (n.includes('перекус')) return '🥪'
  return '🍴'
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    const full = await api.getEventFull(props.eventId)
    days.value = full.days
  } catch (e) { error.value = e.message } finally { loading.value = false }
}

async function updateGuests(m, raw) {
  const n = Math.max(0, parseInt(raw, 10) || 0)
  m.guests_count = n
  await api.updateMeal(m.id, { name: m.name, sort_order: m.sort_order, guests_count: n })
  emit('changed')
}

async function applyBulk() {
  const n = Math.max(0, Number(bulkN.value) || 0)
  if (n > 0 && !confirm(`Поставить ${n} гостей на ВСЕ приёмы пищи всех дней?`)) return
  await api.setAllGuests(props.eventId, n)
  await load()
  emit('changed')
}

async function applyForDay(day) {
  const n = Math.max(0, Number(dayBulkValues[day.id]) || 0)
  for (const m of day.meals) {
    await api.updateMeal(m.id, { name: m.name, sort_order: m.sort_order, guests_count: n })
  }
  await load()
  emit('changed')
}

watch(() => props.eventId, load)
onMounted(load)
defineExpose({ reload: load })
</script>

<style scoped>
.day-card { margin-bottom: 12px; padding: 14px 16px; }
.day-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}
.bulk-bar {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
  margin-top: 12px;
}
.hint-block {
  background: var(--green-50);
  border-left: 3px solid var(--green-600);
  padding: 10px 14px;
  border-radius: 6px;
  font-size: 13px;
  color: var(--green-900);
}
.empty {
  background: #fff;
  border: 1px dashed var(--green-500);
  border-radius: var(--radius);
  padding: 48px 20px;
  text-align: center;
  color: var(--muted);
}
.empty .big { font-size: 56px; opacity: 0.6; margin-bottom: 12px; }
</style>
