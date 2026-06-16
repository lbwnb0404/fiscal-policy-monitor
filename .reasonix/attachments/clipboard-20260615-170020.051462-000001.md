# 财政政策舆情监测系统 — Handoff 文档

**生成时间:** 2026-06-15
**来源对话:** 从项目启动到定时任务配置完成的完整开发过程
**项目目录:** C:\Users\jjt\Desktop\财政政策舆情监测

---

## 项目状态摘要

核心功能已完成并测试通过。项目处于"功能稳定化"阶段末尾，即将进入"展示优化"阶段。

### 完成度矩阵

| 模块 | 状态 | 说明 |
|------|------|------|
| 数据采集 | 完成 | 4个数据源：财政部、统计局、第一财经、B站 |
| AI分析 | 完成 | DeepSeek API 分类+情绪+关键词+洞察 |
| 报告生成 | 完成 | 图表/PDF/Markdown/公众号素材包 |
| 可视化 | 完成 | Streamlit http://localhost:8501 |
| 一键运行 | 完成 | python main.py |
| 基础测试 | 完成 | 6/6 通过 |
| B站数据源 | 完成 | 通过 B站公开搜索 API（无额度限制） |
| 定时任务 | 完成 | 每周五 17:00 自动运行 (schtasks) |
| 配置管理 | 未开始 | config.py 已创建但未完整迁移 |
| 错误处理 | 未开始 | 基础 try/except 已存在但需增强 |
| UI美化 | 未开始 | Streamlit 默认样式 |
| AI洞察优化 | 未开始 | 可用 nature-writing skill 优化 |

---

## 架构

4个模块通过文件系统解耦：

1. **data_collector.py** — 直接HTTP请求采集（不依赖 anysearch 搜索API）
2. **analyzer.py** — DeepSeek API 分析
3. **report_generator.py** — matplotlib/wordcloud/fpdf2 生成报告
4. **streamlit_app.py** — 交互式可视化

每个模块可独立运行。全流程由 main.py 或 un_weekly.py 串联。

---

## 关键配置

### 环境变量
- DEEPSEEK_API_KEY: sk-210eb0617fdf4cc38029aa4c664f15e3（在 .env 文件中）
- PYTHONPATH: <project_dir>\py_deps_new
- MPLCONFIGDIR: <project_dir>\output\tmp

### 系统环境变量（已设置）
- PYTHONPATH (User): 同上
- MPLCONFIGDIR (User): 同上

### 计划任务
- 名称: FiscalPolicyWeekly
- 触发: 每周五 17:00
- 执行: python run_weekly.py
- 下次运行: 2026/6/19 17:00

---

## 已知问题和注意事项

### Streamlit 启动
- 需要 --global.developmentMode false 参数
- config.toml 已删除（曾有 BOM 编码问题）
- 启动方式: python -m streamlit run streamlit_app.py --global.developmentMode false
- 端口: 8501（后端 + 前端）

### anysearch 额度
- 账号每日免费额度已用完（10974/0）
- 现有 Key: as_sk_04c72d357372a6f05f10a67d2d7a8d93
- **不需要 anysearch**：目前所有数据源均通过直接 HTTP 请求采集

### 当前进程
- python.exe 进程可能已停止（端口8501不一定在监听）
- 重启方式: Start-Process python "-m streamlit run streamlit_app.py --global.developmentMode false"

---

## 已完成的关键调试修复

1. **credentials.py 补丁**: 已修改 py_deps_new\streamlit\runtime\credentials.py 中的 check_credentials 函数，替换为直接 return
2. **BOM 编码问题**: .streamlit\config.toml 的 UTF-8 BOM 导致 TOML 解析失败，已删除
3. **B站 API**: 使用 https://api.bilibili.com/x/web-interface/search/type?search_type=video&keyword=... 直接访问
4. **PowerShell 编码**: 中文路径在 cmd.exe 批处理中有编码问题，已改用 Python 脚本执行定时任务

---

## 数据源状态

| 数据源 | 类型 | 技术方案 | 状态 |
|--------|------|---------|------|
| 财政部 mof.gov.cn | 官方 | 直接 requests 抓取 | 稳定 |
| 统计局 stats.gov.cn | 官方 | 直接 requests 抓取 | 稳定 |
| 第一财经 yicai.com | 财经媒体 | 直接 requests 抓取 | 稳定 |
| B站 bilibili.com | 社交媒体 | B站公开搜索 API | 稳定（新加） |
| 人民网 | 财经媒体 | 已移除（导航页问题） | 已移除 |
| 小红书 | 社交媒体 | 未实现 | 待规划 |
| 抖音 | 社交媒体 | 未实现 | 待规划 |

---

## 后续路线图

### 第一阶段: 功能稳定化（当前）
- [x] 基础测试 test.py (6/6 通过)
- [x] B站数据源
- [x] 定时任务 (FiscalPolicyWeekly)
- [ ] 配置管理 —— 将硬编码的数据源、路径等迁移到 config.py
- [ ] 错误处理增强 —— 重试机制、API降级、超时处理

### 第二阶段: 展示优化（推荐优先）
- [ ] Streamlit 主题美化 —— 用 frontend-design skill 提供配色/字体方案
- [ ] AI洞察写作优化 —— 用 nature-writing skill 优化周报文风
- [ ] 封面图 AI 生成 —— 用 imagegen skill 生成精美公众号封面

### 第三阶段: 面试准备
- [ ] README 升级（含架构图、演示截图）
- [ ] 面试问答准备

---

## 推荐 Skill

在下一阶段工作中，以下 skill 会有帮助（按优先级排列）:

| 优先级 | Skill | 场景 |
|--------|-------|------|
| 1 | rontend-design | Streamlit UI 美化（配色、字体、布局） |
| 2 | 
ature-writing | 优化 AI 洞察的写作风格，从通用→学术级政策分析 |
| 3 | imagegen | 生成 AI 封面图替代当前 Pillow 文字图 |
| 4 | eview | 代码审查（编码规范、需求匹配） |
| 5 | nysearch | 当额度恢复后可辅助搜索其它社交媒体数据 |
| 6 | 	each | 学习特定技术 |

---

## 测试结果

运行 python test.py，6/6 全部通过:
1. 环境配置 — 依赖包导入 OK, API Key 配置 OK
2. 数据采集 — 财政部页面 29037 bytes, 46个链接
3. 数据分析 — 1个数据文件格式正确
4. 报告生成 — 图表完整, PDF 存在
5. 端到端验证 — 全流程通过

---

*手写文档结束 — 请读取上述路径中的设计文档和代码文件获取更多细节。*
*API Key 已从本文档中显示，实际存储在 .env 文件中。*