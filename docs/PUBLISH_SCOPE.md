# 公开文件范围

本仓库从独立脱敏副本建立，保留应用代码与部署模板，不导入生产目录或历史备份。

| 建议包含 | 边界 |
| --- | --- |
| miniprogram/ | 页面、逻辑、样式、模板配置及简单古诗/单词卡片 |
| server/app/ | 当前后端源码；页面中的个人局域网地址已去除 |
| server/tests/ | 原有测试，数据库位置调整为独立临时目录 |
| server/crawler/ | 爬虫代码、示例选择器和小型测试样本；不附带抓取成果 |
| Dockerfile、requirements、Nginx 模板 | 保留现有依赖结构和部署模板 |
| .env.example、.gitignore、.dockerignore | 全新配置模板和排除规则 |
| compose.local.yml、README 和 docs/ | 新副本的本地运行与审核说明 |
| tests/、.github/workflows/ | 前端逻辑回归测试与自动检查 |
| LICENSE、licenses/ | 项目 MIT 许可与第三方声明 |

明确排除：

- 生产 .env、旧 .env.example、任何 .env 备份或生产 override。
- SQLite 数据库、用户资料、身份标识、账号散列、学习记录、错题、打卡和私人聊天。
- 书籍全文、翻译、插图、题库资源包、视频目录、音频、录音和抓取缓存。
- 所有 ZIP/GZ/TAR、旧小程序副本、代码备份、虚拟环境、日志、缓存和临时文件。
- TLS 私钥、证书、SSH 文件、服务器维护脚本及其他项目。
- server/scripts/ 的资源导入与维护脚本；这些脚本及配套数据需要单独核对来源与用途。

.gitignore 不会自动保护已经跟踪的文件。今后新增文件应继续核对提交清单，扫描密钥和个人数据，并保留第三方内容来源与许可。仓库历史从脱敏代码开始，不包含部署目录历史。
