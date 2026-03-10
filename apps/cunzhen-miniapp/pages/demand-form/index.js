const FALLBACK_COMMUTE_OPTIONS = ['30 分钟内', '45 分钟内', '60 分钟内']

function getModules() {
  const app = getApp()
  return (app && app.globalData && app.globalData.modules) || {}
}

function getRepository() {
  return getModules().repository
}

function getConstants() {
  return getModules().constants || {}
}

function showError(error) {
  wx.showToast({ title: (error && error.message) || '提交失败', icon: 'none' })
}

Page({
  data: {
    listingId: '',
    form: {
      name: '',
      contact: '',
      budgetMin: '1000',
      budgetMax: '1800',
      workArea: '',
      commutePreference: FALLBACK_COMMUTE_OPTIONS[1],
      roomPreference: '单间',
      moveInDeadline: '2026-03-16',
      sourceChannel: '小程序求租卡',
      notes: ''
    },
    commuteOptions: FALLBACK_COMMUTE_OPTIONS
  },

  onLoad(query) {
    const constants = getConstants()
    this.setData({ commuteOptions: constants.COMMUTE_OPTIONS || FALLBACK_COMMUTE_OPTIONS })
    if (query.listingId) {
      this.setData({ listingId: query.listingId })
    }
  },

  onInput(event) {
    const field = event.currentTarget.dataset.field
    const form = Object.assign({}, this.data.form)
    form[field] = event.detail.value
    this.setData({ form: form })
  },

  onRoomChange(event) {
    const form = Object.assign({}, this.data.form)
    form.roomPreference = event.detail.value
    this.setData({ form: form })
  },

  onCommuteChange(event) {
    const form = Object.assign({}, this.data.form)
    form.commutePreference = this.data.commuteOptions[event.detail.value]
    this.setData({ form: form })
  },

  onDateChange(event) {
    const form = Object.assign({}, this.data.form)
    form.moveInDeadline = event.detail.value
    this.setData({ form: form })
  },

  submitForm() {
    const form = this.data.form
    const repository = getRepository()
    if (!form.name || !form.contact || !form.workArea || !form.budgetMin || !form.budgetMax) {
      wx.showToast({ title: '请先补齐必填项', icon: 'none' })
      return
    }
    repository.submitDemandCard(form).then((lead) => {
      wx.showModal({
        title: '求租卡已提交',
        content: '线索级别：' + lead.priority + '。建议你现在继续预约看房或等待人工匹配 3 套房源。',
        confirmText: '去找房',
        success(res) {
          if (res.confirm) {
            wx.switchTab({ url: '/pages/listings/index' })
          }
        }
      })
    }).catch(showError)
  }
})
