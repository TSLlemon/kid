const { API_BASE, DEV_LOGIN } = require('../config')

function login() {
  return new Promise((resolve, reject) => {
    const done = code => wx.request({
      url: API_BASE + '/api/login', method: 'POST', data: { code },
      success: r => r.statusCode === 200 ? (wx.setStorageSync('token', r.data.token), resolve(r.data)) : reject(r.data),
      fail: reject
    })
    if (DEV_LOGIN) return done('devkid')
    wx.login({ success: r => done(r.code), fail: reject })
  })
}

function request(path, method = 'GET', data = {}, retry = true) {
  return new Promise((resolve, reject) => {
    wx.request({
      url: API_BASE + path, method, data, timeout: 120000,
      header: { Authorization: 'Bearer ' + (wx.getStorageSync('token') || '') },
      success: async r => {
        if (r.statusCode === 401 && retry) {
          try { await login(); resolve(await request(path, method, data, false)) } catch (e) { reject(e) }
        } else if (r.statusCode >= 200 && r.statusCode < 300) resolve(r.data)
        else { wx.showToast({ title: (r.data && r.data.detail) || '出错了', icon: 'none' }); reject(r.data) }
      },
      fail: e => { wx.showToast({ title: '网络错误', icon: 'none' }); reject(e) }
    })
  })
}

function upload(path, filePath, formData) {
  return new Promise((resolve, reject) => {
    wx.uploadFile({
      url: API_BASE + path, filePath, name: 'file', formData, timeout: 120000,
      header: { Authorization: 'Bearer ' + (wx.getStorageSync('token') || '') },
      success: r => {
        let d = {}; try { d = JSON.parse(r.data) } catch (e) {}
        if (r.statusCode === 200) resolve(d); else { wx.showToast({ title: d.detail || '出错了', icon: 'none' }); reject(d) }
      },
      fail: reject
    })
  })
}
module.exports = { login, request, upload }
