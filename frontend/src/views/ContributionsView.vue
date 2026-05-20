<template>
  <div v-if="loading" class="muted">Расчёт…</div>
  <div v-else-if="error" class="error">{{ error }}</div>
  <template v-else-if="data">
    <div class="toolbar">
      <h2 style="margin:0">💰 Взносы: {{ data.event.name }}</h2>
      <div class="row">
        <router-link :to="`/events/${eventId}/edit`"><button class="secondary">Редактор</button></router-link>
        <router-link :to="`/events/${eventId}/estimate`"><button class="secondary">Смета</button></router-link>
        <router-link to="/events"><button class="secondary">← К списку</button></router-link>
      </div>
    </div>

    <div class="summary-grid">
      <div class="summary-card">
        <div class="label">К сбору, план</div>
        <div class="value">{{ fmt(data.summary.to_collect_planned) }} ₽</div>
      </div>
      <div class="summary-card">
        <div class="label">Собрано</div>
        <div class="value">{{ fmt(data.summary.collected_fact) }} ₽</div>
      </div>
      <div class="summary-card">
        <div class="label">Остаток</div>
        <div class="value">{{ fmt(data.summary.balance) }} ₽</div>
      </div>
      <div class="summary-card">
        <div class="label">Наценка</div>
        <div class="value">{{ data.event.markup_percent }} %</div>
      </div>
    </div>

    <div class="card">
      <table>
        <thead>
          <tr>
            <th>Роль</th>
            <th>ФИО</th>
            <th class="right">Приёмов пищи</th>
            <th class="center">РАЗНОЕ</th>
            <th class="right">Без наценки</th>
            <th class="right">К оплате</th>
            <th class="right">Оплачено</th>
            <th class="right">Остаток</th>
            <th class="center">Статус</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in data.contributions" :key="row.person_id">
            <td><span class="tag blue">{{ row.role || '—' }}</span></td>
            <td>{{ row.full_name }}</td>
            <td class="right">{{ row.meals_count }}</td>
            <td class="center">
              <span class="tag" :class="row.misc ? 'green' : ''">{{ row.misc ? '✓' : '—' }}</span>
            </td>
            <td class="right">{{ fmt(row.base_amount) }}</td>
            <td class="right"><b>{{ fmt(row.amount) }}</b></td>
            <td class="right">
              <input type="number" :value="row.paid_amount"
                     class="w-sm right"
                     @change="updatePaid(row, $event.target.value)" />
            </td>
            <td class="right" :style="{color: row.balance > 0.5 ? 'var(--red)' : 'var(--green)'}">
              {{ fmt(row.balance) }}
            </td>
            <td class="center">
              <span class="tag" :class="statusClass(row.status)">{{ row.status }}</span>
            </td>
          </tr>
        </tbody>
        <tfoot>
          <tr>
            <th colspan="4">ИТОГО</th>
            <th class="right">{{ fmt(totals.base) }}</th>
            <th class="right">{{ fmt(totals.amount) }}</th>
            <th class="right">{{ fmt(totals.paid) }}</th>
            <th class="right">{{ fmt(totals.balance) }}</th>
            <th></th>
          </tr>
        </tfoot>
      </table>
    </div>
  </template>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../api.js'

const route = useRoute()
const eventId = Number(route.params.id)
const data = ref(null)
const loading = ref(true)
const error = ref('')

function fmt(n) {
  return new Intl.NumberFormat('ru-RU', { maximumFractionDigits: 2 }).format(n || 0)
}

function statusClass(s) {
  if (s === 'Оплачено') return 'green'
  if (s === 'Частично') return 'amber'
  return ''
}

const totals = computed(() => {
  const t = { base: 0, amount: 0, paid: 0, balance: 0 }
  if (!data.value) return t
  for (const r of data.value.contributions) {
    t.base += r.base_amount
    t.amount += r.amount
    t.paid += r.paid_amount
    t.balance += r.balance
  }
  return t
})

async function load() {
  loading.value = true
  try { data.value = await api.getEstimate(eventId) }
  catch (e) { error.value = e.message }
  finally { loading.value = false }
}

async function updatePaid(row, value) {
  const amount = Number(value) || 0
  await api.updatePayment(eventId, row.person_id, amount)
  await load()
}

onMounted(load)
</script>
