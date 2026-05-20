<template>
  <h2>📖 База блюд</h2>

  <div class="toolbar">
    <div class="row">
      <input v-model="filter" class="w-lg" placeholder="Поиск по названию блюда…" />
      <span class="muted">{{ filtered.length }} / {{ dishes.length }}</span>
    </div>
    <button @click="startNew">+ Новое блюдо</button>
  </div>

  <div v-if="error" class="error">{{ error }}</div>

  <div v-if="loading" class="muted">Загрузка…</div>
  <div v-else-if="!filtered.length" class="empty">
    <div class="big">🍲</div>
    Ничего не нашлось
  </div>

  <div v-for="d in filtered" :key="d.id" class="card">
    <div class="toolbar" style="margin:0 0 8px 0">
      <h3 style="margin:0">{{ d.name }}</h3>
      <div class="row">
        <span class="muted">всего {{ totalGrams(d) }} г на порцию</span>
        <button class="secondary small" @click="startEdit(d)">Изменить</button>
        <button class="danger small" @click="remove(d)">×</button>
      </div>
    </div>
    <table v-if="d.ingredients.length">
      <thead>
        <tr>
          <th>Продукт</th>
          <th class="right">г / порция</th>
          <th>Ед.</th>
          <th class="right">Г в уп.</th>
          <th>Срок</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="i in d.ingredients" :key="i.id">
          <td>{{ i.product.name }}</td>
          <td class="right">{{ i.grams_per_portion }}</td>
          <td>{{ i.product.unit }}</td>
          <td class="right">{{ i.product.grams_in_package }}</td>
          <td>
            <span class="tag" :class="termClass(i.product.storage_term)">{{ i.product.storage_term }}</span>
          </td>
        </tr>
      </tbody>
    </table>
    <div v-else class="muted">Ингредиентов нет.</div>
  </div>

  <div v-if="editing" class="modal-backdrop" @click.self="editing = null">
    <div class="modal">
      <h3>{{ editing.id ? 'Изменить блюдо' : 'Новое блюдо' }}</h3>
      <div class="row">
        <label>Название:</label>
        <input v-model="editing.name" class="w-lg" placeholder="Название блюда" autofocus />
      </div>

      <h3>Ингредиенты</h3>
      <table>
        <thead>
          <tr>
            <th style="width:55%">Продукт</th>
            <th>г / порция</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(ing, idx) in editing.ingredients" :key="idx">
            <td>
              <ProductPicker
                :products="products"
                v-model="ing.product_id"
                placeholder="Начните вводить…"
              />
            </td>
            <td><input type="number" v-model.number="ing.grams_per_portion" class="w-sm" /></td>
            <td class="right">
              <button class="danger small" @click="editing.ingredients.splice(idx, 1)">×</button>
            </td>
          </tr>
        </tbody>
      </table>
      <button class="secondary small" style="margin-top:8px" @click="addIng">+ Ингредиент</button>

      <div v-if="modalError" class="error">{{ modalError }}</div>

      <div class="row" style="margin-top:18px; justify-content:flex-end">
        <button class="secondary" @click="editing = null">Отмена</button>
        <button @click="save">Сохранить</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { api } from '../api.js'
import ProductPicker from '../components/ProductPicker.vue'

const dishes = ref([])
const products = ref([])
const loading = ref(true)
const error = ref('')
const editing = ref(null)
const modalError = ref('')
const filter = ref('')

function termClass(t) {
  if (!t) return ''
  return t.toLowerCase().startsWith('кратк') ? 'amber' : 'green'
}

function totalGrams(d) {
  return d.ingredients.reduce((sum, i) => sum + (i.grams_per_portion || 0), 0)
}

const filtered = computed(() => {
  const q = filter.value.trim().toLowerCase()
  if (!q) return dishes.value
  return dishes.value.filter(d => d.name.toLowerCase().includes(q))
})

async function load() {
  loading.value = true
  error.value = ''
  try {
    [dishes.value, products.value] = await Promise.all([api.listDishes(), api.listProducts()])
  } catch (e) { error.value = e.message } finally { loading.value = false }
}

function startNew() {
  editing.value = { id: null, name: '', ingredients: [] }
  modalError.value = ''
}

function startEdit(d) {
  editing.value = {
    id: d.id,
    name: d.name,
    ingredients: d.ingredients.map(i => ({ product_id: i.product_id, grams_per_portion: i.grams_per_portion })),
  }
  modalError.value = ''
}

function addIng() {
  editing.value.ingredients.push({ product_id: null, grams_per_portion: 0 })
}

async function save() {
  modalError.value = ''
  if (!editing.value.name.trim()) { modalError.value = 'Укажите название.'; return }
  const ingredients = editing.value.ingredients
    .filter(i => i.product_id)
    .map(i => ({ product_id: i.product_id, grams_per_portion: Number(i.grams_per_portion) || 0 }))
  try {
    const payload = { name: editing.value.name.trim(), ingredients }
    if (editing.value.id) await api.updateDish(editing.value.id, payload)
    else await api.createDish(payload)
    editing.value = null
    await load()
  } catch (e) { modalError.value = e.message }
}

async function remove(d) {
  if (!confirm(`Удалить блюдо «${d.name}»?`)) return
  try { await api.deleteDish(d.id); await load() } catch (e) { error.value = e.message }
}

onMounted(load)
</script>
