const FALLBACK_LEAD_STATUSES = ['新线索', '已联系', '已匹配', '已带看', '已成交', '流失']
const FALLBACK_VIEWING_STATUSES = ['待确认', '已确认', '已完成', '爽约']

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

function mapCountObject(counts) {
  return Object.keys(counts || {}).map(function (key) {
    return { label: key, value: counts[key] }
  })
}

function showError(error) {
  wx.showToast({ title: (error && error.message) || '加载失败', icon: 'none' })
}

Page({
  data: {
    session: null,
    password: '',
    summary: null,
    leadStats: [],
    viewingStats: []
  },

  onShow() {
    this.refreshPage()
  },

  refreshPage() {
    const repository = getRepository()
    repository.getAdminSession().then((session) => {
      if (!session) {
        this.setData({ session: null, summary: null, leadStats: [], viewingStats: [] })
        return null
      }
      this.setData({ session: session })
      return repository.getAdminSummary()
    }).then((summary) => {
      if (!summary) return
      this.setData({
        summary: summary,
        leadStats: mapCountObject(summary.leadStatusCount),
        viewingStats: mapCountObject(summary.viewingStatusCount)
      })
    }).catch(showError)
  },

  onPasswordInput(event) {
    this.setData({ password: event.detail.value })
  },

  login() {
    const repository = getRepository()
    if (!this.data.password) {
      wx.showToast({ title: '请输入管理员密码', icon: 'none' })
      return
    }
    repository.loginAdmin(this.data.password).then((session) => {
      this.setData({ session: session, password: '' })
      this.refreshPage()
      wx.showToast({ title: '登录成功', icon: 'success' })
    }).catch(showError)
  },

  logout() {
    const repository = getRepository()
    repository.logoutAdmin().then(() => {
      this.setData({ session: null, summary: null, leadStats: [], viewingStats: [] })
      wx.showToast({ title: '已退出', icon: 'none' })
    }).catch(showError)
  },

  goSupplyForm() {
    wx.navigateTo({ url: '/pages/supply-form/index' })
  },

  openListingActions(event) {
    const repository = getRepository()
    const listingId = event.currentTarget.dataset.id
    const status = event.currentTarget.dataset.status
    const authFlag = event.currentTarget.dataset.authFlag
    const actions = []

    if (status !== '可发布') {
      actions.push({ label: '标记可发布', payload: { status: '可发布' } })
    }
    actions.push({ label: '刷新核验时间', payload: { lastVerifiedAt: new Date().toISOString() } })
    if (status !== '已失效') {
      actions.push({ label: '标记已失效', payload: { status: '已失效' } })
    }
    if (authFlag !== '已认证') {
      actions.push({ label: '设为已认证', payload: { authFlag: '已认证' } })
    }

    wx.showActionSheet({
      itemList: actions.map(function (item) { return item.label }),
      success: (res) => {
        repository.updateListingStatus(listingId, actions[res.tapIndex].payload).then(() => {
          this.refreshPage()
          wx.showToast({ title: '房源已更新', icon: 'success' })
        }).catch(showError)
      }
    })
  },

  openLeadActions(event) {
    const repository = getRepository()
    const constants = getConstants()
    const leadId = event.currentTarget.dataset.id
    const currentStatus = event.currentTarget.dataset.status
    const actions = (constants.LEAD_STATUSES || FALLBACK_LEAD_STATUSES).filter(function (item) {
      return item !== currentStatus
    })
    wx.showActionSheet({
      itemList: actions,
      success: (res) => {
        repository.updateLeadStatus(leadId, { status: actions[res.tapIndex] }).then(() => {
          this.refreshPage()
          wx.showToast({ title: '线索已更新', icon: 'success' })
        }).catch(showError)
      }
    })
  },

  openViewingActions(event) {
    const repository = getRepository()
    const constants = getConstants()
    const viewingId = event.currentTarget.dataset.id
    const currentStatus = event.currentTarget.dataset.status
    const actions = (constants.VIEWING_STATUSES || FALLBACK_VIEWING_STATUSES).filter(function (item) {
      return item !== currentStatus
    })
    wx.showActionSheet({
      itemList: actions,
      success: (res) => {
        repository.updateViewingStatus(viewingId, { status: actions[res.tapIndex] }).then(() => {
          this.refreshPage()
          wx.showToast({ title: '带看已更新', icon: 'success' })
        }).catch(showError)
      }
    })
  }
})
