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
      <span class="muted">{{ filtered.length }} / {{ products.length }}</span>
    </div>
    <button @click="startNew">+ Новый продукт</button>
  </div>

  <div v-if="error" class="error">{{ error }}</div>

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
        <tr v-for="p in filtered" :key="p.id">
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
        <tr v-if="!filtered.length">
          <td colspan="6" class="empty">
            <div class="big">🌾</div>
            Ничего не нашлось
          </td>
        </tr>
      </tbody>
    </table>
  </div>

  <div v-if="editing" class="modal-backdrop" @click.self="editing = null">
    <div class="modal" style="max-width:520px">
      <h3>{{ editing.id ? 'Изменить продукт' : 'Новый продукт' }}</h3>
      <div class="kv">
        <label>Название:</label>
        <input v-model="editing.name" autofocus />
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

const products = ref([])
const error = ref('')
const editing = ref(null)
const modalError = ref('')
const filter = ref('')
const termFilter = ref('')

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
    return true
  })
})

async function load() {
  try { products.value = await api.listProducts() } catch (e) { error.value = e.message }
}

function startNew() {
  editing.value = {
    id: null, name: '', unit: 'кг', grams_in_package: 1000,
    price_per_unit: 0, storage_term: 'Долгосрочный', product_link: '',
  }
  modalError.value = ''
}

function startEdit(p) {
  editing.value = { ...p }
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
