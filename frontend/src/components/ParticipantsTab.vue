<template>
  <div v-if="loading" class="muted">Загрузка…</div>
  <div v-else-if="error" class="error">{{ error }}</div>
  <template v-else>
    <div v-if="!people.length" class="empty-hero">
      <div class="big">👤</div>
      <p>Нет участников. Добавьте их в разделе <a href="/people">«Участники»</a>.</p>
    </div>

    <template v-else>
      <!-- ===== Кто едет ===== -->
      <div class="card going-card">
        <div class="going-header">
          <h3 style="margin:0">✅ Кто едет</h3>
          <span class="muted" style="font-size:13px">{{ goingIds.length }} из {{ people.length }} чел.</span>
        </div>
        <p class="muted" style="font-size:13px; margin:6px 0 14px">
          При изменении список автоматически обновится во всех приёмах пищи.
          Новые приёмы тоже будут заполнены этим списком.
        </p>
        <div class="going-grid">
          <label
            v-for="person in people"
            :key="person.id"
            class="going-label"
            :class="{ going: goingIds.includes(person.id) }"
          >
            <input
              type="checkbox"
              :checked="goingIds.includes(person.id)"
              @change="toggleGoing(person.id, $event.target.checked)"
            />
            <span>{{ person.full_name }}</span>
            <span v-if="person.role" class="muted role-badge">{{ person.role }}</span>
          </label>
        </div>
        <div v-if="goingSaving" class="muted" style="font-size:12px; margin-top:8px">Сохранение…</div>
      </div>

      <div class="hint-block" style="margin-bottom:14px">
        👤 Личные продукты и блюда каждого участника. Продукты делятся по объёму закупки.
      </div>

      <div class="participants-list">
        <div
          v-for="person in people"
          :key="person.id"
          class="participant-row card"
        >
          <div class="participant-info">
            <span class="participant-name">{{ person.full_name }}</span>
            <span v-if="person.role" class="muted" style="font-size:12px">{{ person.role }}</span>
          </div>
          <div class="participant-summary">
            <span v-if="productCountFor(person.id)" class="count-chip">
              🛒 {{ productCountFor(person.id) }} прод.
            </span>
            <span v-if="dishCountFor(person.id)" class="count-chip">
              🍽 {{ dishCountFor(person.id) }} блюд
            </span>
            <span v-if="!productCountFor(person.id) && !dishCountFor(person.id)" class="muted" style="font-size:12px">
              ничего не задано
            </span>
          </div>
          <button class="secondary small" @click="openPerson(person)">📋 Меню</button>
        </div>
      </div>
    </template>

    <!-- Modal for participant menu -->
    <div v-if="activePerson" class="modal-backdrop" @click.self="activePerson = null">
      <div class="modal participant-modal">
        <div class="modal-title-row">
          <h3 style="margin:0">👤 {{ activePerson.full_name }}</h3>
          <span v-if="activePerson.role" class="muted" style="font-size:13px">{{ activePerson.role }}</span>
        </div>

        <!-- Products -->
        <h4 class="section-head">🛒 Продукты</h4>
        <div class="size-columns">
          <div v-for="s in SIZES" :key="s.value" class="size-col" :class="`sz-${s.value}`">
            <div class="size-header" :class="`szh-${s.value}`">{{ s.label }}</div>

            <div
              v-for="item in productsFor(activePerson.id, s.value)"
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
                  @change="updateProduct(item)"
                />
                <span class="muted unit-label">{{ item.product.unit }}</span>
                <button class="ghost small danger-text" @click="removeProduct(item)">×</button>
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
                @click="addProduct(s.value)"
              >+</button>
            </div>
          </div>
        </div>

        <!-- Dishes -->
        <h4 class="section-head" style="margin-top:20px">🍽 Блюда</h4>
        <div v-if="dishesFor(activePerson.id).length" class="dishes-simple">
          <div v-for="d in dishesFor(activePerson.id)" :key="d.id" class="dish-simple-row">
            <span>{{ d.name }}</span>
            <button class="ghost small danger-text" @click="removeDish(d)">×</button>
          </div>
        </div>
        <div v-else class="muted" style="margin-bottom:8px; font-size:13px">Блюд нет.</div>

        <div class="row" style="margin-top:8px; gap:8px">
          <input
            v-model="newDishName"
            placeholder="Название блюда"
            style="flex:1"
            @keyup.enter="addDish"
          />
          <button :disabled="!newDishName.trim()" @click="addDish">+ Добавить</button>
        </div>

        <div class="row" style="justify-content:flex-end; margin-top:20px">
          <button class="secondary" @click="activePerson = null">Закрыть</button>
        </div>
      </div>
    </div>
  </template>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { api } from '../api.js'
import ProductPicker from './ProductPicker.vue'

const props = defineProps({ eventId: { type: Number, required: true } })

const SIZES = [
  { value: 'малое',   label: 'Малое' },
  { value: 'среднее', label: 'Среднее' },
  { value: 'большое', label: 'Большое' },
]

const loading = ref(true)
const error = ref('')
const people = ref([])
const products = ref([])
const participantProducts = ref([])
const participantDishes = ref([])
const goingIds = ref([])
const goingSaving = ref(false)

const activePerson = ref(null)
const newDishName = ref('')

function freshNewProd() {
  return {
    малое:   { product_id: null, quantity: 1 },
    среднее: { product_id: null, quantity: 1 },
    большое: { product_id: null, quantity: 1 },
  }
}
const newProd = ref(freshNewProd())

async function load() {
  loading.value = true
  error.value = ''
  try {
    const [ppl, prods, items, gids] = await Promise.all([
      api.listPeople(),
      api.listProducts(),
      api.getParticipantItems(props.eventId),
      api.getEventParticipants(props.eventId),
    ])
    people.value = ppl
    products.value = prods
    participantProducts.value = items.products
    participantDishes.value = items.dishes
    goingIds.value = gids
  } catch (e) { error.value = e.message }
  finally { loading.value = false }
}

async function toggleGoing(personId, checked) {
  const s = new Set(goingIds.value)
  if (checked) s.add(personId); else s.delete(personId)
  goingIds.value = [...s]
  goingSaving.value = true
  try {
    await api.setEventParticipants(props.eventId, goingIds.value)
  } finally {
    goingSaving.value = false
  }
}

async function reload() {
  const items = await api.getParticipantItems(props.eventId)
  participantProducts.value = items.products
  participantDishes.value = items.dishes
}

function productsFor(personId, size) {
  return participantProducts.value.filter(p => p.person_id === personId && p.size === size)
}

function dishesFor(personId) {
  return participantDishes.value.filter(d => d.person_id === personId)
}

function productCountFor(personId) {
  return participantProducts.value.filter(p => p.person_id === personId).length
}

function dishCountFor(personId) {
  return participantDishes.value.filter(d => d.person_id === personId).length
}

function openPerson(person) {
  activePerson.value = person
  newProd.value = freshNewProd()
  newDishName.value = ''
}

async function addProduct(size) {
  const np = newProd.value[size]
  if (!np.product_id) return
  await api.addParticipantProduct(props.eventId, activePerson.value.id, {
    product_id: np.product_id,
    quantity: Number(np.quantity) || 1,
    size,
  })
  np.product_id = null
  np.quantity = 1
  await reload()
}

async function updateProduct(item) {
  await api.updateParticipantProduct(item.id, {
    product_id: item.product_id,
    quantity: Number(item.quantity) || 1,
    size: item.size,
  })
}

async function removeProduct(item) {
  await api.deleteParticipantProduct(item.id)
  await reload()
}

async function addDish() {
  const name = newDishName.value.trim()
  if (!name) return
  await api.addParticipantDish(props.eventId, activePerson.value.id, { name })
  newDishName.value = ''
  await reload()
}

async function removeDish(d) {
  await api.deleteParticipantDish(d.id)
  await reload()
}

watch(() => props.eventId, load)
onMounted(load)
defineExpose({ reload: load })
</script>

<style scoped>
.hint-block {
  background: var(--green-50);
  border-left: 3px solid var(--green-600);
  padding: 10px 14px;
  border-radius: 6px;
  font-size: 13px;
  color: var(--green-900);
}

.participants-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.participant-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  flex-wrap: wrap;
}

.participant-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex: 1;
  min-width: 160px;
}

.participant-name {
  font-weight: 600;
  color: var(--green-900);
}

.participant-summary {
  display: flex;
  gap: 6px;
  align-items: center;
  flex-wrap: wrap;
}

.count-chip {
  background: var(--green-100);
  color: var(--green-800);
  border-radius: 999px;
  padding: 2px 10px;
  font-size: 12px;
  font-weight: 500;
}

/* Modal */
.participant-modal {
  max-width: 760px;
  max-height: 85vh;
  overflow-y: auto;
}

.modal-title-row {
  display: flex;
  align-items: baseline;
  gap: 10px;
  margin-bottom: 16px;
}

.section-head {
  margin: 0 0 10px;
  font-size: 14px;
  font-weight: 700;
  color: var(--green-900);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

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
  background: #fff;
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

.qty-input {
  width: 52px;
  padding: 3px 6px;
  font-size: 13px;
}

.unit-label {
  font-size: 11px;
  min-width: 16px;
}

.add-product-bar {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px dashed var(--border);
}

/* Dishes */
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

/* Going card */
.going-card { margin-bottom: 16px; padding: 16px 18px; }
.going-header {
  display: flex;
  align-items: baseline;
  gap: 12px;
  margin-bottom: 4px;
}
.going-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 6px;
}
.going-label {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border: 1px solid var(--border);
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  transition: background 0.1s;
}
.going-label:hover { background: var(--green-50); }
.going-label.going {
  background: var(--green-50);
  border-color: var(--green-500);
}
.role-badge {
  font-size: 11px;
  margin-left: auto;
}
</style>
