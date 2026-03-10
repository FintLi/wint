function getModules() {
  const app = getApp()
  return (app && app.globalData && app.globalData.modules) || {}
}

function getRepository() {
  return getModules().repository
}

function showError(error) {
  wx.showToast({ title: (error && error.message) || '提交失败', icon: 'none' })
}

Page({
  data: {
    form: {
      title: '',
      village: '',
      areaBand: '西乡',
      roomType: '单间',
      monthlyRent: '1200',
      depositRule: '押一付一',
      utilityRule: '',
      floorLabel: '',
      sunlight: '',
      elevator: '无',
      furnitureAppliances: '',
      moveInDate: '2026-03-15',
      lastVerifiedAt: '2026-03-09T18:00:00+08:00',
      videoUrl: '',
      sourceRole: '合作中介',
      authFlag: '待认证',
      contact: '',
      notes: ''
    }
  },

  onInput(event) {
    const field = event.currentTarget.dataset.field
    const form = Object.assign({}, this.data.form)
    form[field] = event.detail.value
    this.setData({ form: form })
  },

  onDateChange(event) {
    const form = Object.assign({}, this.data.form)
    form.moveInDate = event.detail.value
    this.setData({ form: form })
  },

  submitSupply() {
    const repository = getRepository()
    const form = this.data.form
    if (!form.village || !form.areaBand || !form.roomType || !form.monthlyRent || !form.depositRule) {
      wx.showToast({ title: '请先补齐基础房源信息', icon: 'none' })
      return
    }
    repository.submitSupplyListing(form).then((listing) => {
      wx.showModal({
        title: '提报已收到',
        content: listing.publishable ? '资料完整，可进入候选上架池。' : '资料已进入待核验，需补齐后才能上架。',
        confirmText: '我知道了',
        showCancel: false
      })
    }).catch(showError)
  }
})
