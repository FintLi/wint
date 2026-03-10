const http = require('http')
const { URL } = require('url')
const config = require('./config')
const store = require('./lib/store')
const { ensureStateFile } = require('./lib/persistence')

function sendJson(res, statusCode, payload) {
  res.writeHead(statusCode, {
    'Content-Type': 'application/json; charset=utf-8',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, x-admin-token'
  })
  res.end(JSON.stringify(payload))
}

function sendError(res, statusCode, message) {
  sendJson(res, statusCode, { error: message })
}

function parseBody(req) {
  return new Promise(function (resolve, reject) {
    let body = ''
    req.on('data', function (chunk) {
      body += chunk
    })
    req.on('end', function () {
      if (!body) {
        resolve({})
        return
      }
      try {
        resolve(JSON.parse(body))
      } catch (error) {
        reject(error)
      }
    })
    req.on('error', reject)
  })
}

function validateLead(payload) {
  const required = ['name', 'contact', 'budgetMin', 'budgetMax', 'workArea', 'moveInDeadline']
  return required.filter(function (field) {
    return payload[field] === undefined || payload[field] === null || payload[field] === ''
  })
}

function validateViewing(payload) {
  const required = ['listingId', 'leadName', 'contact', 'preferredDate', 'timeSlot']
  return required.filter(function (field) {
    return payload[field] === undefined || payload[field] === null || payload[field] === ''
  })
}

function validateSupply(payload) {
  const required = ['village', 'areaBand', 'roomType', 'monthlyRent', 'depositRule']
  return required.filter(function (field) {
    return payload[field] === undefined || payload[field] === null || payload[field] === ''
  })
}

function requireAdmin(req) {
  const token = req.headers['x-admin-token']
  return token && token === config.adminToken
}

async function handler(req, res) {
  if (req.method === 'OPTIONS') {
    res.writeHead(204, {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, x-admin-token'
    })
    res.end()
    return
  }

  const url = new URL(req.url, 'http://localhost')
  const pathname = url.pathname

  if (req.method === 'GET' && pathname === '/health') {
    sendJson(res, 200, { status: 'ok', service: 'cunzhen-api' })
    return
  }

  if (req.method === 'POST' && pathname === '/api/admin/login') {
    const payload = await parseBody(req)
    if (payload.password !== config.adminPassword) {
      sendError(res, 401, '管理员密码不正确')
      return
    }
    sendJson(res, 200, { data: { username: 'admin', token: config.adminToken, source: 'remote' } })
    return
  }

  if (req.method === 'GET' && pathname === '/api/listings') {
    sendJson(res, 200, { data: store.getPublishedListings(Object.fromEntries(url.searchParams.entries())) })
    return
  }

  if (req.method === 'GET' && pathname === '/api/listings/all') {
    sendJson(res, 200, { data: store.getAllListings() })
    return
  }

  if (req.method === 'GET' && pathname.startsWith('/api/listings/')) {
    const id = pathname.split('/').pop()
    const listing = store.getListingById(id)
    if (!listing) {
      sendError(res, 404, 'Listing not found')
      return
    }
    sendJson(res, 200, { data: listing })
    return
  }

  if (req.method === 'GET' && pathname === '/api/admin/summary') {
    sendJson(res, 200, { data: store.getAdminSummary() })
    return
  }

  if (req.method === 'POST' && pathname === '/api/leads') {
    const payload = await parseBody(req)
    const missing = validateLead(payload)
    if (missing.length) {
      sendError(res, 400, 'Missing lead fields: ' + missing.join(', '))
      return
    }
    sendJson(res, 201, { data: store.submitDemandCard(payload) })
    return
  }

  if (req.method === 'POST' && pathname === '/api/viewings') {
    const payload = await parseBody(req)
    const missing = validateViewing(payload)
    if (missing.length) {
      sendError(res, 400, 'Missing viewing fields: ' + missing.join(', '))
      return
    }
    sendJson(res, 201, { data: store.createViewingAppointment(payload) })
    return
  }

  if (req.method === 'POST' && pathname === '/api/listings/intake') {
    const payload = await parseBody(req)
    const missing = validateSupply(payload)
    if (missing.length) {
      sendError(res, 400, 'Missing supply fields: ' + missing.join(', '))
      return
    }
    sendJson(res, 201, { data: store.submitSupplyListing(payload) })
    return
  }

  if (req.method === 'POST' && pathname === '/api/admin/listings/' + pathname.split('/')[4] + '/status') {
    if (!requireAdmin(req)) {
      sendError(res, 401, '管理员未授权')
      return
    }
    const payload = await parseBody(req)
    const listingId = pathname.split('/')[4]
    const listing = store.updateListingStatus(listingId, payload)
    if (!listing) {
      sendError(res, 404, 'Listing not found')
      return
    }
    sendJson(res, 200, { data: listing })
    return
  }

  if (req.method === 'POST' && pathname === '/api/admin/leads/' + pathname.split('/')[4] + '/status') {
    if (!requireAdmin(req)) {
      sendError(res, 401, '管理员未授权')
      return
    }
    const payload = await parseBody(req)
    const leadId = pathname.split('/')[4]
    const lead = store.updateLeadStatus(leadId, payload)
    if (!lead) {
      sendError(res, 404, 'Lead not found')
      return
    }
    sendJson(res, 200, { data: lead })
    return
  }

  if (req.method === 'POST' && pathname === '/api/admin/viewings/' + pathname.split('/')[4] + '/status') {
    if (!requireAdmin(req)) {
      sendError(res, 401, '管理员未授权')
      return
    }
    const payload = await parseBody(req)
    const viewingId = pathname.split('/')[4]
    const viewing = store.updateViewingStatus(viewingId, payload)
    if (!viewing) {
      sendError(res, 404, 'Viewing not found')
      return
    }
    sendJson(res, 200, { data: viewing })
    return
  }

  if (req.method === 'POST' && pathname === '/api/dev/reset') {
    sendJson(res, 200, { data: store.resetState() })
    return
  }

  sendError(res, 404, 'Route not found')
}

ensureStateFile()

const server = http.createServer(function (req, res) {
  handler(req, res).catch(function (error) {
    sendError(res, 500, error.message || 'Internal Server Error')
  })
})

server.listen(config.port, function () {
  console.log('cunzhen-api listening on port ' + config.port)
})
