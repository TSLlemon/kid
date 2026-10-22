# 测试说明

本地验证日期：2026-10-22。环境：macOS、Python 3.12.13、Node.js 24.18.0、独立虚拟环境和临时 SQLite。没有使用真实模型或生产数据库。

| 检查 | 结果 |
| --- | --- |
| Python 后端及爬虫 pytest | 17 通过 |
| 小程序练习逻辑 Node.js 测试 | 4 通过 |
| 新库注册、密码登录及重复用户名 | 回归通过 |
| 旧库增量迁移、已有数据保留及重复启动 | 回归通过 |
| 非空词表及年级过滤 | 回归通过 |
| 前两次答错不给答案、不记错题，第三次才入库 | 回归通过 |
| 前端累计次数、失败重试、重复点击和完成后停止 | 回归通过 |

从仓库根目录建立 Python 环境后安装依赖：

    python -m pip install -r server/requirements.txt -r server/crawler/requirements.txt
    python -m pip install --no-deps -r server/requirements-tts.txt
    python -m pytest server/tests server/crawler/tests -q

Node.js 使用内置测试运行器，无额外 npm 依赖：

    node --test tests/*.test.cjs

API 测试使用独立临时数据库；模型返回被模拟，爬虫只解析合成的本地 HTML/JSON/CSV。前端测试在模拟的小程序页面环境中执行 JS，不是微信真机测试。

.github/workflows/ci.yml 在 push/pull_request 时执行上述 Python 和 Node.js 检查，使用 Python 3.12、Node.js 24，官方 Actions 固定到提交 SHA。CI 状态与日志见仓库 Actions 页面。

尚未验证：真实微信登录、模型供应商、OCR 推理、在线 TTS、Nginx/HTTPS、Docker 构建与实际抓取。现有 FastAPI startup 事件和部分依赖存在弃用警告。

requirements.txt 没有完全锁定传递依赖，rapidocr_onnxruntime 也未固定版本；本次本地解析为 1.4.4。不同平台重装可能解析到不同版本。
