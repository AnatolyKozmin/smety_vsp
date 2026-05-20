<template>
  <div v-if="loading" class="muted">Загрузка…</div>
  <div v-else-if="error" class="error">{{ error }}</div>
  <template v-else-if="eventInfo">
    <div class="toolbar">
      <h2 style="margin:0">🛒 Что купить: {{ eventInfo.name }}</h2>
      <div class="row">
        <router-link :to="`/events/${eventId}/edit`"><button class="secondary">Редактор</button></router-link>
        <router-link :to="`/events/${eventId}/estimate`"><button class="secondary">📊 Смета</button></router-link>
        <button class="secondary" @click="printPage">🖨 Печать</button>
        <router-link to="/shopping"><button class="ghost">← Все покупки</button></router-link>
      </div>
    </div>

    <ShoppingListContent :event-id="eventId" />
  </template>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../api.js'
import ShoppingListContent from '../components/ShoppingListContent.vue'

const route = useRoute()
const eventId = Number(route.params.id)

const eventInfo = ref(null)
const loading = ref(true)
const error = ref('')

async function load() {
  loading.value = true
  try {
    const events = await api.listEvents()
    eventInfo.value = events.find(e => e.id === eventId) || null
    if (!eventInfo.value) error.value = 'Заброс не найден'
  } catch (e) { error.value = e.message }
  finally { loading.value = false }
}

function printPage() { window.print() }

onMounted(load)
</script>
