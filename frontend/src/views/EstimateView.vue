<template>
  <div v-if="loading" class="muted">Расчёт…</div>
  <div v-else-if="error" class="error">{{ error }}</div>
  <template v-else-if="data">
    <div class="toolbar">
      <h2 style="margin:0">📊 Смета: {{ data.event.name }}</h2>
      <div class="row">
        <router-link :to="`/events/${eventId}/edit`"><button class="secondary">Редактор</button></router-link>
        <router-link :to="`/events/${eventId}/shopping`"><button class="secondary">🛒 Список покупок</button></router-link>
        <router-link :to="`/events/${eventId}/contributions`"><button class="secondary">💰 Взносы</button></router-link>
        <router-link to="/events"><button class="ghost">← К списку</button></router-link>
      </div>
    </div>

    <div class="summary-grid">
      <div class="summary-card">
        <div class="label">Еда (без наценки)</div>
        <div class="value">{{ fmt(data.food_total) }} ₽</div>
      </div>
      <div class="summary-card">
        <div class="label">Прочее</div>
        <div class="value">{{ fmt(data.misc_total) }} ₽</div>
      </div>
      <div class="summary-card">
        <div class="label">Итого без наценки</div>
        <div class="value">{{ fmt(data.base_total) }} ₽</div>
      </div>
      <div class="summary-card accent">
        <div class="label">С наценкой {{ data.event.markup_percent }} %</div>
        <div class="value">{{ fmt(data.total_with_markup) }} ₽</div>
      </div>
      <div class="summary-card">
        <div class="label">Собрать (план)</div>
        <div class="value">{{ fmt(data.summary.to_collect_planned) }} ₽</div>
      </div>
      <div class="summary-card">
        <div class="label">Собрано (факт)</div>
        <div class="value">{{ fmt(data.summary.collected_fact) }} ₽</div>
      </div>
      <div class="summary-card bark">
        <div class="label">Остаток к сбору</div>
        <div class="value">{{ fmt(data.summary.balance) }} ₽</div>
      </div>
    </div>

    <h3>📅 Меню по дням</h3>
    <div v-for="d in data.days" :key="d.id" class="card day-card">
      <div class="toolbar" style="margin:0">
        <div>
          <h3 style="margin:0">{{ d.name }} <span v-if="d.short_name" class="tag">{{ d.short_name }}</span></h3>
        </div>
        <div class="tag green">{{ fmt(d.total_price) }} ₽</div>
      </div>

      <div v-for="m in d.meals" :key="m.id" class="meal-block">
        <div class="meal-header">
          <h4 style="margin:0; text-transform:none; color:var(--green-900); font-size:14px">
            {{ m.name }} <span class="muted">— {{ m.portions }} порций</span>
          </h4>
          <div class="tag amber">{{ fmt(m.total_price) }} ₽</div>
        </div>

        <div v-for="dsh in m.dishes" :key="dsh.id" class="dish-block">
          <div class="toolbar" style="margin:0 0 6px 0">
            <div class="dish-name">{{ dsh.name }}</div>
            <div class="muted">{{ fmt(dsh.total_price) }} ₽</div>
          </div>
          <table>
            <thead>
              <tr>
                <th>Продукт</th>
                <th class="right">г/порция</th>
                <th class="right">Всего</th>
                <th>Ед.</th>
                <th class="right">Г в упак.</th>
                <th class="right">Цена/уп</th>
                <th class="right">Упаковок</th>
                <th class="right">Итог</th>
                <th class="center">Взяли?</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="ing in dsh.ingredients" :key="ing.id">
                <td>
                  <a v-if="ing.product_link" :href="ing.product_link" target="_blank">{{ ing.product_name }}</a>
                  <span v-else>{{ ing.product_name }}</span>
                  <span v-if="ing.storage_term" class="tag" :class="termClass(ing.storage_term)" style="margin-left:6px">
                    {{ ing.storage_term[0] }}
                  </span>
                </td>
                <td class="right">{{ ing.grams_per_portion }}</td>
                <td class="right">{{ fmtGrams(ing.total_grams) }}</td>
                <td>{{ ing.unit }}</td>
                <td class="right">{{ ing.grams_in_package || '—' }}</td>
                <td class="right">{{ ing.price_per_unit }} ₽</td>
                <td class="right"><b>{{ ing.packages_needed }}</b></td>
                <td class="right">{{ fmt(ing.total_price) }} ₽</td>
                <td class="center">
                  <input type="checkbox" :checked="ing.taken" @change="toggle(ing, $event.target.checked)" />
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-if="m.dishes.length === 0" class="muted">Блюд нет.</div>
      </div>
      <div v-if="d.meals.length === 0" class="muted">Приёмов пищи нет.</div>
    </div>

    <h3 style="margin-top:24px">🧂 Прочее <span class="tag amber">{{ fmt(data.misc_total) }} ₽</span></h3>
    <div class="card">
      <div class="muted" style="margin-bottom:8px">
        Скидываются: {{ data.misc_participant_ids.length }} чел.,
        по {{ fmt(data.per_person_misc) }} ₽ / чел.
      </div>
      <table>
        <thead>
          <tr>
            <th>Продукт</th>
            <th class="right">Кол-во</th>
            <th>Ед.</th>
            <th>Срок</th>
            <th class="right">₽ за уп.</th>
            <th class="right">Итог</th>
            <th class="center">Взяли?</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="i in data.misc" :key="i.id">
            <td>{{ i.product_name }}</td>
            <td class="right">{{ i.quantity }}</td>
            <td>{{ i.unit }}</td>
            <td><span class="tag" :class="termClass(i.storage_term)">{{ i.storage_term }}</span></td>
            <td class="right">{{ i.price_per_unit }} ₽</td>
            <td class="right">{{ fmt(i.total_price) }} ₽</td>
            <td class="center"><span class="tag" :class="i.taken ? 'green' : ''">{{ i.taken ? '✓' : '—' }}</span></td>
          </tr>
          <tr v-if="!data.misc.length">
            <td colspan="7" class="muted center">Ничего не добавлено.</td>
          </tr>
        </tbody>
      </table>
    </div>
  </template>
</template>

<script setup>
import { ref, onMounted } from 'vue'
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
function fmtGrams(g) {
  if (!g) return '—'
  if (g >= 1000) return (g / 1000).toFixed(2).replace(/\.?0+$/, '') + ' кг'
  return g + ' г'
}
function termClass(t) {
  if (!t) return ''
  return t.toLowerCase().startsWith('кратк') ? 'amber' : 'green'
}

async function load() {
  loading.value = true
  try { data.value = await api.getEstimate(eventId) }
  catch (e) { error.value = e.message }
  finally { loading.value = false }
}

async function toggle(ing, val) {
  await api.toggleTaken(ing.id, val)
  ing.taken = val
}

onMounted(load)
</script>
