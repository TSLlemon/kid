// ★ 唯一需要改的配置：后端地址
// 开发者工具本地调试：http://127.0.0.1:8000 （需在"详情-本地设置"勾选"不校验合法域名"）
// 真机/体验版：必须是已备案的 https 域名，并在小程序后台配置为 request/uploadFile 合法域名
module.exports = {
  API_BASE: 'https://your.domain.com',
  DEV_LOGIN: false // 后端 DEV_MODE=true 时可设 true，跳过微信登录
}
