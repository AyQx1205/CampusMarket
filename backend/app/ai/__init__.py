"""ai 层：LangChain 1.0 服务型 AI 助手。

模块职责：
- llm.py       LLM 工厂（配置校验 + ChatOpenAI 创建）
- prompts.py   全部 Prompt 集中定义
- memory.py    Redis 会话记忆（多轮对话）
- tools.py     Agent 工具集（内部调 service 层，不走 HTTP）
- router.py    轻量意图/画像识别（老年模式提示词，无多 Agent 编排）
- agent.py     langchain 1.0 create_agent 组装主服务 Agent
- chains/      场景化结构化输出链（文案 / 搜索解析 / 估价 / 规则问答）

规范：本项目面向 create_agent API，禁止 import langgraph、禁止 AgentExecutor。
"""
