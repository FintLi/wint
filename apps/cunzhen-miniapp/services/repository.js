const env = require('./env')
const localStore = require('./store')

const ADMIN_SESSION_KEY = 'cunzhen-miniapp-admin-session'

function bootstrap() {
  if (env.DATA_SOURCE === 'local') {
    localStore.bootstrap()
  }
  return Promise.resolve()
}

function getAdminSessionSync() {
  if (env.DATA_SOURCE === 'local') {
    return localStore.getAdminSession()
  }
  return wx.getStorageSync(ADMIN_SESSION_KEY) || null
}

function saveAdminSession(session) {
  if (env.DATA_SOURCE === 'remote') {
    wx.setStorageSync(ADMIN_SESSION_KEY, session)
  }
}

function clearAdminSession() {
  if (env.DATA_SOURCE === 'remote') {
    wx.removeStorageSync(ADMIN_SESSION_KEY)
  }
}

function request(method, path, data, options) {
  const settings = options || {}
  const session = getAdminSessionSync()
  const headers = Object.assign(
    {
      'Content-Type': 'application/json'
    },
    settings.headers || {}
  )

  if (session && session.token) {
    headers['x-admin-token'] = session.token
  }

  return new Promise(function (resolve, reject) {
    wx.request({
      url: env.API_BASE_URL + path,
      method: method,
      data: data,
      header: headers,
      success(response) {
        if (response.statusCode >= 200 && response.statusCode < 300) {
          resolve(response.data.data)
          return
        }
        reject(new Error((response.data && response.data.error) || '请求失败'))
      },
      fail(error) {
        reject(new Error(error.errMsg || '网络请求失败'))
      }
    })
  })
}

function wrapLocal(fn) {
  return Promise.resolve().then(fn)
}

function getPublishedListings(filters) {
  if (env.DATA_SOURCE === 'remote') {
    const params = buildQuery(filters)
    return request('GET', '/api/listings' + params)
  }
  return wrapLocal(function () {
    return localStore.getPublishedListings(filters)
  })
}

function getAllListings() {
  if (env.DATA_SOURCE === 'remote') {
    return request('GET', '/api/listings/all')
  }
  return wrapLocal(function () {
    return localStore.getAllListings()
  })
}

function getListingById(id) {
  if (env.DATA_SOURCE === 'remote') {
    return request('GET', '/api/listings/' + id)
  }
  return wrapLocal(function () {
    return localStore.getListingById(id)
  })
}

function submitDemandCard(payload) {
  if (env.DATA_SOURCE === 'remote') {
    return request('POST', '/api/leads', payload)
  }
  return wrapLocal(function () {
    return localStore.submitDemandCard(payload)
  })
}

function createViewingAppointment(payload) {
  if (env.DATA_SOURCE === 'remote') {
    return request('POST', '/api/viewings', payload)
  }
  return wrapLocal(function () {
    return localStore.createViewingAppointment(payload)
  })
}

function submitSupplyListing(payload) {
  if (env.DATA_SOURCE === 'remote') {
    return request('POST', '/api/listings/intake', payload)
  }
  return wrapLocal(function () {
    return localStore.submitSupplyListing(payload)
  })
}

function getAdminSummary() {
  if (env.DATA_SOURCE === 'remote') {
    return request('GET', '/api/admin/summary')
  }
  return wrapLocal(function () {
    return localStore.getAdminSummary()
  })
}

function getAdminSession() {
  return wrapLocal(function () {
    return getAdminSessionSync()
  })
}

function loginAdmin(password) {
  if (env.DATA_SOURCE === 'remote') {
    return request('POST', '/api/admin/login', { password: password }).then(function (session) {
      saveAdminSession(session)
      return session
    })
  }
  return wrapLocal(function () {
    return localStore.loginAdmin(password)
  })
}

function logoutAdmin() {
  if (env.DATA_SOURCE === 'remote') {
    clearAdminSession()
    return Promise.resolve()
  }
  return wrapLocal(function () {
    localStore.logoutAdmin()
  })
}

function updateListingStatus(id, payload) {
  if (env.DATA_SOURCE === 'remote') {
    return request('POST', '/api/admin/listings/' + id + '/status', payload)
  }
  return wrapLocal(function () {
    return localStore.updateListingStatus(id, payload)
  })
}

function updateLeadStatus(id, payload) {
  if (env.DATA_SOURCE === 'remote') {
    return request('POST', '/api/admin/leads/' + id + '/status', payload)
  }
  return wrapLocal(function () {
    return localStore.updateLeadStatus(id, payload)
  })
}

function updateViewingStatus(id, payload) {
  if (env.DATA_SOURCE === 'remote') {
    return request('POST', '/api/admin/viewings/' + id + '/status', payload)
  }
  return wrapLocal(function () {
    return localStore.updateViewingStatus(id, payload)
  })
}

function buildQuery(filters) {
  if (!filters) return ''
  const entries = Object.keys(filters).filter(function (key) {
    return filters[key] !== undefined && filters[key] !== null && filters[key] !== ''
  }).map(function (key) {
    return encodeURIComponent(key) + '=' + encodeURIComponent(filters[key])
  })
  return entries.length ? '?' + entries.join('&') : ''
}

module.exports = {
  bootstrap,
  getPublishedListings,
  getAllListings,
  getListingById,
  submitDemandCard,
  createViewingAppointment,
  submitSupplyListing,
  getAdminSummary,
  getAdminSession,
  loginAdmin,
  logoutAdmin,
  updateListingStatus,
  updateLeadStatus,
  updateViewingStatus
}
