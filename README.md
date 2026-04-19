# 千广传媒 - 主播智能问答助手

基于 RAG（检索增强生成）的电商直播智能问答系统，为主播提供文档检索、多轮对话和流式输出。

## 技术栈

**后端**
- Python 3.10+
- FastAPI + Uvicorn
- LangChain + OpenAI API
- ChromaDB 向量数据库
- SQLite + SQLAlchemy（用户/会话数据）
- python-jose（JWT 认证）
- pdfplumber / pypdf（PDF 文档解析）

**前端**
- Vue 3 Composition API
- Element Plus UI
- Vite 5
- Markdown 渲染

## 项目结构

```
├── backend/
│   ├── app/
│   │   ├── routers/        # API 路由（auth, chat, docs, conversations）
│   │   ├── services/       # 业务逻辑（chat, document, vector）
│   │   ├── schemas/        # Pydantic 请求/响应模型
│   │   ├── config.py       # 配置管理
│   │   ├── database.py     # 数据库初始化
│   │   └── main.py         # FastAPI 入口
│   └── pyproject.toml      # 依赖管理
├── frontend/
│   ├── src/
│   │   ├── components/     # Vue 组件
│   │   ├── api/            # API 请求封装
│   │   ├── styles/         # 全局样式（设计系统 token）
│   │   ├── App.vue
│   │   └── main.js
│   └── package.json
└── README.md
```

## 快速开始

### 后端

```bash
cd backend

# 创建虚拟环境
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate  # macOS/Linux

# 安装依赖
pip install -e .

# 配置环境变量（在项目根目录创建 .env）
# OPENAI_API_KEY=sk-...
# OPENAI_BASE_URL=https://...
# SECRET_KEY=your-secret-key

# 启动服务
python -m app.main
# 或
uvicorn app.main:app --reload --port 8000
```

### 前端

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

访问 http://localhost:5173

## API 端点

| 路由 | 方法 | 说明 |
|------|------|------|
| `/auth/register` | POST | 用户注册 |
| `/auth/login` | POST | 用户登录 |
| `/chat` | POST | 流式对话（SSE） |
| `/docs/upload` | POST | 上传文档（.txt / .pdf） |
| `/conversations` | GET | 获取对话列表 |
| `/conversations/{id}` | GET | 获取对话详情 |
| `/conversations/{id}` | DELETE | 删除对话 |
| `/conversations/{id}/rename` | PUT | 重命名对话 |

## 功能特性

- 文档上传与向量化（支持 .txt 和 .pdf）
- 混合检索（BM25 + 向量相似度）
- 流式输出（SSE）
- 多轮对话管理
- 对话重命名 / 删除
- JWT 用户认证
- 消息点赞/点踩反馈
- 深色主题 UI（Together AI 风格）
- 移动端响应式

## 设计系统

全局 CSS 变量定义在 `frontend/src/styles/notion.css`，包含：
- 亮色/暗色双世界主题
- 品牌色：品红 `#ef2cc1` → 橙色 `#fc4c02` 渐变
- Inter 字体族 + 负 letter-spacing
- 4px 锐利圆角

## License

Private - 千广传媒
