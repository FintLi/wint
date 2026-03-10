const fs = require('fs')
const path = require('path')
const config = require('../config')
const { mockState } = require('../../cunzhen-miniapp/data/mock')
const { clone } = require('../../cunzhen-miniapp/utils/format')

function ensureStateFile() {
  const dir = path.dirname(config.stateFile)
  fs.mkdirSync(dir, { recursive: true })
  if (!fs.existsSync(config.stateFile)) {
    fs.writeFileSync(config.stateFile, JSON.stringify(clone(mockState), null, 2))
  }
}

function readState() {
  ensureStateFile()
  return JSON.parse(fs.readFileSync(config.stateFile, 'utf8'))
}

function writeState(state) {
  ensureStateFile()
  fs.writeFileSync(config.stateFile, JSON.stringify(state, null, 2))
}

function resetState() {
  writeState(clone(mockState))
  return readState()
}

module.exports = {
  ensureStateFile,
  readState,
  writeState,
  resetState
}
