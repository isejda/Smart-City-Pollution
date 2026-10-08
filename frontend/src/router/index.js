import { createRouter, createWebHashHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const PublicPortal = () => import('../views/public/PublicPortal.vue')
const MonitorPortal = () => import('../views/monitor/MonitorPortal.vue')
const RegisterView = () => import('../views/RegisterView.vue')

const routes = [
  { path: '/', name: 'public', component: PublicPortal, meta: { title: 'Portali publik' } },
  {
    path: '/monitorimi',
    name: 'monitor',
    component: MonitorPortal,
    meta: { title: 'Portali i Monitorimit', requiresAuth: true },
  },
  { path: '/regjistrimi', name: 'register', component: RegisterView, meta: { title: 'Regjistrimi' } },
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

const router = createRouter({
  // hash history keeps the app deployable as a static bundle on any host
  history: createWebHashHistory(),
  routes,
  scrollBehavior(to) {
    if (to.hash) return { el: to.hash, top: 74 }
    return { top: 0 }
  },
})

router.beforeEach((to) => {
  const auth = useAuthStore()
  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    return { path: '/', query: { staff: '1' } }
  }
})

router.afterEach((to) => {
  const base = 'Smart City Pollution'
  document.title = to.meta && to.meta.title ? `${base} - ${to.meta.title}` : base
})

export default router
