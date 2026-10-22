const api = require('../../utils/api')
Page({
  data: { s: { by_subject: [], week: [] }, records: [] },
  onShow() {
    api.request('/api/stats').then(s => this.setData({ s }))
    api.request('/api/records?limit=30').then(records => this.setData({ records }))
  },
  onPullDownRefresh() { this.onShow(); wx.stopPullDownRefresh() }
})
