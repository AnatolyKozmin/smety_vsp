<template>
  <h2>🥕 Продукты</h2>

  <div class="toolbar">
    <div class="row">
      <input v-model="filter" class="w-lg" placeholder="Поиск по названию..." />
      <select v-model="termFilter">
        <option value="">Срок: любой</option>
        <option>Краткосрочный</option>
        <option>Долгосрочный</option>
      </select>
      <select v-model="categoryFilter">
        <option value="">Категория: все</option>
        <option v-for="c in CATEGORIES" :key="c">{{ categoryIcon(c) }} {{ c }}</option>
      </select>
      <span class="muted">{{ filtered.length }} / {{ products.length }}</span>
    </div>
    <button @click="startNew">+ Новый продукт</button>
  </div>

  <div v-if="error" class="error">{{ error }}</div>

  <!-- Группировка по категориям -->
  <div v-for="cat in visibleCategories" :key="cat" class="cat-block">
    <h3>{{ categoryIcon(cat) }} {{ cat }} <span class="muted">({{ groupedFiltered[cat].length }})</span></h3>
    <div class="card" style="padding:0">
      <table>
        <thead>
          <tr>
            <th>Продукт</th>
            <th>Ед. изм.</th>
            <th class="right">Г в упаковке</th>
            <th class="right">₽ за упаковку</th>
            <th>Срок</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="p in groupedFiltered[cat]" :key="p.id">
            <td><b>{{ p.name }}</b></td>
            <td>{{ p.unit }}</td>
            <td class="right">{{ p.grams_in_package || '—' }}</td>
            <td class="right">{{ p.price_per_unit ? p.price_per_unit + ' ₽' : '—' }}</td>
            <td>
              <span class="tag" :class="termClass(p.storage_term)">{{ p.storage_term }}</span>
            </td>
            <td class="right nowrap">
              <button class="secondary small" @click="startEdit(p)">Изменить</button>
              <button class="danger small" @click="remove(p)" style="margin-left:6px">×</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>

  <div v-if="!visibleCategories.length" class="empty">
    <div class="big">🌾</div>
    Ничего не нашлось
  </div>

  <div v-if="editing" class="modal-backdrop" @click.self="editing = null">
    <div class="modal" style="max-width:520px">
      <h3>{{ editing.id ? 'Изменить продукт' : 'Новый продукт' }}</h3>
      <div class="kv">
        <label>Название:</label>
        <input v-model="editing.name" autofocus />
        <label>Категория:</label>
        <select v-model="editing.category">
          <option v-for="c in CATEGORIES" :key="c" :value="c">{{ categoryIcon(c) }} {{ c }}</option>
        </select>
        <label>Единица:</label>
        <input v-model="editing.unit" placeholder="кг, пачка, банка, г…" class="w-md" />
        <label>Грамм в упаковке:</label>
        <input type="number" v-model.number="editing.grams_in_package" class="w-sm" />
        <label>Цена за упаковку, ₽:</label>
        <input type="number" v-model.number="editing.price_per_unit" class="w-sm" />
        <label>Срок хранения:</label>
        <select v-model="editing.storage_term">
          <option>Краткосрочный</option>
          <option>Долгосрочный</option>
        </select>
        <label>Ссылка (опц.):</label>
        <input v-model="editing.product_link" placeholder="https://..." />
      </div>
      <div v-if="modalError" class="error">{{ modalError }}</div>
      <div class="row" style="justify-content:flex-end; margin-top:18px">
        <button class="secondary" @click="editing = null">Отмена</button>
        <button @click="save">Сохранить</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { api } from '../api.js'

const CATEGORIES = ['овощи-фрукты', 'мясо', 'молочка', 'крупы', 'приправы', 'прочее']

function categoryIcon(c) {
  return ({
    'овощи-фрукты': '🥕',
    'мясо': '🥩',
    'молочка': '🥛',
    'крупы': '🌾',
    'приправы': '🧂',
    'прочее': '📦',
  })[c] || '📦'
}

const products = ref([])
const error = ref('')
const editing = ref(null)
const modalError = ref('')
const filter = ref('')
const termFilter = ref('')
const categoryFilter = ref('')

function termClass(t) {
  if (!t) return ''
  if (t.toLowerCase().startsWith('кратк')) return 'amber'
  return 'green'
}

const filtered = computed(() => {
  const q = filter.value.trim().toLowerCase()
  return products.value.filter(p => {
    if (q && !p.name.toLowerCase().includes(q)) return false
    if (termFilter.value && p.storage_term !== termFilter.value) return false
    if (categoryFilter.value && p.category !== categoryFilter.value) return false
    return true
  })
})

const groupedFiltered = computed(() => {
  const g = {}
  for (const c of CATEGORIES) g[c] = []
  for (const p of filtered.value) {
    const c = CATEGORIES.includes(p.category) ? p.category : 'прочее'
    g[c].push(p)
  }
  for (const c of CATEGORIES) g[c].sort((a, b) => a.name.localeCompare(b.name, 'ru'))
  return g
})

const visibleCategories = computed(() =>
  CATEGORIES.filter(c => groupedFiltered.value[c].length > 0)
)

async function load() {
  try { products.value = await api.listProducts() } catch (e) { error.value = e.message }
}

function startNew() {
  editing.value = {
    id: null, name: '', unit: 'кг', grams_in_package: 1000,
    price_per_unit: 0, storage_term: 'Долгосрочный',
    category: 'прочее', product_link: '',
  }
  modalError.value = ''
}

function startEdit(p) {
  editing.value = { ...p, category: p.category || 'прочее' }
  modalError.value = ''
}

async function save() {
  if (!editing.value.name.trim()) { modalError.value = 'Укажите название.'; return }
  const data = {
    name: editing.value.name.trim(),
    unit: (editing.value.unit || 'г').trim(),
    grams_in_package: Number(editing.value.grams_in_package) || 0,
    price_per_unit: Number(editing.value.price_per_unit) || 0,
    storage_term: editing.value.storage_term || 'Долгосрочный',
    category: editing.value.category || 'прочее',
    product_link: editing.value.product_link || '',
  }
  try {
    if (editing.value.id) await api.updateProduct(editing.value.id, data)
    else await api.createProduct(data)
    editing.value = null
    await load()
  } catch (e) { modalError.value = e.message }
}

async function remove(p) {
  if (!confirm(`Удалить продукт «${p.name}»?`)) return
  try { await api.deleteProduct(p.id); await load() }
  catch (e) { error.value = e.message }
}

onMounted(load)
</script>

<style scoped>
.cat-block { margin-bottom: 20px; }
.cat-block h3 { margin: 16px 0 8px; }
</style>
