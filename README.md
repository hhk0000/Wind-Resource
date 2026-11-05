# 风序 · 风资源自动化分析平台

需求与方案阶段交付，依据上传的需求文档及两份可研参考文件设计。

- [设计方案](docs/设计方案.md)：需求拆解、模板映射、统计口径、交付阶段与风险。
- [架构文档](docs/架构文档.md)：组件、数据模型、API、版本谱系、扩展与验证计划。
- `docs/设计方案.docx`、`docs/架构文档.docx`：便于下载审阅的Word版本。
- [图表目录](docs/图表目录.csv)：从辅助模板提取的40张表和24个图位。
- `gui/`：白色圆角风格交互原型。

## 运行GUI

无需安装依赖，使用Python 3：

```sh
cd /workspace/Wind-Resource
python -m http.server 8000 --bind 0.0.0.0 --directory gui
```

浏览器打开该服务器的 `/`。也可直接打开 `gui/index.html`。后续任务使用现有检出目录，无需创建Git worktree。

页面覆盖工作台、数据导入、分析配置、图表、报告、规范管理。CSV/TXT可本地解析、映射并预检；下载示例CSV可用于体验。结束日期不含在统计区间中。回溯10/20/30年窗口随配置更新。上传后的基础统计替换图表中心的合成示例，长序列仍明确标记为示例。支持下载配置JSON、当前结果CSV、含人工标黄的报告HTML。

**边界**：浏览器内存处理，刷新丢失；不上传云端。XLS/XLSX提示未实现，不冒充解析成功。专业规范算法、相关回归、MCP、Weibull、正式DOCX、账号权限、后台队列和云端原件/初版存储均为架构设计，尚未实现。概览风况曲线始终为合成布局示例。

## 校验

`python tests/smoke.py` 使用已安装的Playwright及Chromium验证界面、真实小样本预检、窗口与下载。无需前端构建。验证记录见 `docs/验证记录.md`。

## 在线GUI与共同开发

GitHub仓库：`hhk0000/Wind-Resource`。`gui/`通过`gh-pages`发布分支提供在线原型；需要在仓库Settings → Pages启用该分支。启用前不代表网页已上线。

后续main分支中GUI变更通过`.github/workflows/publish-gui.yml`同步发布分支。完整版本、分支、方案比较和回退约定见[协作与版本管理](docs/协作与版本管理.md)，每轮变化记录在[CHANGELOG](CHANGELOG.md)。
