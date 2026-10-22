const api = require('../../utils/api')
Page({
  data: { filters: ['', '语文', '数学', '英语'], subject: '', mastered: 0, list: [], open: {} },
  onShow() { this.load() },
  load() { api.request(`/api/mistakes?mastered=${this.data.mastered}&subject=${encodeURIComponent(this.data.subject)}`).then(list => this.setData({ list })) },
  filter(e) { this.setData({ subject: e.currentTarget.dataset.s }); this.load() },
  toggleMastered() { this.setData({ mastered: this.data.mastered ? 0 : 1 }); this.load() },
  toggle(e) { const id = e.currentTarget.dataset.id; this.setData({ [`open.${id}`]: !this.data.open[id] }) },
  master(e) { api.request(`/api/mistakes/${e.currentTarget.dataset.id}`, 'PATCH', { mastered: this.data.mastered ? 0 : 1 }).then(() => this.load()) },
  del(e) {
    wx.showModal({ title: '删除这道错题？', success: r => r.confirm && api.request(`/api/mistakes/${e.currentTarget.dataset.id}`, 'DELETE').then(() => this.load()) })
  },
  redo(e) { wx.setStorageSync('practiceTopic', e.currentTarget.dataset.q); wx.switchTab({ url: '/pages/practice/practice' }) }
})
