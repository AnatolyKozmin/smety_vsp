const BASE = '/api'

async function request(path, opts = {}) {
  const res = await fetch(BASE + path, {
    headers: { 'Content-Type': 'application/json' },
    ...opts,
  })
  if (!res.ok) {
    let detail = ''
    try {
      const text = await res.text()
      try { detail = JSON.parse(text).detail || text } catch { detail = text }
    } catch { /* ignore */ }
    throw new Error(detail || `HTTP ${res.status}`)
  }
  if (res.status === 204) return null
  return res.json()
}

export const api = {
  // products
  listProducts: () => request('/products'),
  createProduct: (data) => request('/products', { method: 'POST', body: JSON.stringify(data) }),
  updateProduct: (id, data) => request(`/products/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteProduct: (id) => request(`/products/${id}`, { method: 'DELETE' }),

  // dishes
  listDishes: () => request('/dishes'),
  getDish: (id) => request(`/dishes/${id}`),
  createDish: (data) => request('/dishes', { method: 'POST', body: JSON.stringify(data) }),
  updateDish: (id, data) => request(`/dishes/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteDish: (id) => request(`/dishes/${id}`, { method: 'DELETE' }),

  // people
  listPeople: () => request('/people'),
  createPerson: (data) => request('/people', { method: 'POST', body: JSON.stringify(data) }),
  updatePerson: (id, data) => request(`/people/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deletePerson: (id) => request(`/people/${id}`, { method: 'DELETE' }),

  // events
  listEvents: () => request('/events'),
  createEvent: (data) => request('/events', { method: 'POST', body: JSON.stringify(data) }),
  updateEvent: (id, data) => request(`/events/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteEvent: (id) => request(`/events/${id}`, { method: 'DELETE' }),
  getEventFull: (id) => request(`/events/${id}/full`),
  getEstimate: (id) => request(`/events/${id}/estimate`),
  getShoppingList: (id) => request(`/events/${id}/shopping-list`),

  // days/meals
  addDay: (eventId, data) => request(`/events/${eventId}/days`, { method: 'POST', body: JSON.stringify(data) }),
  updateDay: (dayId, data) => request(`/events/days/${dayId}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteDay: (dayId) => request(`/events/days/${dayId}`, { method: 'DELETE' }),
  addMeal: (dayId, data) => request(`/events/days/${dayId}/meals`, { method: 'POST', body: JSON.stringify(data) }),
  updateMeal: (mealId, data) => request(`/events/meals/${mealId}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteMeal: (mealId) => request(`/events/meals/${mealId}`, { method: 'DELETE' }),
  setMealParticipants: (mealId, ids) => request(`/events/meals/${mealId}/participants`, {
    method: 'PUT', body: JSON.stringify(ids),
  }),
  setAllGuests: (eventId, n) => request(`/events/${eventId}/set-all-guests?n=${n}`, {
    method: 'PUT',
  }),

  // dishes inside meal
  addDishToMeal: (mealId, data) => request(`/events/meals/${mealId}/dishes`, {
    method: 'POST', body: JSON.stringify(data),
  }),
  addDishFromCatalog: (mealId, dishId) => request(
    `/events/meals/${mealId}/dishes/from-catalog/${dishId}`,
    { method: 'POST' },
  ),
  updateEventDish: (dishId, data) => request(`/events/dishes/${dishId}`, {
    method: 'PUT', body: JSON.stringify(data),
  }),
  deleteEventDish: (dishId) => request(`/events/dishes/${dishId}`, { method: 'DELETE' }),
  toggleTaken: (ingId, taken) => request(
    `/events/ingredients/${ingId}/taken?taken=${taken}`,
    { method: 'PATCH' },
  ),

  // misc
  listMisc: (eventId) => request(`/events/${eventId}/misc`),
  addMisc: (eventId, data) => request(`/events/${eventId}/misc`, {
    method: 'POST', body: JSON.stringify(data),
  }),
  updateMisc: (itemId, data) => request(`/events/misc/${itemId}`, {
    method: 'PUT', body: JSON.stringify(data),
  }),
  deleteMisc: (itemId) => request(`/events/misc/${itemId}`, { method: 'DELETE' }),
  setMiscParticipants: (eventId, ids) => request(`/events/${eventId}/misc/participants`, {
    method: 'PUT', body: JSON.stringify(ids),
  }),

  // payments
  updatePayment: (eventId, personId, amount) => request(`/events/${eventId}/payments`, {
    method: 'PUT', body: JSON.stringify({ person_id: personId, paid_amount: amount }),
  }),

  // event participants ("кто едет")
  getEventParticipants: (eventId) => request(`/events/${eventId}/participants`),
  setEventParticipants: (eventId, ids) => request(`/events/${eventId}/participants`, {
    method: 'PUT', body: JSON.stringify(ids),
  }),

  // guest items
  getGuestItems: (eventId) => request(`/events/${eventId}/guest-items`),
  addGuestProduct: (eventId, data) => request(`/events/${eventId}/guest-products`, {
    method: 'POST', body: JSON.stringify(data),
  }),
  updateGuestProduct: (itemId, data) => request(`/events/guest-products/${itemId}`, {
    method: 'PUT', body: JSON.stringify(data),
  }),
  deleteGuestProduct: (itemId) => request(`/events/guest-products/${itemId}`, { method: 'DELETE' }),
  addGuestDish: (eventId, data) => request(`/events/${eventId}/guest-dishes`, {
    method: 'POST', body: JSON.stringify(data),
  }),
  deleteGuestDish: (itemId) => request(`/events/guest-dishes/${itemId}`, { method: 'DELETE' }),

  // participant items
  getParticipantItems: (eventId) => request(`/events/${eventId}/participant-items`),
  addParticipantProduct: (eventId, personId, data) => request(
    `/events/${eventId}/participants/${personId}/products`,
    { method: 'POST', body: JSON.stringify(data) },
  ),
  updateParticipantProduct: (itemId, data) => request(`/events/participant-products/${itemId}`, {
    method: 'PUT', body: JSON.stringify(data),
  }),
  deleteParticipantProduct: (itemId) => request(`/events/participant-products/${itemId}`, { method: 'DELETE' }),
  addParticipantDish: (eventId, personId, data) => request(
    `/events/${eventId}/participants/${personId}/dishes`,
    { method: 'POST', body: JSON.stringify(data) },
  ),
  deleteParticipantDish: (itemId) => request(`/events/participant-dishes/${itemId}`, { method: 'DELETE' }),
}
