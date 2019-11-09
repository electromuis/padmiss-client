'use strict'

import _ from 'lodash'

import packageJson from '../../package.json'

let commonConfig = {
  apiBaseUrl: 'https://localhost/replace/this/with/env/config',
  version: packageJson.version,
  debug: {
    vue: false,
  },
}

const mergeConfigs = (envConfig) => {
  return _.merge({}, commonConfig, envConfig)
}

export default mergeConfigs
