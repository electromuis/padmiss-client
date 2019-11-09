'use strict'

import Vue from 'vue'
Vue.config.devtools = true

import Vuex from 'vuex'
Vue.use(Vuex)

import State from './store/State'
import Actions from './store/Actions'
import Mutations from './store/Mutations'

export default new Vuex.Store({
  strict: false,
  state: JSON.parse(JSON.stringify(State)),
  actions: Actions,
  mutations: Mutations,
})
