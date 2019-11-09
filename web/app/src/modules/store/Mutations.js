'use strict'

import _ from 'lodash'

import State from './State'

const findCollectionByKey = (state, key) => {
  if (!_.hasIn(state, key)) {
    throw new Error('findCollectionByKey state does not have:' + key)
  }

  let collection = _.get(state, key)

  if (!_.isArray(collection)) {
    throw new Error('findCollectionByKey not found:' + key)
  }

  return collection
}

const addOrUpdateEntityToCollection = (collection, { entity, uid = null, primaryKey = 'Id', addMissing = true }) => {
  if (!uid && entity[primaryKey]) {
    uid = entity[primaryKey]
  }
  else if (!uid) {
    collection.push(entity)
    return
  }

  let index = _.findIndex(collection, [primaryKey, uid])

  if (index > -1) {
    collection.splice(index, 1, entity)
  }
  else if (addMissing) {
    collection.push(entity)
  }
}

export default {
  SET(state, { key, value }) {
    _.set(state, key, value)
  },

  NULL(state, { key }) {
    _.set(state, key, null)
  },

  COLLECTION_UPDATE(state, { key, entity, uid = null, primaryKey = 'Id', addMissing = true }) {
    let collection = findCollectionByKey(state, key)

    addOrUpdateEntityToCollection(collection, {
      entity,
      uid,
      primaryKey,
      addMissing
    })
  },

  COLLECTION_LOAD(state, { key, items = [], primaryKey = 'Id'}) {
    let collection = findCollectionByKey(state, key)

    _.each(items, entity => {
      addOrUpdateEntityToCollection(collection, {
        entity,
        primaryKey,
      })
    })
  },

  COLLECTION_REMOVE(state, { key, uid, primaryKey = 'Id' }) {
    let collection = findCollectionByKey(state, key)
    let index = _.findIndex(collection, [primaryKey, uid])

    if (index > -1) {
      collection.splice(index, 1)
    }
  },

  DEFAULT_STATE_RESET(state) {
    let cleanState = JSON.parse(JSON.stringify(State))

    _.each(cleanState, (value, key) => {
      _.set(state, key, value)
    })
  }
}
