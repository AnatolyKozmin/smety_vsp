<template>
  <div class="combo" ref="root">
    <input
      :value="display"
      @focus="open = true"
      @input="onType($event.target.value)"
      @keydown.down.prevent="move(1)"
      @keydown.up.prevent="move(-1)"
      @keydown.enter.prevent="pick(filtered[active])"
      @keydown.esc="open = false"
      :placeholder="placeholder"
      :class="inputClass"
    />
    <div v-if="open && filtered.length" class="dropdown">
      <div
        v-for="(p, i) in filtered" :key="p.id"
        class="opt"
        :class="{ active: i === active }"
        @mousedown.prevent="pick(p)"
        @mouseenter="active = i"
      >
        {{ p.name }} <span class="hint">{{ p.unit }} · {{ p.storage_term }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'

const props = defineProps({
  products: { type: Array, default: () => [] },
  modelValue: { type: [Number, null], default: null },
  placeholder: { type: String, default: 'Выберите продукт' },
  inputClass: { type: String, default: '' },
})
const emit = defineEmits(['update:modelValue', 'selected'])

const open = ref(false)
const query = ref('')
const active = ref(0)
const root = ref(null)

const selected = computed(() => props.products.find(p => p.id === props.modelValue) || null)
const display = computed(() => {
  if (open.value) return query.value
  return selected.value ? selected.value.name : ''
})

const filtered = computed(() => {
  const q = query.value.trim().toLowerCase()
  if (!q) return props.products.slice(0, 50)
  return props.products.filter(p => p.name.toLowerCase().includes(q)).slice(0, 50)
})

watch(() => props.modelValue, () => { query.value = '' })

function onType(v) {
  query.value = v
  active.value = 0
  open.value = true
}

function move(delta) {
  if (!filtered.value.length) return
  active.value = (active.value + delta + filtered.value.length) % filtered.value.length
}

function pick(p) {
  if (!p) return
  emit('update:modelValue', p.id)
  emit('selected', p)
  open.value = false
  query.value = ''
}

function onDocClick(e) {
  if (root.value && !root.value.contains(e.target)) open.value = false
}
onMounted(() => document.addEventListener('mousedown', onDocClick))
onBeforeUnmount(() => document.removeEventListener('mousedown', onDocClick))
</script>
