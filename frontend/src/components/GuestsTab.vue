<template>
  <div v-if="loading" class="muted">Загрузка…</div>
  <div v-else-if="error" class="error">{{ error }}</div>
  <template v-else>

    <!-- ===== Счётчик по приёмам пищи ===== -->
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

    <!-- ===== Продукты гостей ===== -->
    <div class="card" style="margin-top:8px">
      <h3 style="margin-top:0">🛒 Продукты гостей</h3>
      <p class="muted" style="font-size:13px; margin-bottom:14px">
        Общие продукты для всей группы гостей, разбитые по объёму закупки.
      </p>

      <div class="size-columns">
        <div v-for="s in SIZES" :key="s.value" class="size-col">
          <div class="size-header" :class="`szh-${s.value}`">{{ s.label }}</div>

          <div
            v-for="item in guestProductsBy(s.value)"
            :key="item.id"
            class="pitem-row"
          >
            <span class="pitem-name">{{ item.product.name }}</span>
            <div class="pitem-right">
              <input
                type="number"
                v-model.number="item.quantity"
                class="qty-input"
                min="0.1"
                step="0.1"
                @change="updateGuestProduct(item)"
              />
              <span class="muted unit-label">{{ item.product.unit }}</span>
              <button class="ghost small danger-text" @click="removeGuestProduct(item)">×</button>
            </div>
          </div>

          <div class="add-product-bar">
            <ProductPicker
              :products="products"
              v-model="newProd[s.value].product_id"
              placeholder="Добавить…"
              style="flex:1; min-width:0"
            />
            <input
              type="number"
              v-model.number="newProd[s.value].quantity"
              class="qty-input"
              min="0.1"
              step="0.1"
            />
            <button
              class="secondary small"
              :disabled="!newProd[s.value].product_id"
              @click="addGuestProduct(s.value)"
            >+</button>
          </div>
        </div>
      </div>
    </div>

    <!-- ===== Блюда гостей ===== -->
    <div class="card" style="margin-top:8px">
      <h3 style="margin-top:0">🍽 Блюда гостей</h3>

      <div v-if="guestDishes.length" class="dishes-simple">
        <div v-for="d in guestDishes" :key="d.id" class="dish-simple-row">
          <span>{{ d.name }}</span>
          <button class="ghost small danger-text" @click="removeGuestDish(d)">×</button>
        </div>
      </div>
      <div v-else class="muted" style="font-size:13px; margin-bottom:8px">Блюд нет.</div>

      <div class="row" style="margin-top:8px; gap:8px">
        <input
          v-model="newDishName"
          placeholder="Название блюда"
          style="flex:1"
          @keyup.enter="addGuestDish"
        />
        <button :disabled="!newDishName.trim()" @click="addGuestDish">+ Добавить</button>
      </div>
    </div>

  </template>
</template>

<script setup>
import { ref, watch, reactive, onMounted } from 'vue'
import { api } from '../api.js'
import ProductPicker from './ProductPicker.vue'

const props = defineProps({ eventId: { type: Number, required: true } })
const emit = defineEmits(['changed'])

const SIZES = [
  { value: 'малое',   label: 'Малое' },
  { value: 'среднее', label: 'Среднее' },
  { value: 'большое', label: 'Большое' },
]

const days = ref([])
const products = ref([])
const guestProducts = ref([])
const guestDishes = ref([])
const loading = ref(true)
const error = ref('')
const bulkN = ref(0)
const dayBulkValues = reactive({})
const newDishName = ref('')

function freshNewProd() {
  return {
    малое:   { product_id: null, quantity: 1 },
    среднее: { product_id: null, quantity: 1 },
    большое: { product_id: null, quantity: 1 },
  }
}
const newProd = ref(freshNewProd())

function mealIcon(name) {
  const n = (name || '').toLowerCase()
  if (n.includes('завтрак')) return '🍳'
  if (n.includes('обед')) return '🥣'
  if (n.includes('ужин')) return '🍲'
  if (n.includes('перекус')) return '🥪'
  return '🍴'
}

function guestProductsBy(size) {
  return guestProducts.value.filter(p => p.size === size)
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    const [full, prods, items] = await Promise.all([
      api.getEventFull(props.eventId),
      api.listProducts(),
      api.getGuestItems(props.eventId),
    ])
    days.value = full.days
    products.value = prods
    guestProducts.value = items.products
    guestDishes.value = items.dishes
  } catch (e) { error.value = e.message } finally { loading.value = false }
}

async function reloadItems() {
  const items = await api.getGuestItems(props.eventId)
  guestProducts.value = items.products
  guestDishes.value = items.dishes
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

async function addGuestProduct(size) {
  const np = newProd.value[size]
  if (!np.product_id) return
  await api.addGuestProduct(props.eventId, {
    product_id: np.product_id,
    quantity: Number(np.quantity) || 1,
    size,
  })
  np.product_id = null
  np.quantity = 1
  await reloadItems()
}

async function updateGuestProduct(item) {
  await api.updateGuestProduct(item.id, {
    product_id: item.product_id,
    quantity: Number(item.quantity) || 1,
    size: item.size,
  })
}

async function removeGuestProduct(item) {
  await api.deleteGuestProduct(item.id)
  await reloadItems()
}

async function addGuestDish() {
  const name = newDishName.value.trim()
  if (!name) return
  await api.addGuestDish(props.eventId, { name })
  newDishName.value = ''
  await reloadItems()
}

async function removeGuestDish(d) {
  await api.deleteGuestDish(d.id)
  await reloadItems()
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

/* Size columns */
.size-columns {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
}
@media (max-width: 600px) {
  .size-columns { grid-template-columns: 1fr; }
}

.size-col {
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 10px 10px 8px;
  background: #fafafa;
}

.size-header {
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  margin-bottom: 8px;
  padding: 3px 8px;
  border-radius: 4px;
  display: inline-block;
}
.szh-малое   { background: #e8f5e9; color: #388e3c; }
.szh-среднее { background: #fff3e0; color: #e65100; }
.szh-большое { background: #fce4ec; color: #c62828; }

.pitem-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 6px;
  padding: 5px 4px;
  border-bottom: 1px solid var(--green-50);
}
.pitem-row:last-of-type { border-bottom: 0; }

.pitem-name {
  font-size: 13px;
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.pitem-right {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

.qty-input { width: 52px; padding: 3px 6px; font-size: 13px; }
.unit-label { font-size: 11px; min-width: 16px; }

.add-product-bar {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px dashed var(--border);
}

.dishes-simple {
  border: 1px solid var(--border);
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 4px;
}

.dish-simple-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  border-bottom: 1px solid var(--border);
  font-size: 14px;
}
.dish-simple-row:last-child { border-bottom: 0; }
.dish-simple-row:hover { background: var(--green-50); }
</style>
