<template>
  <div v-if="loading" class="muted">Считаем закупку…</div>
  <div v-else-if="error" class="error">{{ error }}</div>
  <template v-else-if="data">
    <div class="summary-grid">
      <div class="summary-card bark">
        <div class="label">📦 Долгосрочное</div>
        <div class="value">{{ fmt(data.long_total) }} ₽</div>
      </div>
      <div class="summary-card">
        <div class="label">🥬 Краткосрочное</div>
        <div class="value">{{ fmt(data.short_total) }} ₽</div>
      </div>
      <div class="summary-card accent">
        <div class="label">💰 Всего к закупке</div>
        <div class="value">{{ fmt(data.grand_total) }} ₽</div>
      </div>
    </div>

    <h3>📦 Долгосрочное хранение — берём заранее</h3>
    <div class="card" style="padding:0">
      <ShoppingTable :rows="data.long_term" :total="data.long_total" />
    </div>

    <h3 style="margin-top:24px">🥬 Краткосрочное — за 1–2 дня до выезда</h3>
    <div class="card" style="padding:0">
      <ShoppingTable :rows="data.short_term" :total="data.short_total" />
    </div>
  </template>
</template>

<script setup>
import { ref, watch, onMounted, defineComponent, h } from 'vue'
import { api } from '../api.js'

const props = defineProps({
  eventId: { type: Number, required: true },
})

const data = ref(null)
const loading = ref(true)
const error = ref('')

function fmt(n) {
  return new Intl.NumberFormat('ru-RU', { maximumFractionDigits: 2 }).format(n || 0)
}

async function load() {
  loading.value = true
  error.value = ''
  try { data.value = await api.getShoppingList(props.eventId) }
  catch (e) { error.value = e.message }
  finally { loading.value = false }
}

watch(() => props.eventId, load)
onMounted(load)
defineExpose({ reload: load })

const ShoppingTable = defineComponent({
  props: { rows: Array, total: Number },
  setup(props) {
    return () => h('table', [
      h('thead', h('tr', [
        h('th', 'Продукт'),
        h('th', { class: 'right' }, 'Всего г'),
        h('th', { class: 'right' }, 'Г в упак.'),
        h('th', { class: 'right' }, 'Упаковок'),
        h('th', 'Ед.'),
        h('th', { class: 'right' }, '₽ / упак.'),
        h('th', { class: 'right' }, 'Сумма'),
      ])),
      h('tbody', [
        ...props.rows.map(r => h('tr', { key: r.product_id }, [
          h('td', [
            r.product_link
              ? h('a', { href: r.product_link, target: '_blank' }, r.product_name)
              : r.product_name,
          ]),
          h('td', { class: 'right' }, r.total_grams ? fmt(r.total_grams) : '—'),
          h('td', { class: 'right' }, r.grams_in_package || '—'),
          h('td', { class: 'right' }, h('b', String(r.packages_needed))),
          h('td', r.unit),
          h('td', { class: 'right' }, r.price_per_unit ? fmt(r.price_per_unit) + ' ₽' : '—'),
          h('td', { class: 'right' }, fmt(r.total_price) + ' ₽'),
        ])),
        props.rows.length === 0
          ? h('tr', h('td', { colspan: 7, class: 'muted center' }, 'Ничего не нужно'))
          : null,
      ]),
      h('tfoot', h('tr', [
        h('th', { colspan: 6, class: 'right' }, 'ИТОГО'),
        h('th', { class: 'right' }, fmt(props.total) + ' ₽'),
      ])),
    ])
  },
})
</script>

<style>
@media print {
  .sidebar, .toolbar button, .tabs { display: none !important; }
  .main { padding: 0; }
  body { background: #fff; }
  .summary-card { box-shadow: none; }
}
</style>
