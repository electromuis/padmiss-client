'use strict'

import Vue from 'vue'
import VueRouter from 'vue-router'
import { sync } from 'vuex-router-sync'

import store from './Store'

Vue.use(VueRouter)

import Home from '../components/Home.vue'
import Login from 'padmiss-client/src/components/Login.vue'
import Recover from 'padmiss-client/src/components/Login/Recover.vue'
import ChangeRecover from 'padmiss-client/src/components/Login/Recover/Change.vue'

const routes = [
  {
    path: '/',
    component: Home,
    name: 'home',
    meta: {
      title: 'Home',
      public: true,
    },
  },
  {
    path: '/login',
    component: Login,
    name: 'login',
    meta: {
      title: 'Login',
      public: true,
    },
  },
  {
    path: '/login/recover',
    component: Recover,
    name: 'login-recover',
    meta: {
      paren: 'login',
      title: 'Recover',
      public: true,
    },
  },
  {
    path: '/forgot-password/receive-new-password/:userId/:token',
    component: ChangeRecover,
    name: 'login-recover-change',
    meta: {
      paren: 'login-recover',
      title: 'Recover',
      public: true,
    },
  },
]

const router = new VueRouter({
  routes,
  linkActiveClass: 'active',
})
router.beforeEach((to, from, next) => {
  if (to.meta && to.meta.title) {
    document.title = to.meta.title + ' - EC2019'
  }
  next()
})
sync(store, router)

export default router
