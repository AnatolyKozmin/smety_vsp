<template>
  <div class="app-shell">
    <aside class="sidebar">
      <div class="brand">
        <div class="logo">🌲</div>
        <div>
          <div class="title">Вспышка'26</div>
          <div class="subtitle">Сметы и закупки</div>
        </div>
      </div>
      <router-link to="/events"><span class="icon">🏕️</span> Забросы</router-link>
      <router-link to="/menu"><span class="icon">🍲</span> Меню</router-link>
      <router-link to="/shopping"><span class="icon">🛒</span> Что купить</router-link>
      <router-link to="/dishes"><span class="icon">📖</span> База блюд</router-link>
      <router-link to="/products"><span class="icon">🥕</span> Продукты</router-link>
      <router-link to="/people"><span class="icon">🧑‍🤝‍🧑</span> Участники</router-link>
      <div class="footer-note">🍃 v0.2 · 2026</div>
    </aside>
    <main class="main">
      <router-view />
    </main>
  </div>
</template>
