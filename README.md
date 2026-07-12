<p align="center">
  <img src="frontend/public/favicon.svg" width="80" alt="AI Knowledge Hub" />
</p>

<h1 align="center">AI Knowledge Hub</h1>

<p align="center">
  <strong>智能知识库管理系统</strong><br>
  FastAPI + Vue 3 + SQLite · 语义搜索 · 知识图谱 · MCP 协议
</p>

<p align="center">
  <img src="https://img.shields.io/badge/backend-FastAPI-009688" alt="FastAPI">
  <img src="https://img.shields.io/badge/frontend-Vue_3-4FC08D" alt="Vue 3">
  <img src="https://img.shields.io/badge/search-FTS5_+-_Vector-3B82F6" alt="Search">
  <img src="https://img.shields.io/badge/protocol-MCP-7C3AED" alt="MCP">
</p>

---

## 概述

AI Knowledge Hub 是一个现代化的知识库管理系统，支持文档管理、语义搜索、知识图谱展示，并提供标准的 MCP（Model Context Protocol）接口，允许 AI 助手直接连接和查询知识库。

### 核心功能

- **文档管理** — 创建、编辑、导入/导出文档，支持 Markdown 格式
- **语义搜索** — 混合搜索（FTS5 全文检索 + 向量语义搜索），支持多种 Embedding 模型
- **知识图谱** — 自动关联文档，可视化展示知识间的关系
- **MCP 协议** — 提供标准 MCP 接口，支持 Claude Desktop、Cursor 等 AI 客户端直连
- **WebDAV 备份** — 支持自动定时备份到 WebDAV 服务器，包含数据库和文档数据
- **向量管理** — 多版本向量索引管理，支持重建和切换
- **总览仪表盘** — KPI 卡片、搜索趋势、热门知识词云等数据分析

### 技术栈

| 层 | 技术 |
|------|------|
| 后端框架 | FastAPI (Python) |
| 前端框架 | Vue 3 + TypeScript + Vite |
| UI 组件 | Lucide Icons + ECharts |
| 数据库 | SQLite + FTS5 全文索引 |
| 向量搜索 | 余弦相似度 + HNSW（近似最近邻） |
| 图表 | ECharts + echarts-wordcloud |
| 图谱 | Cytoscape.js |
| MCP 协议 | HTTP REST（非标准 SSE） |

---

## 快速开始

### 本地开发

**后端：**

`ash
cd backend
python3 -m venv venv
source venv/bin/activate  # Windows: venv\\Scripts\\activate
pip install -r requirements.txt
python3 run.py
`

后端默认启动在 http://localhost:8000

**前端：**

`ash
cd frontend
npm install
npm run dev
`

前端默认启动在 http://localhost:5173

### Docker 部署

`ash
docker-compose up -d
`

### 生产部署

参考 deploy.sh 脚本，使用 Nginx 反向代理到后端的 :8000 端口，前端构建产物部署到 /var/www/html。

---

## 项目结构

`
ai-knowledge-hub/
├── backend/                    # FastAPI 后端
│   ├── app/
│   │   ├── api/               # REST API 路由
│   │   ├── mcp/               # MCP 协议实现
│   │   ├── models/            # SQLAlchemy 模型
│   │   ├── services/          # 业务逻辑层
│   │   ├── core/              # 核心配置与安全
│   │   ├── schemas/           # Pydantic 数据模型
│   │   ├── main.py            # 应用入口
│   │   └── database.py        # 数据库连接
│   ├── requirements.txt
│   └── run.py
├── frontend/                   # Vue 3 前端
│   ├── src/
│   │   ├── views/             # 页面视图
│   │   │   ├── dashboard/     # 总览
│   │   │   ├── knowledge/     # 知识库
│   │   │   ├── graph/         # 知识图谱
│   │   │   ├── settings/      # 设置
│   │   │   ├── search-log/    # 搜索日志
│   │   │   ├── database/      # 数据库管理
│   │   │   └── mcp/           # MCP 配置
│   │   ├── api/               # API 客户端
│   │   ├── router/            # 路由配置
│   │   └── stores/            # 状态管理
│   ├── package.json
│   └── vite.config.ts
├── docs/                       # 文档
│   ├── API_INTERFACE.md       # API 接口文档
│   ├── UI_DESIGN.md           # UI 设计规范
│   └── USER_GUIDE.md          # 用户指南
├── mcp_stdio_client.py        # MCP stdio 包装脚本
├── nginx.conf                 # Nginx 配置模板
├── docker-compose.yml
└── deploy.sh
`

---

## API 概览

### REST API

所有 REST 接口均需要通过 ?key=xxx 参数认证。

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/analytics/dashboard | 仪表盘数据 |
| POST | /api/search?key=xxx | 语义搜索 |
| GET | /api/knowledge?key=xxx | 文档列表 |
| GET | /api/knowledge/{id}?key=xxx | 文档详情 |
| POST | /api/knowledge?key=xxx | 创建文档 |
| GET | /api/graph?key=xxx | 图谱数据 |

### MCP 接口

MCP 客户端通过以下方式连接：

`
GET  /mcp?key=xxx              → 工具列表元数据
POST /mcp/tools/{name}?key=xxx → 执行工具
`

---

## 配置

在 Web 界面的「设置」页面中可配置：

- **向量模型** — 自定义 API URL、API Key、模型名称（支持 OpenAI、SiliconFlow、Ollama、豆包等）
- **检索参数** — 返回结果数量
- **图谱设置** — 最大节点数
- **WebDAV 备份** — 自动定时备份到远程服务器

---

## 使用许可

MIT License
