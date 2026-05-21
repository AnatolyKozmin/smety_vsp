<template>
  <div v-if="loading" class="muted">Загрузка…</div>
  <div v-else-if="error" class="error">{{ error }}</div>
  <template v-else-if="event">

    <div class="event-header">
      <router-link to="/events" class="back-link">← К списку забросов</router-link>
      <div class="event-title-row">
        <h2 style="margin:0">🏕️ {{ event.name }}</h2>
        <div class="row">
          <router-link :to="`/events/${eventId}/shopping`"><button class="secondary">🛒 Список покупок</button></router-link>
          <router-link :to="`/events/${eventId}/estimate`"><button class="secondary">📊 Смета</button></router-link>
          <router-link :to="`/events/${eventId}/contributions`"><button class="secondary">💰 Взносы</button></router-link>
        </div>
      </div>
      <div class="muted small-meta">
        {{ statsLine }}
      </div>
    </div>

    <div class="tabs">
      <button :class="['tab', { active: tab === 'menu' }]" @click="tab = 'menu'">🍲 Меню</button>
      <button :class="['tab', { active: tab === 'misc' }]" @click="tab = 'misc'">🧂 Прочее <span class="tab-count">{{ miscItems.length }}</span></button>
      <button :class="['tab', { active: tab === 'settings' }]" @click="tab = 'settings'">⚙️ Настройки</button>
    </div>

    <!-- ===== MENU TAB ===== -->
    <div v-show="tab === 'menu'">
      <MenuBuilder :event-id="eventId" />
    </div>

    <!-- ===== MISC TAB ===== -->
    <div v-show="tab === 'misc'">
      <div class="card">
        <div class="hint-block">
          🧂 «Прочее» — закупка, не привязанная к конкретным блюдам: хлеб, соль, специи, мусорные мешки.
          Указывайте количество <b>в упаковках/банках</b> — это попадёт в общий список покупок.
        </div>

        <table v-if="miscItems.length">
          <thead>
            <tr>
              <th>Продукт</th>
              <th class="right">Кол-во</th>
              <th>Ед.</th>
              <th>Срок</th>
              <th class="center">Взяли?</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="i in miscItems" :key="i.id">
              <td>{{ i.product.name }}</td>
              <td class="right">
                <input type="number" v-model.number="i.quantity" class="w-sm" @change="saveMisc(i)" />
              </td>
              <td class="muted">{{ i.product.unit }}</td>
              <td><span class="tag" :class="termClass(i.product.storage_term)">{{ i.product.storage_term }}</span></td>
              <td class="center">
                <input type="checkbox" v-model="i.taken" @change="saveMisc(i)" />
              </td>
              <td class="right">
                <button class="ghost small danger-text" @click="removeMisc(i)">🗑</button>
              </td>
            </tr>
          </tbody>
        </table>
        <div v-else class="muted center" style="padding:18px">Пока ничего не добавлено.</div>

        <div class="add-misc-bar">
          <ProductPicker
            :products="products"
            v-model="newMisc.product_id"
            placeholder="Выберите продукт…"
          />
          <input type="number" v-model.number="newMisc.quantity" placeholder="Кол-во" class="w-sm" />
          <button @click="addMisc" :disabled="!newMisc.product_id">+ Добавить</button>
        </div>
      </div>

      <div class="card">
        <h4 style="margin-top:0">Кто скидывается на «Прочее»</h4>
        <div class="muted" style="margin-bottom:8px">
          Сейчас выбрано: <b>{{ miscParticipantIds.length }}</b> чел.
        </div>
        <button class="secondary" @click="openMiscParticipants">👥 Выбрать участников</button>
      </div>

      <div v-if="miscParticipantsOpen" class="modal-backdrop" @click.self="miscParticipantsOpen = false">
        <div class="modal">
          <h3>Кто скидывается на «Прочее»</h3>
          <ParticipantPicker
            :people="people"
            :selectedIds="miscTempIds"
            @update:selectedIds="miscTempIds = $event"
          />
          <div class="row" style="justify-content:flex-end; margin-top:12px">
            <button class="secondary" @click="miscParticipantsOpen = false">Отмена</button>
            <button @click="saveMiscParticipants">Сохранить</button>
          </div>
        </div>
      </div>
    </div>

    <!-- ===== SETTINGS TAB ===== -->
    <div v-show="tab === 'settings'">
      <div class="card">
        <h3 style="margin-top:0">Параметры заброса</h3>
        <div class="kv">
          <label>Название:</label>
          <input v-model="event.name" class="w-lg" />
          <label>Наценка, %:</label>
          <input type="number" v-model.number="event.markup_percent" class="w-sm" />
        </div>
        <div class="row" style="margin-top:14px">
          <button @click="saveEvent">Сохранить</button>
        </div>
      </div>

      <div class="card">
        <h3 style="margin-top:0">Массовое количество людей</h3>
        <div class="hint-block">
          Удобно для забросов с большим числом людей, где имена не нужны — например, общий заезд участников.
          Поставит число во все приёмы пищи всех дней (можно потом перебить в конкретном приёме). 0 = сбросить.
        </div>
        <div class="row">
          <input type="number" v-model.number="bulkPortions" placeholder="50" class="w-sm" min="0" />
          <button @click="applyBulkPortions">Задать всем</button>
        </div>
      </div>

      <div class="card" style="border-color: #f0a8a8">
        <h3 style="margin-top:0; color: var(--berry)">Опасная зона</h3>
        <p class="muted">Удалит весь заброс со всеми днями, приёмами пищи, прочим и платежами.</p>
        <button class="danger" @click="deleteEvent">🗑 Удалить заброс</button>
      </div>
    </div>

  </template>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../api.js'
import ParticipantPicker from '../components/ParticipantPicker.vue'
import MenuBuilder from '../components/MenuBuilder.vue'
import ProductPicker from '../components/ProductPicker.vue'

const route = useRoute()
const router = useRouter()
const eventId = Number(route.params.id)

const event = ref(null)
const loading = ref(true)
const error = ref('')
const people = ref([])
const products = ref([])
const miscItems = ref([])
const miscParticipantIds = ref([])
const newMisc = ref({ product_id: null, quantity: 1 })
const tab = ref('menu')

const miscParticipantsOpen = ref(false)
const miscTempIds = ref([])
const bulkPortions = ref(0)

const statsLine = computed(() => {
  if (!event.value) return ''
  return `Наценка ${event.value.markup_percent}% · ${event.value.days_count} ${plural(event.value.days_count, 'день', 'дня', 'дней')}`
})

function plural(n, one, few, many) {
  n = Math.abs(n) % 100
  const n1 = n % 10
  if (n > 10 && n < 20) return many
  if (n1 > 1 && n1 < 5) return few
  if (n1 === 1) return one
  return many
}

function termClass(t) {
  if (!t) return ''
  return t.toLowerCase().startsWith('кратк') ? 'amber' : 'green'
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    const [full, ppl, prods] = await Promise.all([
      api.getEventFull(eventId),
      api.listPeople(),
      api.listProducts(),
    ])
    event.value = {
      id: full.id,
      name: full.name,
      markup_percent: full.markup_percent,
      days_count: full.days.length,
    }
    miscItems.value = full.misc_items
    miscParticipantIds.value = full.misc_participant_ids
    people.value = ppl
    products.value = prods
  } catch (e) { error.value = e.message }
  finally { loading.value = false }
}

async function saveEvent() {
  await api.updateEvent(eventId, { name: event.value.name, markup_percent: event.value.markup_percent })
}

async function applyBulkPortions() {
  const n = Number(bulkPortions.value) || 0
  if (n > 0 && !confirm(`Поставить ${n} чел. на ВСЕ приёмы пищи всех дней? Текущие значения перезапишутся.`)) return
  if (n <= 0 && !confirm('Сбросить кол-во людей у всех приёмов (вернуться к расчёту по списку участников)?')) return
  await api.setAllPortions(eventId, n)
  alert(n > 0 ? `Поставлено ${n} чел. на все приёмы пищи.` : 'Сброшено.')
}

async function deleteEvent() {
  if (!confirm(`Удалить заброс «${event.value.name}»? Это действие нельзя отменить.`)) return
  await api.deleteEvent(eventId)
  router.push('/events')
}

async function addMisc() {
  if (!newMisc.value.product_id) return
  await api.addMisc(eventId, {
    product_id: newMisc.value.product_id,
    quantity: Number(newMisc.value.quantity) || 0,
    taken: false,
  })
  newMisc.value = { product_id: null, quantity: 1 }
  await load()
}

async function saveMisc(i) {
  await api.updateMisc(i.id, {
    product_id: i.product.id,
    quantity: Number(i.quantity) || 0,
    taken: !!i.taken,
  })
}

async function removeMisc(i) {
  if (!confirm(`Удалить «${i.product.name}» из прочего?`)) return
  await api.deleteMisc(i.id)
  await load()
}

function openMiscParticipants() {
  miscTempIds.value = [...miscParticipantIds.value]
  miscParticipantsOpen.value = true
}

async function saveMiscParticipants() {
  await api.setMiscParticipants(eventId, miscTempIds.value)
  miscParticipantsOpen.value = false
  await load()
}

onMounted(load)
</script>

<style scoped>
.event-header {
  margin-bottom: 16px;
}
.back-link {
  display: inline-block;
  margin-bottom: 8px;
  font-size: 13px;
  color: var(--muted);
}
.back-link:hover { color: var(--green-800); }
.event-title-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}
.small-meta { font-size: 13px; margin-top: 4px; }

.tabs {
  display: flex;
  gap: 4px;
  margin-bottom: 16px;
  border-bottom: 2px solid var(--border);
}
.tab {
  background: transparent;
  color: var(--muted);
  border: 0;
  border-bottom: 2px solid transparent;
  border-radius: 0;
  padding: 10px 18px;
  font-weight: 500;
  font-size: 14px;
  box-shadow: none;
  margin-bottom: -2px;
}
.tab:hover {
  color: var(--green-800);
  background: transparent;
  transform: none;
}
.tab.active {
  color: var(--green-900);
  border-bottom-color: var(--green-700);
  background: transparent;
}
.tab-count {
  display: inline-block;
  background: var(--green-100);
  color: var(--green-800);
  border-radius: 999px;
  padding: 1px 8px;
  font-size: 11px;
  margin-left: 4px;
}
.tab.active .tab-count {
  background: var(--green-700);
  color: #fff;
}

.hint-block {
  background: var(--green-50);
  border-left: 3px solid var(--green-600);
  padding: 10px 14px;
  border-radius: 6px;
  font-size: 13px;
  color: var(--green-900);
  margin-bottom: 12px;
}

.add-misc-bar {
  display: flex;
  gap: 8px;
  margin-top: 12px;
  align-items: center;
  flex-wrap: wrap;
}
.add-misc-bar > .combo { flex: 1; min-width: 220px; }
</style>
