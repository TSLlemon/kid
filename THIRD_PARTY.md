# 第三方依赖与内容

本项目应用代码采用根目录的 MIT 许可。下表是本次安装包元数据与上游许可文件的清单，不替代各个实际分发包中的完整声明。licenses/ 保留主要直接依赖及示例数据源的许可文本；依赖没有被重新授权为本项目的 MIT 许可。

| 直接依赖 | 现有要求 / 本次验证版本 | 包声明许可 |
| --- | --- | --- |
| FastAPI | 0.115.6 | MIT |
| Uvicorn | 0.32.1，含 standard 扩展 | BSD-3-Clause；扩展依赖另计 |
| HTTPX | 0.28.1 | BSD-3-Clause |
| python-multipart | 0.0.20 | Apache-2.0 |
| Pydantic | 2.10.4 | MIT |
| pytest | 8.3.4 | MIT |
| rapidocr-onnxruntime | 原文件未固定版本；本次为 1.4.4 | Apache-2.0 |
| edge-tts | 基础 7.2.8，Docker 第二层覆盖为 7.3.1 | LGPLv3；完整上游文件另含第三方声明 |
| Scrapy | 2.13.3 | BSD-3-Clause |
| PyYAML | 6.0.2 | MIT |

代码还直接导入 NumPy 和 Pillow，目前由其他依赖间接安装。OCR 模型、ONNX Runtime、OpenCV 及其他传递依赖，需按最终锁定版本补齐清单。此副本没有打包依赖库、模型或构建镜像。

核验过的上游许可：

- [RapidOCR 许可](https://github.com/RapidAI/RapidOCR/blob/main/LICENSE)：Apache-2.0。
- [edge-tts 许可](https://github.com/rany2/edge-tts/blob/master/LICENSE)：包含 LGPLv3 及第三方声明。发布镜像或改动该库时，应保留相应许可与通知。
- [chinese-poetry 许可](https://github.com/chinese-poetry/chinese-poetry/blob/master/LICENSE)：MIT。crawler/sources.yaml 引用这个数据源；本副本没有附带其完整数据集，如另行导入并分发，需要保留其版权与许可声明。

小程序卡片只包含按作者署名的传统古诗原文和基础单词，不含现代译注或完整第三方词典。见 [卡片说明](miniprogram/data/README.md)。爬虫测试样本是本项目编写的合成算术、短句和基础单词，未附带真实抓取数据，见 [样本说明](server/crawler/tests/fixtures/README.md)。

生产目录中的现代读物、翻译、插图、抓取题库、视频目录和音频均未加入候选集。某个数据源采用开放许可，并不能证明整个生产数据目录都可再分发；需要按具体内容分别核对。

微信服务、模型提供商和在线 TTS 的使用还受各自服务条款约束。依赖软件许可证本身不授予这些服务或生成音频的额外使用权。
