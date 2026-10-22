const api = require('./utils/api')
App({
  globalData: { grade: wx.getStorageSync('grade') || 3, subject: wx.getStorageSync('subject') || '数学' },
  onLaunch() { api.login().catch(e => console.warn('登录失败', e)) },
  setPref(grade, subject) {
    this.globalData.grade = grade; this.globalData.subject = subject
    wx.setStorageSync('grade', grade); wx.setStorageSync('subject', subject)
  }
})
