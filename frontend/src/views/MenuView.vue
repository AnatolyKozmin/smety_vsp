<template>
  <div class="toolbar">
    <h2 style="margin:0">🍲 Меню</h2>
    <div class="row" v-if="selectedEvent">
      <router-link :to="`/events/${selectedId}/estimate`"><button class="secondary">Смета</button></router-link>
      <router-link :to="`/events/${selectedId}/edit`"><button class="secondary">Редактор заброса</button></router-link>
    </div>
  </div>

  <div v-if="error" class="error">{{ error }}</div>

  <div v-if="events.length === 0" class="empty">
    Нет забросов. <router-link to="/events">Создайте заброс</router-link>, чтобы собрать для него меню.
  </div>

  <template v-else>
    <div class="card">
      <div class="row">
        <label>Заброс:</label>
        <select v-model.number="selectedId" @change="onSelect">
          <option v-for="e in events" :key="e.id" :value="e.id">{{ e.name }}</option>
        </select>
        <span class="muted">— составьте меню: дни → приёмы пищи → блюда</span>
      </div>
    </div>

    <MenuBuilder v-if="selectedId" :key="selectedId" :event-id="selectedId" />
  </template>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../api.js'
import MenuBuilder from '../components/MenuBuilder.vue'

const route = useRoute()
const router = useRouter()

const events = ref([])
const selectedId = ref(null)
const error = ref('')

const selectedEvent = computed(() => events.value.find(e => e.id === selectedId.value))

function onSelect() {
  router.replace(`/menu/${selectedId.value}`)
}

async function load() {
  try {
    events.value = await api.listEvents()
    const fromRoute = Number(route.params.id)
    if (fromRoute && events.value.some(e => e.id === fromRoute)) {
      selectedId.value = fromRoute
    } else if (events.value.length) {
      selectedId.value = events.value[0].id
    }
  } catch (e) { error.value = e.message }
}

onMounted(load)
</script>
