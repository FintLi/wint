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
    listing: null
  },

  onLoad(query) {
    if (query.id) {
      this.loadListing(query.id)
    }
  },

  onShow() {
    if (this.data.listing && this.data.listing.id) {
      this.loadListing(this.data.listing.id)
    }
  },

  loadListing(id) {
    const repository = getRepository()
    const format = getFormat()
    repository.getListingById(id).then((listing) => {
      if (!listing) {
        wx.showToast({ title: '房源不存在', icon: 'none' })
        return
      }
      this.setData({
        listing: Object.assign({}, listing, {
          rentLabel: format.formatCurrency ? format.formatCurrency(listing.monthlyRent) : listing.monthlyRent,
          verifiedLabel: format.formatDate ? format.formatDate(listing.lastVerifiedAt) : listing.lastVerifiedAt,
          versionLabel: format.formatVersionTag && listing.versions && listing.versions.length
            ? format.formatVersionTag(listing.versions[listing.versions.length - 1].version)
            : 'v1'
        })
      })
    }).catch(showError)
  },

  goDemandForm() {
    wx.navigateTo({ url: '/pages/demand-form/index?listingId=' + this.data.listing.id })
  },

  goViewing() {
    wx.navigateTo({ url: '/pages/viewing-booking/index?listingId=' + this.data.listing.id })
  },

  copyVideoUrl() {
    wx.setClipboardData({
      data: this.data.listing.videoUrl,
      success() {
        wx.showToast({ title: '视频链接已复制', icon: 'none' })
      }
    })
  }
})
