const { mockState } = require('../data/mock')
const { clone } = require('../utils/format')
const { deriveListingState, applyFilters } = require('../utils/listing')

const STORAGE_KEY = 'cunzhen-miniapp-state'
const ADMIN_SESSION_KEY = 'cunzhen-miniapp-admin-session'
const LOCAL_ADMIN_PASSWORD = 'cunzhen-admin'

function bootstrap() {
  const existing = wx.getStorageSync(STORAGE_KEY)
  if (!existing || !existing.listings) {
    wx.setStorageSync(STORAGE_KEY, clone(mockState))
  }
}

function getState() {
  bootstrap()
  return wx.getStorageSync(STORAGE_KEY)
}

function saveState(state) {
  wx.setStorageSync(STORAGE_KEY, state)
}

function getPublishedListings(filters) {
  const state = getState()
  const listings = state.listings.map(deriveListingState).filter(function (listing) {
    return listing.frontendVisible
  })
  return applyFilters(listings, filters || {})
}

function getAllListings() {
  return getState().listings.map(deriveListingState)
}

function getListingById(id) {
  const listing = getState().listings.find(function (item) {
    return item.id === id
  })
  return listing ? deriveListingState(listing) : null
}

function inferPriority(moveInDeadline) {
  const now = Date.now()
  const target = new Date(moveInDeadline).getTime()
  if (Number.isNaN(target)) return 'C'
  const days = (target - now) / (1000 * 60 * 60 * 24)
  if (days <= 7) return 'A'
  if (days <= 21) return 'B'
  return 'C'
}

function createLeadId(leads) {
  return 'Q-' + String(leads.length + 1).padStart(3, '0')
}

function createViewingId(viewings) {
  return 'A-' + String(viewings.length + 1).padStart(3, '0')
}

function createListingId(listings) {
  return 'L-' + String(listings.length + 1).padStart(3, '0')
}

function submitDemandCard(payload) {
  const state = getState()
  const lead = {
    id: createLeadId(state.leads),
    createdAt: new Date().toISOString(),
    name: payload.name,
    contact: payload.contact,
    budgetMin: Number(payload.budgetMin),
    budgetMax: Number(payload.budgetMax),
    workArea: payload.workArea,
    commutePreference: payload.commutePreference,
    roomPreference: payload.roomPreference,
    moveInDeadline: payload.moveInDeadline,
    sourceChannel: payload.sourceChannel || '小程序求租卡',
    status: '新线索',
    priority: inferPriority(payload.moveInDeadline),
    notes: payload.notes || ''
  }
  state.leads.unshift(lead)
  saveState(state)
  return lead
}

function createViewingAppointment(payload) {
  const state = getState()
  const viewing = {
    id: createViewingId(state.viewings),
    listingId: payload.listingId,
    listingTitle: payload.listingTitle,
    leadName: payload.leadName,
    contact: payload.contact,
    preferredDate: payload.preferredDate,
    timeSlot: payload.timeSlot,
    status: '待确认',
    notes: payload.notes || ''
  }
  state.viewings.unshift(viewing)

  state.listings = state.listings.map(function (listing) {
    if (listing.id === payload.listingId && listing.status === '可发布') {
      return Object.assign({}, listing, { status: '已预约' })
    }
    return listing
  })

  saveState(state)
  return viewing
}

function submitSupplyListing(payload) {
  const state = getState()
  const listing = {
    id: createListingId(state.listings),
    title: payload.title || payload.areaBand + payload.roomType + '待核验房源',
    village: payload.village,
    areaBand: payload.areaBand,
    roomType: payload.roomType,
    monthlyRent: Number(payload.monthlyRent),
    depositRule: payload.depositRule,
    utilityRule: payload.utilityRule,
    floorLabel: payload.floorLabel,
    sunlight: payload.sunlight,
    elevator: payload.elevator,
    furnitureAppliances: payload.furnitureAppliances,
    moveInDate: payload.moveInDate,
    lastVerifiedAt: payload.lastVerifiedAt,
    videoUrl: payload.videoUrl,
    sourceRole: payload.sourceRole,
    sourceChannel: '小程序邀约录入',
    status: '待核验',
    authFlag: payload.authFlag || '待认证',
    safetyTags: payload.safetyTags || [],
    commuteTags: payload.commuteTags || [],
    notes: payload.notes || '',
    versions: [
      {
        version: '0.9',
        monthlyRent: Number(payload.monthlyRent),
        moveInDate: payload.moveInDate,
        contactSnapshot: payload.contact || '',
        utilityRule: payload.utilityRule,
        updatedAt: new Date().toISOString()
      }
    ]
  }
  state.listings.unshift(listing)
  saveState(state)
  return deriveListingState(listing)
}

function getAdminSession() {
  return wx.getStorageSync(ADMIN_SESSION_KEY) || null
}

function loginAdmin(password) {
  if (password !== LOCAL_ADMIN_PASSWORD) {
    throw new Error('管理员密码不正确')
  }
  const session = {
    username: 'admin',
    token: 'local-admin-token',
    source: 'local'
  }
  wx.setStorageSync(ADMIN_SESSION_KEY, session)
  return session
}

function logoutAdmin() {
  wx.removeStorageSync(ADMIN_SESSION_KEY)
}

function updateListingStatus(id, payload) {
  const state = getState()
  let updated = null
  state.listings = state.listings.map(function (listing) {
    if (listing.id !== id) return listing
    const next = Object.assign({}, listing)
    if (payload.status) next.status = payload.status
    if (payload.authFlag) next.authFlag = payload.authFlag
    if (payload.lastVerifiedAt) next.lastVerifiedAt = payload.lastVerifiedAt
    if (payload.notes) next.notes = payload.notes

    if (payload.lastVerifiedAt || payload.authFlag) {
      const versions = (next.versions || []).slice()
      versions.push({
        version: String(versions.length + 1) + '.0',
        monthlyRent: next.monthlyRent,
        moveInDate: next.moveInDate,
        contactSnapshot: (versions[versions.length - 1] && versions[versions.length - 1].contactSnapshot) || '',
        utilityRule: next.utilityRule,
        updatedAt: new Date().toISOString()
      })
      next.versions = versions
    }
    updated = next
    return next
  })
  saveState(state)
  return updated ? deriveListingState(updated) : null
}

function updateLeadStatus(id, payload) {
  const state = getState()
  let updated = null
  state.leads = state.leads.map(function (lead) {
    if (lead.id !== id) return lead
    const next = Object.assign({}, lead)
    if (payload.status) next.status = payload.status
    if (payload.notes) next.notes = payload.notes
    updated = next
    return next
  })
  saveState(state)
  return updated
}

function updateViewingStatus(id, payload) {
  const state = getState()
  let updated = null
  state.viewings = state.viewings.map(function (viewing) {
    if (viewing.id !== id) return viewing
    const next = Object.assign({}, viewing)
    if (payload.status) next.status = payload.status
    if (payload.notes) next.notes = payload.notes
    if (payload.noShowReason) next.noShowReason = payload.noShowReason
    updated = next
    return next
  })

  if (updated) {
    if (updated.status === '已完成') {
      state.leads = state.leads.map(function (lead) {
        if (lead.contact === updated.contact && lead.status !== '已成交') {
          return Object.assign({}, lead, { status: '已带看' })
        }
        return lead
      })
    }
    if (updated.status === '爽约') {
      state.listings = state.listings.map(function (listing) {
        if (listing.id === updated.listingId && listing.status === '已预约') {
          return Object.assign({}, listing, { status: '可发布' })
        }
        return listing
      })
    }
  }

  saveState(state)
  return updated
}

function getAdminSummary() {
  const state = getState()
  const listings = state.listings.map(deriveListingState)
  const publishableCount = listings.filter(function (item) {
    return item.frontendVisible
  }).length
  const expiredCount = listings.filter(function (item) {
    return item.expired
  }).length
  const pendingReviewCount = listings.filter(function (item) {
    return item.status === '待核验'
  }).length
  const leadStatusCount = countBy(state.leads, 'status')
  const viewingStatusCount = countBy(state.viewings, 'status')
  return {
    publishableCount,
    expiredCount,
    pendingReviewCount,
    leadStatusCount,
    viewingStatusCount,
    latestListings: listings.slice(0, 6),
    latestLeads: state.leads.slice(0, 6),
    latestViewings: state.viewings.slice(0, 6),
    riskyListings: listings.filter(function (item) {
      return item.expired || !item.publishable
    }).slice(0, 6)
  }
}

function countBy(items, key) {
  return items.reduce(function (acc, item) {
    const bucket = item[key] || '未知'
    acc[bucket] = (acc[bucket] || 0) + 1
    return acc
  }, {})
}

module.exports = {
  bootstrap,
  getPublishedListings,
  getAllListings,
  getListingById,
  submitDemandCard,
  createViewingAppointment,
  submitSupplyListing,
  getAdminSession,
  loginAdmin,
  logoutAdmin,
  updateListingStatus,
  updateLeadStatus,
  updateViewingStatus,
  getAdminSummary
}
