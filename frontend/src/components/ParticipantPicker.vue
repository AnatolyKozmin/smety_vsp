<template>
  <div>
    <div class="row" style="margin-bottom:8px">
      <input v-model="filter" placeholder="Поиск по имени/роли" class="w-lg" />
      <button class="secondary small" @click="selectAll">Выбрать всех</button>
      <button class="secondary small" @click="selectNone">Снять</button>
      <span class="muted">Выбрано: {{ localIds.length }}</span>
    </div>

    <div v-for="(roleGroup, role) in grouped" :key="role" class="card" style="padding:8px 12px; margin-bottom:8px">
      <div class="row" style="margin-bottom:4px">
        <b>{{ role || '—' }}</b>
        <button class="secondary small" @click="toggleRole(roleGroup, true)">+ все</button>
        <button class="secondary small" @click="toggleRole(roleGroup, false)">−</button>
      </div>
      <div style="display:grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap:4px">
        <label v-for="p in roleGroup" :key="p.id" class="checkbox">
          <input type="checkbox" :checked="localIds.includes(p.id)" @change="toggle(p.id, $event.target.checked)" />
          {{ p.full_name }}
        </label>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({
  people: { type: Array, default: () => [] },
  selectedIds: { type: Array, default: () => [] },
})
const emit = defineEmits(['update:selectedIds'])

const localIds = ref([...props.selectedIds])
const filter = ref('')

watch(() => props.selectedIds, (v) => { localIds.value = [...v] })
watch(localIds, (v) => emit('update:selectedIds', v), { deep: true })

const filteredPeople = computed(() => {
  const q = filter.value.trim().toLowerCase()
  if (!q) return props.people
  return props.people.filter(p =>
    p.full_name.toLowerCase().includes(q) || (p.role || '').toLowerCase().includes(q)
  )
})

const grouped = computed(() => {
  const map = {}
  for (const p of filteredPeople.value) {
    const r = p.role || ''
    if (!map[r]) map[r] = []
    map[r].push(p)
  }
  return map
})

function toggle(id, checked) {
  const s = new Set(localIds.value)
  if (checked) s.add(id); else s.delete(id)
  localIds.value = [...s]
}

function toggleRole(group, on) {
  const s = new Set(localIds.value)
  for (const p of group) {
    if (on) s.add(p.id); else s.delete(p.id)
  }
  localIds.value = [...s]
}

function selectAll() {
  const s = new Set(localIds.value)
  for (const p of filteredPeople.value) s.add(p.id)
  localIds.value = [...s]
}

function selectNone() {
  const ids = new Set(filteredPeople.value.map(p => p.id))
  localIds.value = localIds.value.filter(id => !ids.has(id))
}
</script>
