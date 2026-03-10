const FALLBACK_TIME_SLOTS = ['周三 19:30-22:00', '周六 14:00-18:00', '自定义沟通']

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
    listing: null,
    form: {
      leadName: '',
      contact: '',
      preferredDate: '2026-03-12',
      timeSlot: FALLBACK_TIME_SLOTS[0],
      notes: ''
    },
    timeSlots: FALLBACK_TIME_SLOTS
  },

  onLoad(query) {
    const constants = getConstants()
    const repository = getRepository()
    this.setData({ timeSlots: constants.TIME_SLOTS || FALLBACK_TIME_SLOTS })
    if (query.listingId) {
      repository.getListingById(query.listingId).then((listing) => {
        this.setData({ listing: listing })
      }).catch(showError)
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
    form.preferredDate = event.detail.value
    this.setData({ form: form })
  },

  onSlotChange(event) {
    const form = Object.assign({}, this.data.form)
    form.timeSlot = this.data.timeSlots[event.detail.value]
    this.setData({ form: form })
  },

  submitBooking() {
    const repository = getRepository()
    const listing = this.data.listing
    const form = this.data.form
    if (!listing) {
      wx.showToast({ title: '房源信息缺失', icon: 'none' })
      return
    }
    if (!form.leadName || !form.contact) {
      wx.showToast({ title: '请填写姓名和联系方式', icon: 'none' })
      return
    }
    repository.createViewingAppointment({
      listingId: listing.id,
      listingTitle: listing.title,
      leadName: form.leadName,
      contact: form.contact,
      preferredDate: form.preferredDate,
      timeSlot: form.timeSlot,
      notes: form.notes
    }).then((viewing) => {
      wx.showModal({
        title: '预约已提交',
        content: '预约状态：' + viewing.status + '。运营侧会继续确认时间和集合点。',
        confirmText: '返回房源',
        success(res) {
          if (res.confirm) {
            wx.navigateBack()
          }
        }
      })
    }).catch(showError)
  }
})
