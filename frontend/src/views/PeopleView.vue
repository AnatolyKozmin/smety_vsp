<template>
  <h2>🧑‍🤝‍🧑 Участники</h2>

  <div class="toolbar">
    <div class="muted">{{ people.length }} человек в списке</div>
    <button @click="startNew">+ Добавить</button>
  </div>

  <div v-if="error" class="error">{{ error }}</div>

  <div class="card">
    <table>
      <thead>
        <tr>
          <th>Роль</th>
          <th>ФИО</th>
          <th>Состояние</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="p in people" :key="p.id">
          <td><span class="tag blue">{{ p.role || '—' }}</span></td>
          <td>{{ p.full_name }}</td>
          <td>
            <span class="tag" :class="p.present ? 'green' : 'red'">
              {{ p.present ? 'Был' : 'Не был' }}
            </span>
          </td>
          <td class="right nowrap">
            <button class="secondary small" @click="startEdit(p)">Изменить</button>
            <button class="danger small" @click="remove(p)" style="margin-left:6px">Удалить</button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>

  <div v-if="editing" class="modal-backdrop" @click.self="editing = null">
    <div class="modal" style="max-width:480px">
      <h3>{{ editing.id ? 'Изменить' : 'Новый участник' }}</h3>
      <div class="kv">
        <label>ФИО:</label>
        <input v-model="editing.full_name" />
        <label>Роль:</label>
        <input v-model="editing.role" placeholder="Например: ГОИ" />
        <label>Состояние:</label>
        <label class="checkbox">
          <input type="checkbox" v-model="editing.present" /> Был
        </label>
      </div>
      <div v-if="modalError" class="error">{{ modalError }}</div>
      <div class="row" style="margin-top:16px; justify-content:flex-end">
        <button class="secondary" @click="editing = null">Отмена</button>
        <button @click="save">Сохранить</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../api.js'

const people = ref([])
const error = ref('')
const editing = ref(null)
const modalError = ref('')

async function load() {
  try { people.value = await api.listPeople() } catch (e) { error.value = e.message }
}

function startNew() {
  editing.value = { id: null, full_name: '', role: '', present: true }
  modalError.value = ''
}

function startEdit(p) {
  editing.value = { ...p }
  modalError.value = ''
}

async function save() {
  if (!editing.value.full_name.trim()) { modalError.value = 'Укажите ФИО.'; return }
  const data = {
    full_name: editing.value.full_name.trim(),
    role: (editing.value.role || '').trim(),
    present: !!editing.value.present,
  }
  try {
    if (editing.value.id) await api.updatePerson(editing.value.id, data)
    else await api.createPerson(data)
    editing.value = null
    await load()
  } catch (e) { modalError.value = e.message }
}

async function remove(p) {
  if (!confirm(`Удалить ${p.full_name}?`)) return
  try { await api.deletePerson(p.id); await load() }
  catch (e) { error.value = e.message }
}

onMounted(load)
</script>
