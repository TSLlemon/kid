const api = require('../../utils/api')
const app = getApp()
Page({
  data: { grades: [1, 2, 3, 4, 5, 6], subjects: ['语文', '数学', '英语'], grade: 3, subject: '数学', checked: false, streak: 0 },
  onShow() {
    this.setData({ grade: app.globalData.grade, subject: app.globalData.subject })
    api.request('/api/checkin').then(d => this.setData(d)).catch(() => {})
  },
  pickGrade(e) { const g = +e.currentTarget.dataset.g; this.setData({ grade: g }); app.setPref(g, this.data.subject) },
  pickSubject(e) { const s = e.currentTarget.dataset.s; this.setData({ subject: s }); app.setPref(this.data.grade, s) },
  checkin() { api.request('/api/checkin', 'POST').then(d => { this.setData(d); wx.showToast({ title: '打卡成功！' }) }) },
  go(e) { const { url, tab } = e.currentTarget.dataset; tab ? wx.switchTab({ url }) : wx.navigateTo({ url }) }
})
