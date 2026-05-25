<template>
  <div class="toolbar">
    <h2 style="margin:0">🎟 Гости</h2>
    <div v-if="selectedId">
      <router-link :to="`/events/${selectedId}/edit`">
        <button class="secondary">Редактор</button>
      </router-link>
    </div>
  </div>

  <div v-if="error" class="error">{{ error }}</div>

  <div v-if="events.length === 0" class="empty-hero">
    <div class="big">🌲</div>
    <p>Нет ни одного заброса.</p>
    <router-link to="/events"><button>+ Создать заброс</button></router-link>
  </div>

  <template v-else>
    <div class="card">
      <div class="row">
        <label>Заброс:</label>
        <select v-model.number="selectedId" @change="onSelect" style="flex:1; max-width:340px">
          <option v-for="e in events" :key="e.id" :value="e.id">{{ e.name }}</option>
        </select>
      </div>
    </div>

    <GuestsTab v-if="selectedId" :key="selectedId" :event-id="selectedId" />
  </template>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../api.js'
import GuestsTab from '../components/GuestsTab.vue'

const route = useRoute()
const router = useRouter()

const events = ref([])
const selectedId = ref(null)
const error = ref('')

function onSelect() {
  router.replace(`/guests/${selectedId.value}`)
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

<style scoped>
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
