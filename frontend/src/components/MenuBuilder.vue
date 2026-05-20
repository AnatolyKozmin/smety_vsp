<template>
  <div v-if="loading" class="muted">Загрузка меню…</div>
  <div v-else-if="error" class="error">{{ error }}</div>
  <template v-else>
    <!-- Empty state for the whole menu -->
    <div v-if="!days.length" class="empty-hero">
      <div class="big">📅</div>
      <p>В меню пока нет ни одного дня.</p>
      <button @click="addDay">+ Добавить первый день</button>
    </div>

    <!-- Days -->
    <div v-for="(day, dayIdx) in days" :key="day.id" class="card day-card">
      <div class="day-header">
        <div class="day-title">
          <span class="day-num">День {{ dayIdx + 1 }}</span>
          <input
            v-model="day.name"
            class="day-name-input"
            placeholder="Например: 01.08 (суббота)"
            @change="updateDay(day)"
          />
        </div>
        <div class="row">
          <button class="ghost small" :disabled="dayIdx === 0" @click="moveDay(dayIdx, -1)" title="Выше">↑</button>
          <button class="ghost small" :disabled="dayIdx === days.length - 1" @click="moveDay(dayIdx, 1)" title="Ниже">↓</button>
          <button class="ghost small danger-text" @click="deleteDay(day)" title="Удалить день">🗑</button>
        </div>
      </div>

      <!-- Meals inside the day -->
      <div v-for="(meal, mealIdx) in day.meals" :key="meal.id" class="meal-block">
        <div class="meal-header">
          <div class="meal-title">
            <span class="meal-icon">{{ mealIcon(meal.name) }}</span>
            <input
              v-model="meal.name"
              class="meal-name-input"
              @change="updateMeal(meal)"
            />
            <button class="chip" @click="openParticipants(meal)" :title="'Выбрать участников'">
              👥 {{ meal.participant_ids.length }} чел.
            </button>
          </div>
          <div class="row">
            <button class="ghost small" :disabled="mealIdx === 0" @click="moveMeal(day, mealIdx, -1)">↑</button>
            <button class="ghost small" :disabled="mealIdx === day.meals.length - 1" @click="moveMeal(day, mealIdx, 1)">↓</button>
            <button class="ghost small danger-text" @click="deleteMeal(meal)" title="Удалить приём">🗑</button>
          </div>
        </div>

        <!-- Dishes inside the meal: simple list -->
        <ul v-if="meal.dishes.length" class="dish-list">
          <li v-for="dsh in meal.dishes" :key="dsh.id" class="dish-row">
            <div class="dish-info">
              <span class="dish-bullet">•</span>
              <span class="dish-name-text">{{ dsh.name }}</span>
              <span class="muted" v-if="dsh.ingredients.length">— {{ dsh.ingredients.length }} ингр.</span>
              <span class="muted" v-else>— без ингредиентов</span>
            </div>
            <div class="row">
              <button class="ghost small" @click="openEditDish(dsh)" title="Редактировать">✏️</button>
              <button class="ghost small danger-text" @click="removeDish(dsh)" title="Удалить">🗑</button>
            </div>
          </li>
        </ul>

        <button class="add-dish-btn" @click="openAddDish(meal)">+ Добавить блюдо</button>
      </div>

      <!-- Quick add meal section -->
      <div class="add-meal-bar">
        <span class="muted">+ Приём пищи:</span>
        <button class="chip" @click="addPresetMeal(day, 'Завтрак')">🍳 Завтрак</button>
        <button class="chip" @click="addPresetMeal(day, 'Обед')">🥣 Обед</button>
        <button class="chip" @click="addPresetMeal(day, 'Ужин')">🍲 Ужин</button>
        <button class="chip" @click="addPresetMeal(day, 'Перекус')">🥪 Перекус</button>
        <button class="chip" @click="addPresetMeal(day, 'Новый приём')">＋ Свой</button>
      </div>
    </div>

    <div v-if="days.length" class="add-day-wrap">
      <button class="secondary" @click="addDay">+ Добавить ещё день</button>
    </div>

    <!-- Modal: meal participants -->
    <div v-if="participantsFor" class="modal-backdrop" @click.self="participantsFor = null">
      <div class="modal">
        <h3>{{ mealIcon(participantsFor.name) }} {{ participantsFor.name }} — участники</h3>
        <ParticipantPicker
          :people="people"
          :selectedIds="tempIds"
          @update:selectedIds="tempIds = $event"
        />
        <div class="row" style="justify-content:flex-end; margin-top:12px">
          <button class="secondary" @click="participantsFor = null">Отмена</button>
          <button @click="saveParticipants">Сохранить</button>
        </div>
      </div>
    </div>

    <!-- Modal: add dish -->
    <div v-if="addDishFor" class="modal-backdrop" @click.self="addDishFor = null">
      <div class="modal" style="max-width:560px">
        <h3>Добавить блюдо в «{{ addDishFor.name }}»</h3>
        <div class="form-block">
          <label class="form-label">📖 Из базы блюд</label>
          <div class="row">
            <select v-model="selectedCatalogDish" style="flex:1">
              <option :value="null">— выбрать —</option>
              <option v-for="cd in catalogDishes" :key="cd.id" :value="cd.id">{{ cd.name }}</option>
            </select>
            <button @click="addFromCatalog" :disabled="!selectedCatalogDish">Добавить</button>
          </div>
        </div>
        <div class="divider">или</div>
        <div class="form-block">
          <label class="form-label">＋ Своё новое блюдо</label>
          <div class="row">
            <input v-model="newDishName" placeholder="Название блюда" style="flex:1" />
            <button @click="addEmptyDish" :disabled="!newDishName.trim()">Создать</button>
          </div>
        </div>
        <div class="row" style="justify-content:flex-end; margin-top:14px">
          <button class="secondary" @click="addDishFor = null">Закрыть</button>
        </div>
      </div>
    </div>

    <!-- Modal: edit dish (with ingredient editor) -->
    <div v-if="editDish" class="modal-backdrop" @click.self="closeEdit">
      <div class="modal">
        <h3>Редактировать блюдо</h3>
        <div class="kv">
          <label>Название:</label>
          <input v-model="editDish.name" class="w-lg" autofocus />
        </div>
        <h4 style="margin-top:14px">Ингредиенты</h4>
        <table>
          <thead>
            <tr>
              <th style="width:55%">Продукт</th>
              <th class="right">г / порция</th>
              <th>Срок</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(ing, i) in editDish.ingredients" :key="i">
              <td>
                <ProductPicker :products="products" v-model="ing.product_id" />
              </td>
              <td><input type="number" v-model.number="ing.grams_per_portion" class="w-sm" /></td>
              <td>
                <span v-if="termOf(ing.product_id)" class="tag" :class="termClass(ing.product_id)">
                  {{ termOf(ing.product_id) }}
                </span>
              </td>
              <td class="right">
                <button class="ghost small danger-text" @click="editDish.ingredients.splice(i, 1)">×</button>
              </td>
            </tr>
            <tr v-if="!editDish.ingredients.length">
              <td colspan="4" class="muted center">Добавьте первый ингредиент ↓</td>
            </tr>
          </tbody>
        </table>
        <button class="secondary small" style="margin-top:8px" @click="editDish.ingredients.push(newIng())">
          + Ингредиент
        </button>

        <div v-if="editError" class="error">{{ editError }}</div>
        <div class="row" style="justify-content:flex-end; margin-top:16px">
          <button class="secondary" @click="closeEdit">Отмена</button>
          <button @click="saveEditDish">Сохранить</button>
        </div>
      </div>
    </div>
  </template>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { api } from '../api.js'
import ParticipantPicker from './ParticipantPicker.vue'
import ProductPicker from './ProductPicker.vue'

const props = defineProps({ eventId: { type: Number, required: true } })
const emit = defineEmits(['changed'])

const days = ref([])
const people = ref([])
const catalogDishes = ref([])
const products = ref([])
const productById = ref({})
const loading = ref(true)
const error = ref('')

const participantsFor = ref(null)
const tempIds = ref([])

const addDishFor = ref(null)
const selectedCatalogDish = ref(null)
const newDishName = ref('')

const editDish = ref(null)
const editError = ref('')

function newIng() {
  return { product_id: null, grams_per_portion: 0, taken: false }
}

function mealIcon(name) {
  const n = (name || '').toLowerCase()
  if (n.includes('завтрак')) return '🍳'
  if (n.includes('обед')) return '🥣'
  if (n.includes('ужин')) return '🍲'
  if (n.includes('перекус')) return '🥪'
  return '🍴'
}

function termOf(pid) { return productById.value[pid]?.storage_term || '' }
function termClass(pid) {
  const t = termOf(pid)
  if (!t) return ''
  return t.toLowerCase().startsWith('кратк') ? 'amber' : 'green'
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    const [full, ppl, dishes, prods] = await Promise.all([
      api.getEventFull(props.eventId),
      api.listPeople(),
      api.listDishes(),
      api.listProducts(),
    ])
    days.value = full.days
    people.value = ppl
    catalogDishes.value = dishes
    products.value = prods
    productById.value = Object.fromEntries(prods.map(p => [p.id, p]))
  } catch (e) { error.value = e.message }
  finally { loading.value = false }
}

async function refresh() {
  await load()
  emit('changed')
}

// ===== Days =====
async function addDay() {
  const sort = days.value.length
  await api.addDay(props.eventId, { name: `День ${sort + 1}`, short_name: '', sort_order: sort })
  await refresh()
}

async function updateDay(d) {
  await api.updateDay(d.id, { name: d.name, short_name: d.short_name || '', sort_order: d.sort_order })
  emit('changed')
}

async function deleteDay(d) {
  if (!confirm(`Удалить «${d.name}» со всеми приёмами пищи?`)) return
  await api.deleteDay(d.id)
  await refresh()
}

async function moveDay(idx, dir) {
  const j = idx + dir
  if (j < 0 || j >= days.value.length) return
  const a = days.value[idx], b = days.value[j]
  ;[a.sort_order, b.sort_order] = [b.sort_order, a.sort_order]
  await Promise.all([updateDay(a), updateDay(b)])
  await refresh()
}

// ===== Meals =====
async function addPresetMeal(day, name) {
  const sort = day.meals.length
  await api.addMeal(day.id, { name, sort_order: sort })
  await refresh()
}

async function updateMeal(m) {
  await api.updateMeal(m.id, { name: m.name, sort_order: m.sort_order })
  emit('changed')
}

async function deleteMeal(m) {
  if (!confirm(`Удалить «${m.name}»?`)) return
  await api.deleteMeal(m.id)
  await refresh()
}

async function moveMeal(day, idx, dir) {
  const j = idx + dir
  if (j < 0 || j >= day.meals.length) return
  const a = day.meals[idx], b = day.meals[j]
  ;[a.sort_order, b.sort_order] = [b.sort_order, a.sort_order]
  await Promise.all([updateMeal(a), updateMeal(b)])
  await refresh()
}

// ===== Participants =====
function openParticipants(m) {
  participantsFor.value = m
  tempIds.value = [...m.participant_ids]
}

async function saveParticipants() {
  await api.setMealParticipants(participantsFor.value.id, tempIds.value)
  participantsFor.value = null
  await refresh()
}

// ===== Add dish =====
function openAddDish(m) {
  addDishFor.value = m
  selectedCatalogDish.value = null
  newDishName.value = ''
}

async function addFromCatalog() {
  await api.addDishFromCatalog(addDishFor.value.id, selectedCatalogDish.value)
  addDishFor.value = null
  await refresh()
}

async function addEmptyDish() {
  const meal = addDishFor.value
  const created = await api.addDishToMeal(meal.id, { name: newDishName.value.trim(), sort_order: 0, ingredients: [] })
  addDishFor.value = null
  await refresh()
  // сразу открыть для заполнения ингредиентов
  const fresh = days.value.flatMap(d => d.meals).flatMap(m => m.dishes).find(d => d.id === created.id)
  if (fresh) openEditDish(fresh)
}

// ===== Edit / remove dish =====
function openEditDish(dsh) {
  editDish.value = {
    id: dsh.id,
    name: dsh.name,
    sort_order: dsh.sort_order || 0,
    ingredients: dsh.ingredients.map(i => ({
      product_id: i.product_id,
      grams_per_portion: i.grams_per_portion,
      taken: i.taken,
    })),
  }
  editError.value = ''
}

function closeEdit() {
  editDish.value = null
}

async function saveEditDish() {
  editError.value = ''
  if (!editDish.value.name.trim()) { editError.value = 'Укажите название.'; return }
  const payload = {
    name: editDish.value.name.trim(),
    sort_order: editDish.value.sort_order || 0,
    ingredients: editDish.value.ingredients
      .filter(i => i.product_id)
      .map(i => ({
        product_id: i.product_id,
        grams_per_portion: Number(i.grams_per_portion) || 0,
        taken: !!i.taken,
      })),
  }
  try {
    await api.updateEventDish(editDish.value.id, payload)
    editDish.value = null
    await refresh()
  } catch (e) { editError.value = e.message }
}

async function removeDish(dsh) {
  if (!confirm(`Удалить блюдо «${dsh.name}»?`)) return
  await api.deleteEventDish(dsh.id)
  await refresh()
}

watch(() => props.eventId, load)
onMounted(load)
defineExpose({ reload: load })
</script>

<style>
.empty-hero {
  background: #fff;
  border: 1px dashed var(--green-500);
  border-radius: var(--radius);
  padding: 48px 20px;
  text-align: center;
  margin-bottom: 16px;
}
.empty-hero .big { font-size: 56px; margin-bottom: 12px; opacity: 0.7; }
.empty-hero p { color: var(--muted); margin: 0 0 16px; }

.day-card { padding: 16px 18px; }

.day-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
  gap: 12px;
}
.day-title {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
  min-width: 0;
}
.day-num {
  font-weight: 700;
  color: var(--green-700);
  background: var(--green-50);
  padding: 4px 12px;
  border-radius: 999px;
  font-size: 13px;
  white-space: nowrap;
}
.day-name-input {
  flex: 1;
  border: 0;
  border-bottom: 1px solid transparent;
  background: transparent;
  font-size: 17px;
  font-weight: 600;
  color: var(--green-900);
  padding: 4px 0;
  border-radius: 0;
  min-width: 0;
}
.day-name-input:focus {
  outline: 0;
  border-bottom-color: var(--green-600);
  box-shadow: none;
}

.meal-block {
  background: var(--green-50);
  border: 1px solid var(--green-100);
  border-radius: 10px;
  padding: 12px 14px;
  margin-top: 12px;
}
.meal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}
.meal-title {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
  min-width: 0;
}
.meal-icon { font-size: 20px; }
.meal-name-input {
  flex: 1;
  border: 0;
  background: transparent;
  font-size: 15px;
  font-weight: 600;
  color: var(--green-900);
  padding: 2px 0;
  border-bottom: 1px solid transparent;
  border-radius: 0;
  min-width: 0;
}
.meal-name-input:focus {
  outline: 0;
  border-bottom-color: var(--green-600);
  box-shadow: none;
}

.dish-list {
  list-style: none;
  margin: 10px 0 8px;
  padding: 0;
  background: #fff;
  border: 1px solid var(--border);
  border-radius: 8px;
  overflow: hidden;
}
.dish-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 9px 12px;
  border-bottom: 1px solid var(--border);
}
.dish-row:last-child { border-bottom: 0; }
.dish-row:hover { background: var(--green-50); }
.dish-info { display: flex; align-items: center; gap: 8px; }
.dish-bullet { color: var(--green-600); font-weight: bold; }
.dish-name-text { font-weight: 500; color: var(--text); }

.add-dish-btn {
  margin-top: 6px;
  background: transparent;
  color: var(--green-800);
  border: 1px dashed var(--green-500);
  box-shadow: none;
  width: 100%;
  padding: 9px;
}
.add-dish-btn:hover {
  background: var(--green-100);
  transform: none;
}

.add-meal-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 14px;
  padding-top: 12px;
  border-top: 1px dashed var(--border);
}

.chip {
  background: #fff;
  color: var(--green-800);
  border: 1px solid var(--border);
  padding: 5px 12px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 500;
  box-shadow: none;
}
.chip:hover {
  background: var(--green-50);
  border-color: var(--green-600);
  transform: none;
}

.add-day-wrap {
  margin-top: 8px;
  text-align: center;
}

.form-block { margin-bottom: 10px; }
.form-label {
  display: block;
  font-size: 12px;
  font-weight: 600;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  margin-bottom: 6px;
}

.divider {
  text-align: center;
  color: var(--muted);
  margin: 14px 0;
  position: relative;
}
.divider::before, .divider::after {
  content: '';
  position: absolute;
  top: 50%;
  width: 40%;
  height: 1px;
  background: var(--border);
}
.divider::before { left: 0; }
.divider::after { right: 0; }

button.ghost.danger-text { color: var(--berry); }
button.ghost.danger-text:hover { background: #fde2e2; }

button.ghost:disabled { opacity: 0.3; }
</style>
