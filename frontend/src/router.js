import { createRouter, createWebHashHistory } from 'vue-router'
import EventsView from './views/EventsView.vue'
import EventEditor from './views/EventEditor.vue'
import EstimateView from './views/EstimateView.vue'
import ContributionsView from './views/ContributionsView.vue'
import MenuView from './views/MenuView.vue'
import DishesView from './views/DishesView.vue'
import PeopleView from './views/PeopleView.vue'
import ProductsView from './views/ProductsView.vue'
import ShoppingListView from './views/ShoppingListView.vue'
import ShoppingHubView from './views/ShoppingHubView.vue'
import GuestsHubView from './views/GuestsHubView.vue'

export const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: '/', redirect: '/events' },
    { path: '/events', component: EventsView },
    { path: '/events/:id/edit', component: EventEditor, props: true },
    { path: '/events/:id/estimate', component: EstimateView, props: true },
    { path: '/events/:id/contributions', component: ContributionsView, props: true },
    { path: '/events/:id/shopping', component: ShoppingListView, props: true },
    { path: '/shopping', component: ShoppingHubView },
    { path: '/shopping/:id', component: ShoppingHubView, props: true },
    { path: '/products', component: ProductsView },
    { path: '/menu', component: MenuView },
    { path: '/menu/:id', component: MenuView, props: true },
    { path: '/dishes', component: DishesView },
    { path: '/people', component: PeopleView },
    { path: '/guests', component: GuestsHubView },
    { path: '/guests/:id', component: GuestsHubView, props: true },
  ],
})
