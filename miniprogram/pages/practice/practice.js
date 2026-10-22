const api = require('../../utils/api')
const app = getApp()
Page({
  data: { topic: '', qs: [], loading: false },
  onShow() {
    const t = wx.getStorageSync('practiceTopic')
    if (t) { wx.removeStorageSync('practiceTopic'); this.setData({ topic: t }) }
    this.setData({ grade: app.globalData.grade, subject: app.globalData.subject })
  },
  onTopic(e) { this.setData({ topic: e.detail.value }) },
  async gen() {
    this.setData({ loading: true, qs: [] })
    try {
      const d = await api.request('/api/practice', 'POST', { grade: this.data.grade, subject: this.data.subject, topic: this.data.topic, count: 5 })
      this.setData({ qs: (d.questions || []).map(q => ({ ...q, options: q.options || [], my: '', result: null, attempt: 0, submitting: false })) })
    } finally { this.setData({ loading: false }) }
  },
  pick(e) { this.setData({ [`qs[${e.currentTarget.dataset.i}].my`]: e.currentTarget.dataset.v }) },
  fill(e) { this.setData({ [`qs[${e.currentTarget.dataset.i}].my`]: e.detail.value }) },
  async check(e) {
    const i = e.currentTarget.dataset.i, q = this.data.qs[i]
    if (!q || q.submitting || (q.result && q.result.correct) || q.attempt >= 3) return
    if (!q.my) return wx.showToast({ title: '先写答案', icon: 'none' })
    const key = 'qs[' + i + ']'
    const attempt = (q.attempt || 0) + 1
    this.setData({ [key + '.submitting']: true })
    try {
      const r = await api.request('/api/grade', 'POST', {
        grade: this.data.grade, subject: this.data.subject, question: q.question,
        answer: q.my, reference: q.answer || '', explanation: q.explanation || '', attempt
      })
      this.setData({ [key + '.attempt']: attempt, [key + '.result']: r })
    } finally {
      this.setData({ [key + '.submitting']: false })
    }
  }
})
