const assert = require('node:assert/strict')
const fs = require('node:fs')
const path = require('node:path')
const test = require('node:test')
const vm = require('node:vm')

const source = fs.readFileSync(path.join(__dirname, '../miniprogram/pages/practice/practice.js'), 'utf8')
const event = { currentTarget: { dataset: { i: 0 } } }

function pageFor(gradeHandler) {
  const calls = []
  const api = {
    async request(route, method, body) {
      calls.push({ route, method, body })
      if (route === '/api/practice') return { questions: [{ question: '2+2', answer: '4' }] }
      return gradeHandler(body)
    }
  }
  let definition
  vm.runInNewContext(source, {
    require: () => api,
    getApp: () => ({ globalData: { grade: 1, subject: '数学' } }),
    Page: value => { definition = value },
    wx: { showToast() {} }
  })
  const page = {
    ...definition,
    data: structuredClone(definition.data),
    setData(values) {
      for (const [key, value] of Object.entries(values)) {
        const match = key.match(/^qs\[(\d+)\]\.(\w+)$/)
        if (match) this.data.qs[Number(match[1])][match[2]] = value
        else this.data[key] = value
      }
    }
  }
  page.data.grade = 1
  page.data.subject = '数学'
  return { page, calls }
}

test('three incorrect submissions send attempts 1, 2, 3, then stop', async () => {
  const { page, calls } = pageFor(body => ({
    correct: false, hint_level: body.attempt,
    ...(body.attempt === 3 ? { correct_answer: '4' } : { hint: '再想想' })
  }))
  await page.gen()
  page.data.qs[0].my = '5'
  for (let attempt = 1; attempt <= 3; attempt++) {
    await page.check(event)
    assert.equal(page.data.qs[0].attempt, attempt)
    assert.equal(page.data.qs[0].submitting, false)
    if (attempt < 3) assert.equal(page.data.qs[0].result.correct_answer, undefined)
  }
  await page.check(event)
  assert.deepEqual(calls.filter(c => c.route === '/api/grade').map(c => c.body.attempt), [1, 2, 3])
  assert.equal(page.data.qs[0].result.correct_answer, '4')
  await page.gen()
  assert.equal(page.data.qs[0].attempt, 0)
  assert.equal(page.data.qs[0].result, null)
})

test('a correct answer cannot be submitted again', async () => {
  const { page, calls } = pageFor(() => ({ correct: true }))
  await page.gen()
  page.data.qs[0].my = '4'
  await page.check(event)
  await page.check(event)
  assert.equal(calls.filter(c => c.route === '/api/grade').length, 1)
})

test('a failed request releases the button and does not consume an attempt', async () => {
  let fail = true
  const { page, calls } = pageFor(() => {
    if (fail) throw new Error('synthetic network failure')
    return { correct: false, hint: '再想想' }
  })
  await page.gen()
  page.data.qs[0].my = '5'
  await assert.rejects(page.check(event), /synthetic network failure/)
  assert.equal(page.data.qs[0].attempt, 0)
  assert.equal(page.data.qs[0].submitting, false)
  fail = false
  await page.check(event)
  assert.deepEqual(calls.filter(c => c.route === '/api/grade').map(c => c.body.attempt), [1, 1])
})

test('overlapping clicks issue one grading request', async () => {
  let release
  const { page, calls } = pageFor(() => new Promise(resolve => { release = resolve }))
  await page.gen()
  page.data.qs[0].my = '5'
  const pending = page.check(event)
  await page.check(event)
  assert.equal(calls.filter(c => c.route === '/api/grade').length, 1)
  release({ correct: false, hint: '再想想' })
  await pending
  assert.equal(page.data.qs[0].attempt, 1)
})
