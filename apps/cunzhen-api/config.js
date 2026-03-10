const path = require('path')

module.exports = {
  port: Number(process.env.CUNZHEN_API_PORT || 3010),
  stateFile: process.env.CUNZHEN_STATE_FILE || path.join(__dirname, 'data', 'state.json'),
  adminPassword: process.env.CUNZHEN_ADMIN_PASSWORD || 'cunzhen-admin',
  adminToken: process.env.CUNZHEN_ADMIN_TOKEN || 'cunzhen-admin-token'
}
