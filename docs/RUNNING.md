# 运行说明

本说明针对新建的本地副本。注册、词表与三次作答逻辑已有自动回归测试；外部服务和真机使用仍有 [已知限制](KNOWN_ISSUES.md)。

## Python 开发环境

本次验证使用 Python 3.12.13。以下命令从 server/ 目录执行：

    python3.12 -m venv .venv
    source .venv/bin/activate
    python -m pip install -r requirements.txt
    python -m pip install --no-deps -r requirements-tts.txt
    cp .env.example .env

Dockerfile 分两层安装 TTS 依赖：基础列表是 edge-tts 7.2.8，第二层覆盖成 7.3.1。两个 requirements 文件不要合并为一次带版本约束的安装。

仅在自己电脑调试时，将新建 .env 中的 DEV_MODE 设为 true、DB_PATH 设为 ./data/tutor.db，并自行设置 TOKEN_SECRET。其他密钥可以留空；未配置大模型密钥时，AI 讲题不可用，本地数学题生成仍可用。

    python -m uvicorn app.main:app --env-file .env --host 127.0.0.1 --port 8000

健康检查为 GET http://127.0.0.1:8000/api/health，接口文档为 /docs。

config.py 读取进程环境变量，不会自行载入 .env；上面命令中的 --env-file 或 Docker Compose 的 env_file 负责加载它。

## 新副本的 Docker 调试

从 server/ 目录执行，使用自己的 .env：

    docker compose -f compose.local.yml up --build

这个配置只启动后端，使用当前副本的 ./data 目录，并将 8000 端口绑定到 127.0.0.1。本次审查没有构建或启动新 Docker 服务。

原有 docker-compose.yml 还包含 Nginx HTTPS 模板，需要自行配置域名、证书和数据目录。候选副本不包含证书，不能直接视为公网部署配置。

## 微信小程序

在微信开发者工具导入 miniprogram/，替换 project.config.json 中的 touristappid，并编辑 config.js 的 API_BASE。

仅在开发者工具本机调试时，可以使用 http://127.0.0.1:8000，配合前端 DEV_LOGIN=true 和后端 DEV_MODE=true。真实设备需使用设备可以访问的后端地址；正式使用要配置合法 HTTPS 域名及微信小程序请求/上传域名。

结束调试后关闭开发登录，使用自己的微信配置和家庭白名单，并替换 TOKEN_SECRET 模板值。当前程序没有强制拒绝弱 TOKEN_SECRET 的启动检查。

此版本的小程序没有完整语音对话入口。后端朗读依赖外部 TTS 服务；OCR、微信真机登录、真实大模型、TTS、HTTPS 和 Docker 构建均未做端到端验证。

## 数据与可选功能

首次启动会创建数据库结构，不会填充生产题库。数学练习优先使用本地生成器；其他科目可能依赖题库或模型服务。

课外阅读、故事、词汇、视频目录和缓存音频需要另行准备。此副本不包含生产数据或资源导入脚本，也不会自动抓取数据。Scrapy 的配置只是可选模板，单元测试只解析本地样本。

部分音频接口在请求时写缓存；MP3 转码分支还依赖 ffmpeg，现有 Dockerfile 没有安装它。
