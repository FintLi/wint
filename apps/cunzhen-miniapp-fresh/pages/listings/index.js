const FALLBACK_AREA_BANDS = ['全部', '西乡', '固戍', '后瑞', '福永']
const FALLBACK_ROOM_TYPES = ['全部', '单间', '合租', '一房']
const FALLBACK_ELEVATOR_OPTIONS = ['全部', '有', '无']
const FALLBACK_BUDGET_OPTIONS = ['全部', '1000以下', '1000-1500', '1500-2000', '2000-2500']

function getModules() {
  const app = getApp()
  return (app && app.globalData && app.globalData.modules) || {}
}

function getRepository() {
  return getModules().repository
}

function getFormat() {
  return getModules().format || {}
}

function getConstants() {
  return getModules().constants || {}
}

function showError(error) {
  wx.showToast({ title: (error && error.message) || '加载失败', icon: 'none' })
}

Page({
  data: {
    listings: [],
    areaBands: FALLBACK_AREA_BANDS,
    roomTypes: FALLBACK_ROOM_TYPES,
    elevatorOptions: FALLBACK_ELEVATOR_OPTIONS,
    budgetOptions: FALLBACK_BUDGET_OPTIONS,
    filters: {
      areaBand: '全部',
      roomType: '全部',
      elevator: '全部',
      budget: '全部'
    },
    pickerIndex: {
      areaBand: 0,
      roomType: 0,
      elevator: 0,
      budget: 0
    }
  },

  onShow() {
    const constants = getConstants()
    this.setData({
      areaBands: constants.AREA_BANDS || FALLBACK_AREA_BANDS,
      roomTypes: constants.ROOM_TYPES || FALLBACK_ROOM_TYPES,
      elevatorOptions: constants.ELEVATOR_OPTIONS || FALLBACK_ELEVATOR_OPTIONS,
      budgetOptions: constants.BUDGET_OPTIONS || FALLBACK_BUDGET_OPTIONS
    })
    this.refreshListings()
  },

  refreshListings() {
    const repository = getRepository()
    const format = getFormat()
    repository.getPublishedListings(this.data.filters).then((listings) => {
      this.setData({
        listings: listings.map(function (item) {
          return Object.assign({}, item, {
            rentLabel: format.formatCurrency ? format.formatCurrency(item.monthlyRent) : item.monthlyRent,
            verifiedLabel: format.formatDate ? format.formatDate(item.lastVerifiedAt) : item.lastVerifiedAt
          })
        })
      })
    }).catch(showError)
  },

  onAreaChange(event) {
    this.updateFilter('areaBand', this.data.areaBands[event.detail.value], event.detail.value)
  },

  onRoomChange(event) {
    this.updateFilter('roomType', this.data.roomTypes[event.detail.value], event.detail.value)
  },

  onElevatorChange(event) {
    this.updateFilter('elevator', this.data.elevatorOptions[event.detail.value], event.detail.value)
  },

  onBudgetChange(event) {
    this.updateFilter('budget', this.data.budgetOptions[event.detail.value], event.detail.value)
  },

  updateFilter(field, value, index) {
    const filters = Object.assign({}, this.data.filters)
    const pickerIndex = Object.assign({}, this.data.pickerIndex)
    filters[field] = value
    pickerIndex[field] = Number(index)
    this.setData({ filters: filters, pickerIndex: pickerIndex })
    this.refreshListings()
  },

  openDetail(event) {
    wx.navigateTo({ url: '/pages/listing-detail/index?id=' + event.currentTarget.dataset.id })
  }
})
