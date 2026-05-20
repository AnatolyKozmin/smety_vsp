<template>
  <h2>🏕️ Забросы</h2>

  <div class="toolbar">
    <div class="muted">Список смет для разных забросов</div>
    <button @click="creating = true">+ Новый заброс</button>
  </div>

  <div v-if="error" class="error">{{ error }}</div>

  <div v-if="events.length === 0" class="empty-hero">
    <div class="big">🌲</div>
    <p>Пока ни одного заброса.</p>
    <button @click="creating = true">+ Создать первый</button>
  </div>

  <div v-for="e in events" :key="e.id" class="event-card" @click="goToEditor(e)">
    <div class="event-card-main">
      <div class="event-card-icon">🏕️</div>
      <div class="event-card-info">
        <h3 class="event-card-title">{{ e.name }}</h3>
        <div class="muted small">Наценка {{ e.markup_percent }} %</div>
      </div>
    </div>
    <div class="event-card-actions" @click.stop>
      <router-link :to="`/events/${e.id}/shopping`" class="link-icon" title="Список покупок">🛒</router-link>
      <router-link :to="`/events/${e.id}/estimate`" class="link-icon" title="Смета">📊</router-link>
      <router-link :to="`/events/${e.id}/contributions`" class="link-icon" title="Взносы">💰</router-link>
      <button class="ghost small danger-text" @click="remove(e)" title="Удалить">🗑</button>
    </div>
  </div>

  <div v-if="creating" class="modal-backdrop" @click.self="creating = false">
    <div class="modal" style="max-width:480px">
      <h3>Новый заброс</h3>
      <div class="kv">
        <label>Название:</label>
        <input v-model="form.name" placeholder="Например: Вспышка'26" autofocus />
        <label>Наценка, %:</label>
        <input type="number" v-model.number="form.markup_percent" class="w-sm" />
      </div>
      <div v-if="createError" class="error">{{ createError }}</div>
      <div class="row" style="justify-content:flex-end; margin-top:16px">
        <button class="secondary" @click="creating = false">Отмена</button>
        <button @click="save">Создать</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api.js'

const router = useRouter()
const events = ref([])
const error = ref('')
const creating = ref(false)
const createError = ref('')
const form = ref({ name: '', markup_percent: 0 })

async function load() {
  try { events.value = await api.listEvents() } catch (e) { error.value = e.message }
}

function goToEditor(e) {
  router.push(`/events/${e.id}/edit`)
}

async function save() {
  createError.value = ''
  if (!form.value.name.trim()) { createError.value = 'Укажите название.'; return }
  try {
    const created = await api.createEvent({
      name: form.value.name.trim(),
      markup_percent: Number(form.value.markup_percent) || 0,
    })
    creating.value = false
    form.value = { name: '', markup_percent: 0 }
    // сразу в редактор
    router.push(`/events/${created.id}/edit`)
  } catch (e) { createError.value = e.message }
}

async function remove(e) {
  if (!confirm(`Удалить заброс «${e.name}»? Все данные сметы будут потеряны.`)) return
  try { await api.deleteEvent(e.id); await load() }
  catch (err) { error.value = err.message }
}

onMounted(load)
</script>

<style scoped>
.event-card {
  background: #fff;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 14px 18px;
  margin-bottom: 10px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  box-shadow: var(--shadow);
  transition: all 0.12s;
}
.event-card:hover {
  border-color: var(--green-600);
  transform: translateY(-1px);
  box-shadow: var(--shadow-lg);
}
.event-card-main { display: flex; align-items: center; gap: 14px; flex: 1; min-width: 0; }
.event-card-icon { font-size: 28px; }
.event-card-info { min-width: 0; }
.event-card-title {
  margin: 0;
  font-size: 17px;
  font-weight: 600;
  color: var(--green-900);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.small { font-size: 12px; }

.event-card-actions {
  display: flex;
  gap: 4px;
  align-items: center;
}
.link-icon {
  display: inline-flex;
  width: 34px; height: 34px;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  border-radius: 8px;
  text-decoration: none;
  transition: background 0.12s;
}
.link-icon:hover { background: var(--green-50); text-decoration: none; }

.empty-hero {
  background: #fff;
  border: 1px dashed var(--green-500);
  border-radius: var(--radius);
  padding: 56px 20px;
  text-align: center;
}
.empty-hero .big { font-size: 64px; margin-bottom: 14px; opacity: 0.7; }
.empty-hero p { color: var(--muted); margin: 0 0 16px; font-size: 15px; }
</style>
