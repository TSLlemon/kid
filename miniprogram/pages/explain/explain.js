const api = require('../../utils/api')
const app = getApp()
Page({
  data: { question: '', img: '', res: null, showAll: false, loading: false },
  onShow() { this.setData({ grade: app.globalData.grade, subject: app.globalData.subject }) },
  onInput(e) { this.setData({ question: e.detail.value }) },
  chooseImg() {
    wx.chooseMedia({ count: 1, mediaType: ['image'], sourceType: ['camera', 'album'], sizeType: ['compressed'],
      success: r => this.setData({ img: r.tempFiles[0].tempFilePath }) })
  },
  async ask() {
    const { question, img, grade, subject } = this.data
    if (!question && !img) return wx.showToast({ title: '先输入题目或拍照', icon: 'none' })
    this.setData({ loading: true, res: null, showAll: false })
    try {
      const res = img ? await api.upload('/api/explain_image', img, { grade, subject, note: question })
                      : await api.request('/api/explain', 'POST', { grade, subject, question })
      this.setData({ res })
    } finally { this.setData({ loading: false }) }
  },
  reveal() { this.setData({ showAll: true }) },
  saveMistake() {
    const { res, grade, subject, question } = this.data
    api.request('/api/mistakes', 'POST', { grade, subject, question: res.question || question, correct_answer: res.answer || '', explanation: (res.steps || []).join('\n') })
      .then(() => wx.showToast({ title: '已加入' }))
  },
  practiceSimilar() {
    wx.setStorageSync('practiceTopic', this.data.res.question || this.data.question)
    wx.switchTab({ url: '/pages/practice/practice' })
  }
})
