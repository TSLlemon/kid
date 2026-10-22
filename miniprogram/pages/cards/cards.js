const words = require('../../data/words')
const poems = require('../../data/poems')
const app = getApp()
Page({
  data: { kind: 'words', all: false, cards: [], idx: 0, back: false, known: 0 },
  onLoad() { this.setData({ grade: app.globalData.grade }); this.build() },
  build() {
    const src = this.data.kind === 'words' ? words : poems
    const cards = this.data.all ? src : src.filter(c => c.grade <= this.data.grade)
    this.setData({ cards, idx: 0, back: false, known: (wx.getStorageSync('known_' + this.data.kind) || []).length })
  },
  setKind(e) { this.setData({ kind: e.currentTarget.dataset.k }); this.build() },
  toggleAll() { this.setData({ all: !this.data.all }); this.build() },
  flip() { this.setData({ back: !this.data.back }) },
  next() { this.setData({ idx: (this.data.idx + 1) % this.data.cards.length, back: false }) },
  prev() { this.setData({ idx: (this.data.idx - 1 + this.data.cards.length) % this.data.cards.length, back: false }) },
  speak() {
    const key = 'known_' + this.data.kind, k = new Set(wx.getStorageSync(key) || [])
    k.add(this.data.cards[this.data.idx].front); wx.setStorageSync(key, [...k]); this.setData({ known: k.size }); this.next()
  }
})
