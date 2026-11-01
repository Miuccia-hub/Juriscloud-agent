# 参考项目与独立实现

本版本独立编写 Python 应用与提示词，未复制以下项目代码或安装其中的技能。阅读其说明和部分文件用于理解设计方法；仓库中的法律内容没有直接作为已核验知识库载入。

| 项目 | 参考点 | 当前状态 |
|---|---|---|
| https://github.com/Golden2002/legal-research-skill | 争点、法源与核验步骤 | 方法参考 |
| https://github.com/CSlawyer1985/china-lawyer-analyst | 领域分类、复核与修正 | 方法参考 |
| https://github.com/CSHaitao/LexiLaw | 中文法律问答与知识库背景 | 未使用模型、权重或数据 |
| https://github.com/open-legal-products/mike | 文档、对话、修改的工作台体验 | 未复制前后端；其 AGPL 代码未并入 |
| https://github.com/General-Legal/legal-templates | 合同结构与模板思路 | 未并入模板；其模板许可单独适用 |
| https://github.com/zubair-trabzada/ai-legal-claude | 分项风险与建议 | 未使用并行 agent 或安装脚本 |
| https://github.com/gordoncprice/AustralianLegal | 区域识别、官方来源、独立复核 | 方法参考；未运行其技能团队 |
| https://github.com/tealou/auslaw-mcp | 检索、段落与引注定位 | 候选组件，尚未接入；当前用 OpenAI web_search 和独立读取模块 |

运行依赖的许可证由各项目提供。未来引入代码或模板时须固定版本、记录来源及许可；不因当前表中的参考而推定可直接复制。

## 嵌入字体

`assets/fonts/NotoSansSC-Regular.ttf` 由 Google Fonts 的 Noto Sans SC 可变字体生成默认静态 400 字重，用于中文 PDF 嵌入及文档显示。原字体来源： https://github.com/google/fonts/tree/main/ofl/notosanssc 。许可证：SIL Open Font License 1.1，完整许可与版权声明保留在 `assets/fonts/OFL.txt`。字体不作为独立付费产品销售。

官方接口参考：

- https://developers.openai.com/api/docs/guides/structured-outputs
- https://developers.openai.com/api/docs/guides/tools-web-search
- https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app


## 本轮设计方法参考

- Emil Design Engineering：https://github.com/emilkowalski/skills ，用于状态、动效频率、焦点与减少动效指导。
- Hallmark：https://github.com/Nutlope/hallmark ，用于应用范围的重设计、设计令牌、静态检查与保留工作流程。
- Mike 的实际聊天与侧面板源文件分析记录见 DESIGN.md；没有复制其实现代码。
- image-to-code：https://github.com/yuzhworkhard-wq/image-to-code/blob/main/SKILL.md 。2026-10-30 阅读，参考截图测量和样式核对方法；本轮仅独立修改 CSS，未运行其脚本、未复制截图资产，未全局安装。


首页设计参考：https://mikeoss.com/ 与 https://www.usehallmark.com/themes/refract/ 。仅参考结构及折射视觉，assets/landing 下的 HTML、CSS 与 WebGL 光纹由本项目编写，不复制参考站的图片、品牌、代码或业务数据。
