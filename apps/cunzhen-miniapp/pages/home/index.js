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

function showError(error) {
  wx.showToast({ title: (error && error.message) || '加载失败', icon: 'none' })
}

Page({
  data: {
    featuredListings: [],
    summaryCards: []
  },

  onShow() {
    this.refreshPage()
  },

  refreshPage() {
    const repository = getRepository()
    const format = getFormat()
    Promise.all([
      repository.getPublishedListings({}),
      repository.getAdminSummary()
    ]).then((results) => {
      const listings = results[0].slice(0, 3).map(function (item) {
        return Object.assign({}, item, {
          rentLabel: format.formatCurrency ? format.formatCurrency(item.monthlyRent) : item.monthlyRent,
          verifiedLabel: format.formatDate ? format.formatDate(item.lastVerifiedAt) : item.lastVerifiedAt
        })
      })
      const admin = results[1]
      this.setData({
        featuredListings: listings,
        summaryCards: [
          { label: '当前可发布房源', value: admin.publishableCount || 0 },
          { label: '待处理线索', value: ((admin.leadStatusCount && admin.leadStatusCount['新线索']) || 0) + ((admin.leadStatusCount && admin.leadStatusCount['已联系']) || 0) },
          { label: '待核验房源', value: admin.pendingReviewCount || 0 },
          { label: '失效风险房源', value: admin.expiredCount || 0 }
        ]
      })
    }).catch(showError)
  },

  goListings() {
    wx.switchTab({ url: '/pages/listings/index' })
  },

  goDemandForm() {
    wx.switchTab({ url: '/pages/demand-form/index' })
  },

  goSupplyForm() {
    wx.navigateTo({ url: '/pages/supply-form/index' })
  },

  openDetail(event) {
    const id = event.currentTarget.dataset.id
    wx.navigateTo({ url: '/pages/listing-detail/index?id=' + id })
  }
})
