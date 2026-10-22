# kid-tutor 家庭版小学学习小程序

帮助家长辅导小学生的微信小程序，包含文字与拍照讲题、数学练习、错题本、学习打卡和古诗/单词卡片。后端另有 OCR、课外阅读、朗读音频和视频推荐接口；这些接口并非都已接入此版本的小程序。

这是可独立部署的家庭学习工具，采用 [MIT 许可](LICENSE)。开源版本已修复全新数据库注册、非空词表返回和练习重试流程；练习保留“前两次答错给提示，第三次答错才加入错题本”的规则。

## 目录

| 路径 | 内容 |
| --- | --- |
| miniprogram/ | 原生微信小程序 JS、WXML、WXSS、配置模板和小型卡片示例 |
| server/app/ | FastAPI、SQLite、兼容 Chat Completions 的模型调用、本地数学题生成器 |
| server/tests/ | 原有后端测试；大模型调用用模拟响应替代 |
| server/crawler/ | Scrapy 爬虫代码、示例配置和本地测试样本 |
| tests/ | 用 Node.js 内置测试运行器执行的小程序逻辑回归测试 |
| server/compose.local.yml | 新副本专用的本地 Docker 配置，端口绑定到回环地址 |
| server/docker-compose.yml | 原有 Nginx/HTTPS 部署模板，需要自己的域名和证书 |

## 本地开始

    git clone https://github.com/TSLlemon/kid.git
    cd kid/server
    cp .env.example .env

先编辑自己的 .env，设置 TOKEN_SECRET；仅在本地调试时开启 DEV_MODE。然后运行：

    docker compose -f compose.local.yml up --build

后端本地地址为 http://127.0.0.1:8000，微信开发者工具导入 miniprogram/。也可以使用 Python 虚拟环境运行。

运行和配置见 [运行说明](docs/RUNNING.md)，验证结果见 [测试说明](docs/TESTING.md)，限制见 [已知问题](docs/KNOWN_ISSUES.md)。

候选副本不附带生产数据库、真实账号、作答记录、图片、音频、书籍资源包或凭据。空数据库可以启动健康检查及本地数学练习，资源类功能需要自行提供有权使用的数据。

公开边界见 [公开文件范围](docs/PUBLISH_SCOPE.md)。依赖与内容来源见 [第三方说明](THIRD_PARTY.md)，相关声明保留在 licenses/。自动检查见 [GitHub Actions](https://github.com/TSLlemon/kid/actions)。

当前验证覆盖 Python 测试 17 项和小程序逻辑测试 4 项。尚未完成微信真机、真实模型、OCR 推理、在线朗读、HTTPS 或 Docker 构建的端到端验证；已知问题文档包含剩余部署风险。
