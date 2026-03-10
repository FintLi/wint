const STORAGE_KEY = 'cunzhen-miniapp-inline-state'
const ADMIN_SESSION_KEY = 'cunzhen-miniapp-inline-admin-session'
const EXPIRY_HOURS = 72

const constants = {
  LEAD_STATUSES: ['新线索', '已联系', '已匹配', '已带看', '已成交', '流失'],
  VIEWING_STATUSES: ['待确认', '已确认', '已完成', '爽约'],
  AREA_BANDS: ['全部', '西乡', '固戍', '后瑞', '福永'],
  ROOM_TYPES: ['全部', '单间', '合租', '一房'],
  ELEVATOR_OPTIONS: ['全部', '有', '无'],
  BUDGET_OPTIONS: ['全部', '1000以下', '1000-1500', '1500-2000', '2000-2500'],
  COMMUTE_OPTIONS: ['30 分钟内', '45 分钟内', '60 分钟内'],
  TIME_SLOTS: ['周三 19:30-22:00', '周六 14:00-18:00', '自定义沟通']
}

function pad(value) {
  return value < 10 ? '0' + value : '' + value
}

function formatCurrency(value) {
  if (value === null || value === undefined || value === '') return '--'
  return '¥' + value + '/月'
}

function formatDate(dateLike) {
  if (!dateLike) return '--'
  const date = new Date(dateLike)
  if (Number.isNaN(date.getTime())) return '--'
  return [date.getFullYear(), pad(date.getMonth() + 1), pad(date.getDate())].join('-')
}

function formatVersionTag(version) {
  if (!version) return 'v1'
  return 'v' + version
}

function clone(data) {
  return JSON.parse(JSON.stringify(data))
}

function hoursAgo(hourCount) {
  return new Date(Date.now() - hourCount * 60 * 60 * 1000).toISOString()
}

function daysLater(dayCount) {
  return new Date(Date.now() + dayCount * 24 * 60 * 60 * 1000).toISOString().slice(0, 10)
}

function hoursSince(dateLike) {
  if (!dateLike) return Number.POSITIVE_INFINITY
  const time = new Date(dateLike).getTime()
  if (Number.isNaN(time)) return Number.POSITIVE_INFINITY
  return (Date.now() - time) / (1000 * 60 * 60)
}

function hasValue(value) {
  return !(value === undefined || value === null || value === '')
}

function buildInitialState() {
  return {
    listings: [
      {
        id: 'L-001',
        title: '西乡坪洲地铁 12 分钟实拍单间',
        village: '西乡盐田村',
        areaBand: '西乡',
        roomType: '单间',
        monthlyRent: 1380,
        depositRule: '押一付一',
        utilityRule: '水 8 电 1.5，卫生费 30',
        floorLabel: '4 楼',
        sunlight: '朝南，白天采光稳定',
        elevator: '无',
        furnitureAppliances: '床、空调、热水器、洗衣机',
        moveInDate: daysLater(2),
        lastVerifiedAt: hoursAgo(6),
        videoUrl: 'https://example.com/video/L-001',
        sourceRole: '合作拍房员',
        sourceChannel: '实拍采集',
        status: '可发布',
        authFlag: '已认证',
        safetyTags: ['巷口亮', '夜归可走主路', '楼道整洁'],
        commuteTags: ['坪洲通勤友好', '适合宝体/前海方向'],
        notes: '适合预算 1500 内、偏好独立空间的租客。',
        versions: [
          {
            version: '1.0',
            monthlyRent: 1380,
            moveInDate: daysLater(2),
            contactSnapshot: 'wx-xixiang-001',
            utilityRule: '水 8 电 1.5，卫生费 30',
            updatedAt: hoursAgo(6)
          }
        ]
      },
      {
        id: 'L-002',
        title: '福永白石厦电梯一房',
        village: '福永白石厦',
        areaBand: '福永',
        roomType: '一房',
        monthlyRent: 2280,
        depositRule: '押二付一',
        utilityRule: '民水民电，管理费 80',
        floorLabel: '9 楼',
        sunlight: '东南向，通风不错',
        elevator: '有',
        furnitureAppliances: '床、空调、冰箱、洗衣机、衣柜',
        moveInDate: daysLater(5),
        lastVerifiedAt: hoursAgo(18),
        videoUrl: 'https://example.com/video/L-002',
        sourceRole: '合作中介',
        sourceChannel: '合作中介录入',
        status: '可发布',
        authFlag: '已认证',
        safetyTags: ['楼下便利店', '主路近', '女生可看'],
        commuteTags: ['机场东通勤友好', '福永地铁接驳'],
        notes: '适合情侣或希望独立起居的一房需求。',
        versions: [
          {
            version: '1.0',
            monthlyRent: 2280,
            moveInDate: daysLater(5),
            contactSnapshot: 'wx-fuyong-002',
            utilityRule: '民水民电，管理费 80',
            updatedAt: hoursAgo(18)
          }
        ]
      },
      {
        id: 'L-003',
        title: '固戍地铁步行 10 分钟合租次卧',
        village: '固戍下围园',
        areaBand: '固戍',
        roomType: '合租',
        monthlyRent: 1180,
        depositRule: '押一付一',
        utilityRule: '水电均摊，网费已含',
        floorLabel: '6 楼',
        sunlight: '窗大，下午偏亮',
        elevator: '无',
        furnitureAppliances: '床、空调、书桌、热水器',
        moveInDate: daysLater(1),
        lastVerifiedAt: hoursAgo(30),
        videoUrl: 'https://example.com/video/L-003',
        sourceRole: '二房东',
        sourceChannel: '邀约录入',
        status: '可发布',
        authFlag: '待认证',
        safetyTags: ['巷道较宽', '快递方便'],
        commuteTags: ['固戍通勤友好'],
        notes: '合租室友作息正常，接受轻煮食。',
        versions: [
          {
            version: '1.0',
            monthlyRent: 1180,
            moveInDate: daysLater(1),
            contactSnapshot: 'wx-gushu-003',
            utilityRule: '水电均摊，网费已含',
            updatedAt: hoursAgo(30)
          }
        ]
      }
    ],
    leads: [
      {
        id: 'Q-001',
        createdAt: hoursAgo(4),
        name: '阿杰',
        contact: 'wechat-ajie',
        budgetMin: 1000,
        budgetMax: 1600,
        workArea: '坪洲地铁站',
        commutePreference: '45 分钟内',
        roomPreference: '单间',
        moveInDeadline: daysLater(4),
        sourceChannel: '短视频评论区',
        status: '新线索',
        priority: 'A',
        notes: '希望夜归安全。'
      }
    ],
    viewings: [
      {
        id: 'A-001',
        listingId: 'L-001',
        listingTitle: '西乡坪洲地铁 12 分钟实拍单间',
        leadName: '小林',
        contact: 'wechat-xiaolin',
        preferredDate: daysLater(1),
        timeSlot: '周三 19:30-22:00',
        status: '待确认',
        notes: '希望同场再看两套。'
      }
    ]
  }
}

function getState() {
  const cached = wx.getStorageSync(STORAGE_KEY)
  if (cached && cached.listings) {
    return cached
  }
  const initialState = buildInitialState()
  wx.setStorageSync(STORAGE_KEY, clone(initialState))
  return initialState
}

function saveState(state) {
  wx.setStorageSync(STORAGE_KEY, state)
}

function isListingPublishable(listing) {
  return ['monthlyRent', 'utilityRule', 'lastVerifiedAt', 'videoUrl'].every(function (field) {
    return hasValue(listing[field])
  })
}

function isListingExpired(listing) {
  return hoursSince(listing.lastVerifiedAt) > EXPIRY_HOURS
}

function deriveListingState(listing) {
  const publishable = isListingPublishable(listing)
  const expired = isListingExpired(listing)
  const next = Object.assign({}, listing)
  next.publishable = publishable
  next.expired = expired
  next.frontendVisible = publishable && !expired && listing.status === '可发布'
  next.verificationLabel = expired ? '已超 72 小时，需复核' : '72 小时内已核验'
  return next
}

function fitsBudget(rent, budgetLabel) {
  if (!budgetLabel || budgetLabel === '全部') return true
  if (budgetLabel === '1000以下') return rent < 1000
  if (budgetLabel === '1000-1500') return rent >= 1000 && rent <= 1500
  if (budgetLabel === '1500-2000') return rent > 1500 && rent <= 2000
  if (budgetLabel === '2000-2500') return rent > 2000 && rent <= 2500
  return true
}

function applyFilters(listings, filters) {
  return listings.filter(function (listing) {
    if (filters && filters.areaBand && filters.areaBand !== '全部' && listing.areaBand !== filters.areaBand) {
      return false
    }
    if (filters && filters.roomType && filters.roomType !== '全部' && listing.roomType !== filters.roomType) {
      return false
    }
    if (filters && filters.elevator && filters.elevator !== '全部' && listing.elevator !== filters.elevator) {
      return false
    }
    if (!fitsBudget(listing.monthlyRent, filters && filters.budget)) {
      return false
    }
    return true
  })
}

function createId(prefix, items) {
  return prefix + '-' + String(items.length + 1).padStart(3, '0')
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

function countByStatus(items, statusKey, knownStatuses) {
  const counts = {}
  knownStatuses.forEach(function (status) {
    counts[status] = 0
  })
  items.forEach(function (item) {
    const key = item[statusKey]
    counts[key] = (counts[key] || 0) + 1
  })
  return counts
}

const repository = {
  bootstrap() {
    getState()
    return Promise.resolve()
  },

  getPublishedListings(filters) {
    const listings = getState().listings.map(deriveListingState).filter(function (listing) {
      return listing.frontendVisible
    })
    return Promise.resolve(applyFilters(listings, filters || {}))
  },

  getAllListings() {
    return Promise.resolve(getState().listings.map(deriveListingState))
  },

  getListingById(id) {
    const listing = getState().listings.find(function (item) {
      return item.id === id
    })
    return Promise.resolve(listing ? deriveListingState(listing) : null)
  },

  submitDemandCard(payload) {
    const state = getState()
    const lead = {
      id: createId('Q', state.leads),
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
    return Promise.resolve(lead)
  },

  createViewingAppointment(payload) {
    const state = getState()
    const viewing = {
      id: createId('A', state.viewings),
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
    return Promise.resolve(viewing)
  },

  submitSupplyListing(payload) {
    const state = getState()
    const listing = {
      id: createId('L', state.listings),
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
      lastVerifiedAt: payload.lastVerifiedAt || new Date().toISOString(),
      videoUrl: payload.videoUrl,
      sourceRole: payload.sourceRole || '合作方',
      sourceChannel: '小程序邀约录入',
      status: '待核验',
      authFlag: payload.authFlag || '待认证',
      safetyTags: payload.safetyTags || ['待补实拍', '待补安全标签'],
      commuteTags: payload.commuteTags || ['待补通勤标签'],
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
    return Promise.resolve(deriveListingState(listing))
  },

  getAdminSummary() {
    const state = getState()
    const listings = state.listings.map(deriveListingState)
    const leadCounts = countByStatus(state.leads, 'status', constants.LEAD_STATUSES)
    const viewingCounts = countByStatus(state.viewings, 'status', constants.VIEWING_STATUSES)
    const riskyListings = listings.filter(function (item) {
      return item.expired || !item.publishable || item.status === '待核验'
    })
    return Promise.resolve({
      publishableCount: listings.filter(function (item) { return item.publishable && item.status === '可发布' && !item.expired }).length,
      expiredCount: listings.filter(function (item) { return item.expired }).length,
      pendingReviewCount: listings.filter(function (item) { return item.status === '待核验' }).length,
      leadStatusCount: leadCounts,
      viewingStatusCount: viewingCounts,
      latestListings: listings.slice(0, 5),
      latestLeads: clone(state.leads).slice(0, 5),
      latestViewings: clone(state.viewings).slice(0, 5),
      riskyListings: riskyListings.slice(0, 5)
    })
  },

  getAdminSession() {
    return Promise.resolve(wx.getStorageSync(ADMIN_SESSION_KEY) || null)
  },

  loginAdmin(password) {
    if (password !== 'cunzhen-admin') {
      return Promise.reject(new Error('管理员密码不正确'))
    }
    const session = {
      username: 'admin',
      token: 'inline-admin-token',
      source: 'inline'
    }
    wx.setStorageSync(ADMIN_SESSION_KEY, session)
    return Promise.resolve(session)
  },

  logoutAdmin() {
    wx.removeStorageSync(ADMIN_SESSION_KEY)
    return Promise.resolve()
  },

  updateListingStatus(id, payload) {
    const state = getState()
    let updated = null
    state.listings = state.listings.map(function (listing) {
      if (listing.id !== id) return listing
      const next = Object.assign({}, listing)
      if (payload.status) next.status = payload.status
      if (payload.authFlag) next.authFlag = payload.authFlag
      if (payload.lastVerifiedAt) next.lastVerifiedAt = payload.lastVerifiedAt
      if (payload.notes) next.notes = payload.notes
      const versions = clone(next.versions || [])
      if (payload.status || payload.authFlag || payload.lastVerifiedAt) {
        versions.push({
          version: String(versions.length + 1) + '.0',
          monthlyRent: next.monthlyRent,
          moveInDate: next.moveInDate,
          contactSnapshot: versions.length ? versions[versions.length - 1].contactSnapshot : '',
          utilityRule: next.utilityRule,
          updatedAt: new Date().toISOString()
        })
      }
      next.versions = versions
      updated = next
      return next
    })
    saveState(state)
    return Promise.resolve(updated ? deriveListingState(updated) : null)
  },

  updateLeadStatus(id, payload) {
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
    return Promise.resolve(updated)
  },

  updateViewingStatus(id, payload) {
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
    if (updated && updated.status === '爽约') {
      state.listings = state.listings.map(function (listing) {
        if (listing.id === updated.listingId && listing.status === '已预约') {
          return Object.assign({}, listing, { status: '可发布' })
        }
        return listing
      })
    }
    saveState(state)
    return Promise.resolve(updated)
  }
}

App({
  onLaunch() {
    try {
      repository.bootstrap()
    } catch (error) {
      console.error('inline bootstrap failed', error)
    }
  },
  globalData: {
    appName: '村圳',
    modules: {
      repository: repository,
      format: {
        formatCurrency: formatCurrency,
        formatDate: formatDate,
        formatVersionTag: formatVersionTag
      },
      constants: constants
    }
  }
})
