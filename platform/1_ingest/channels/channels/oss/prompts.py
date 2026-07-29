"""
SR-CH-003: AI 开源雷达日报 — Prompt 配置
A 快反赛道 + D 技术文档赛道
"""

# ─── A 赛道：快反 ─────────────────────────────────

A_FLASH_SYSTEM = """你是 AI 开源生态速报员，专精于将 GitHub Trending / Hugging Face / ModLib 扫描数据
转化为结构化速报。写作风格：信息点密集、快速可扫、每个项目一条灵魂描述。"""

# 昨日新发现
PROMPT_NEW_DISCOVERIES = """【A 快反赛道】昨日新发现

输入：{projects_json}（来自 ModLib 扫描 + CI Engine 开源事件）

请生成 Top 5 新开源项目速览：
1. 每个项目 50 字简介 + ⭐ 趋势 + 主要编程语言
2. 优先选择：新发布 / 快速涨星 / 独特技术栈
3. 排序：按社区热度（Star 增速 > 发布 novelty > CI Engine 影响力评分）

格式：
### {序号}. {项目名}
{简介 50 字}
> ⭐ {star数/增速} | 语言：{lang} | 许可证：{license}
"""

# 开源趋势信号
PROMPT_TREND_SIGNALS = """【A 快反赛道】开源趋势信号

输入：{events_json}

识别本周出现的新方向/范式转变：
1. 新工具链出现 → 是否解决了一个之前被忽视的痛点
2. 新模型架构 → 是否区别于 Transformer/Diffusion
3. 新许可证模式 → 是否影响商业采用

格式：
- {emoji} **{方向}**：{一句话描述} — {为什么值得关注}
"""

# 许可证与合规警示
PROMPT_LICENSE_ALERT = """【A 快反赛道】许可证与合规警示

输入：{events_json}

追踪许可证变更/安全漏洞/停维通知：
1. 许可证变更 → 对商业用户的影响
2. 安全漏洞 → CVE 编号 + 影响范围 + 修复版本
3. 停维通知 → 迁移建议

格式：
### ⚠️ {类型}：{项目名}
{描述 + 影响 + 建议}
"""


# ─── D 赛道：技术文档 ─────────────────────────────

D_TECHDOC_SYSTEM = """你是 AI 开源技术架构师，专精于对重点项目做结构化技术深读。
写作风格：技术准确、结构清晰、代码示例驱动理解。"""

# 重点项目深读
PROMPT_DEEP_PROJECT = """【D 技术文档赛道】重点项目深读

输入：{project_json}

对选定的重点项目做结构化技术深读：
1. **技术栈**：核心依赖、运行环境、部署方式
2. **架构设计**：模块划分、数据流、扩展点
3. **应用场景**：3 个典型使用场景
4. **代码示例**：1-2 个展示核心 API 的代码片段（Python/TypeScript）
5. **社区健康度**：贡献者数量、Issue 响应速度、文档质量

格式：
## {项目名}

### 技术栈
{列表}

### 架构设计
{描述 + 架构亮点}

### 应用场景
1. **{场景1}**：{描述}
2. **{场景2}**：{描述}
3. **{场景3}**：{描述}

### 快速上手
```python
{代码示例}
```

### 社区健康度
| 指标 | 值 |
|------|-----|
| GitHub Stars | {数量} |
| 活跃贡献者 | {数量} |
| Issue 平均响应 | {时间} |
| 文档评级 | {S/A/B/C} |
"""


# ─── 命名映射 ──────────────────────────────────────

OSS_ENTITIES = {
    "langchain": "LangChain",
    "llamaindex": "LlamaIndex",
    "huggingface": "Hugging Face",
    "ollama": "Ollama",
    "vllm": "vLLM",
    "crewai": "CrewAI",
    "autogen": "AutoGen",
    "comfyui": "ComfyUI",
    "diffusers": "Diffusers",
    "deepseek": "DeepSeek",
    "qwen": "Qwen（通义千问）",
    "mistral": "Mistral AI",
    "meta": "Meta",
    "stability": "Stability AI",
}

# ─── 差异度阈值 ────────────────────────────────────

STAGE_DIVERSITY_THRESHOLD = 0.50
