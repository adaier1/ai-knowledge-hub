# AI Knowledge Hub — 用户使用手册

> 版本: v1.0  
> 最后更新: 2026-07-08  
> 在线访问: http://YOUR_SERVER_IP

---

## 1. 系统概述

AI Knowledge Hub 是一个现代化的知识管理与检索系统，支持：
- 知识的创建、编辑、删除与管理
- 混合搜索（关键词 + 语义向量）
- 知识图谱可视化
- 向量嵌入与语义检索
- MCP 协议接入（AI 助手可直接调用）
- WebDAV 备份与恢复
- 多数据库管理

---

## 2. 快速开始

### 2.1 本地开发

\`\`\`bash
# 启动后端
cd backend
pip install -r requirements.txt
python run.py

# 启动前端（新终端）
cd frontend
npm install
npm run dev
\`\`\`

前端访问: http://localhost:5173  
后端 API: http://localhost:8000

### 2.2 服务器部署

\`\`\`bash
# 前端构建
cd frontend
npm install --legacy-peer-deps
npm run build

# 部署到服务器
scp -r dist/* root@YOUR_SERVER_IP:/var/www/html/
ssh root@YOUR_SERVER_IP "chmod -R 755 /var/www/html/assets"
\`\`\`

---

## 3. 页面功能说明

### 3.1 总览 (Dashboard)
**路径:** /

总览页面是系统的数据仪表盘，包含：

- **KPI 卡片** (4个): 搜索次数、命中率、平均延迟、知识总数
  - 每张卡片底部有 Sparkline 迷你趋势图
  - 右上角时间筛选器（7天/30天/90天）
- **热门知识词云**: 以词云形式展示高频知识条目
- **最近搜索**: 最新搜索记录，显示查询内容、耗时、命中状态
- **最近新增知识**: 最新创建的知识条目，点击可跳转详情
- **来源分布**: 知识来源的环形饼图
- **系统状态**: 数据库、向量引擎、存储、MCP 服务、API 状态指示灯

### 3.2 知识库 (Knowledge)
**路径:** /knowledge

知识库列表页面，支持：
- 分页展示所有知识条目
- 搜索筛选（按标题/内容关键词）
- 标签筛选
- 点击条目进入详情页

**详情页 (/knowledge/:id):**
- 展示完整内容
- 显示标签、来源、token 数等信息
- 相关 Chunk 列表
- 相关知识推荐

### 3.3 知识图谱 (Graph)
**路径:** /graph

3D 球形知识图谱可视化：
- 节点表示知识条目
- 连线表示知识间的关系
- 支持拖拽、缩放
- Hover 显示节点标签
- 节点颜色根据连接数量变化

### 3.4 搜索日志 (Search Log)
**路径:** /search-log

搜索历史记录：
- 查询内容
- 搜索类型
- 耗时与命中状态
- 时间排序

### 3.5 数据库管理 (Database)
**路径:** /database

数据库浏览器：
- 下拉选择不同的 .db 文件
- 浏览表结构和数据
- 执行自定义 SQL 查询
- 导出/导入数据库文件

### 3.6 统计 (Analytics)
**路径:** /analytics

搜索行为分析：
- 知识总量、搜索总量、命中率、平均延迟概览
- 14天搜索趋势
- 热门搜索词排行
- 热门知识排行

### 3.7 MCP 服务配置
**路径:** /mcp

MCP (Model Context Protocol) 服务配置：
- 查看 MCP 连接地址和密钥
- 创建/删除 API Key
- 复制连接 URL
- 重置密钥

MCP 配置示例:
\`\`\`
MCP 链接 (包含密钥):
http://<服务器IP>:8086/mcp?key=<你的API密钥>
\`\`\`

### 3.8 系统设置 (Settings)
**路径:** /settings

系统设置包含：

**Embedding 设置:**
- API URL: 向量模型服务地址
- API Key: 向量模型密钥
- 模型名称: 向量模型名称
- 测试连接按钮: 验证模型配置

**WebDAV 备份:**
- URL 地址: WebDAV 服务器地址
- 用户名/密码: WebDAV 登录凭证
- 测试连接按钮
- 备份路径
- 自动备份开关 (iOS 风格 toggle)
- 备份频率: 每天/每周/每月
- 备份时间设置
- 立即备份按钮
- 导入备份: 从本地上传或从 WebDAV 获取

---

## 4. 搜索功能

### 4.1 搜索类型
系统支持多种搜索方式：
- **keyword**: 纯关键词全文搜索 (FTS5)
- **semantic**: 语义/向量搜索
- **hybrid**: 混合搜索（关键词 + 语义，默认）

### 4.2 搜索流程
1. 用户输入查询文本
2. 系统生成查询的向量嵌入
3. 同时进行关键词检索和向量检索
4. 结果合并与重排序
5. 记录搜索日志

---

## 5. 向量嵌入

### 5.1 配置向量模型
在 设置 → Embedding 设置 中配置：
1. API URL: 填入 Embedding API 地址
2. API Key: 填入认证密钥
3. 模型名称: 填入模型标识
4. 点击"测试连接"验证有效性

### 5.2 向量重建
切换向量模型后需要重建索引：
1. 保留原始文档（不会丢失数据）
2. 新建向量集合 (v2)
3. 使用新模型重新计算所有 Chunk 的向量
4. 构建新索引
5. 切换到新集合
6. 保留旧集合作为回滚方案

---

## 6. 备份与恢复

### 6.1 WebDAV 备份
使用 WebDAV 协议备份知识库：
1. 在设置中配置 WebDAV 服务器信息
2. 点击"测试连接"确认连通性
3. 设置备份路径和自动备份计划
4. 可手动点击"立即备份"

### 6.2 备份内容
备份包含完整的知识库数据：
- 数据库文件 (knowledge.db)
- 上传的文件
- 配置信息

### 6.3 恢复
- 从 WebDAV 选择备份文件恢复
- 从本地上传备份文件恢复
- 恢复后自动导入所有数据

---

## 7. MCP 接入

### 7.1 什么是 MCP
MCP (Model Context Protocol) 是 AI 助手的标准协议，通过 MCP 接入后，AI 助手可以直接：
- 搜索知识库
- 创建/更新/删除知识
- 管理标签和关系
- 调用记忆功能

### 7.2 接入配置
在 MCP 服务页面获取连接 URL:
\`\`\`
http://<服务器IP>:8086/mcp?key=<API密钥>
\`\`\`

### 7.3 可用工具
| 工具 | 用途 |
|------|------|
| search_knowledge | 搜索知识 |
| create_document | 创建知识 |
| get_document | 获取知识详情 |
| remember | 存储 AI 记忆 |
| recall | 召回 AI 记忆 |
| graph_search | 知识图谱查询 |

---

## 8. 常见问题

### 8.1 页面显示空白
- 检查 Nginx 是否运行: `systemctl status nginx`
- 检查 assets 目录权限: `chmod -R 755 /var/www/html/assets`
- 检查浏览器控制台是否有 404 错误

### 8.2 搜索无结果
- 确认知识库中有内容
- 检查 Embedding 配置是否正确
- 尝试切换搜索类型

### 8.3 备份失败
- 检查 WebDAV 服务器连通性
- 确认服务器支持 PUT 方法
- 检查备份路径权限

### 8.4 向量模型配置
- 确认 API URL 和 Key 正确
- 确认模型名称为有效的 Embedding 模型
- 部分模型不支持某些 API 端点，请参考模型文档

---

## 9. 技术栈

| 层 | 技术 |
|----|------|
| 前端框架 | Vue 3 + TypeScript |
| 构建工具 | Vite 8 |
| UI 组件 | Naive UI + 自定义样式 |
| 图表 | ECharts 6 + vue-echarts + echarts-wordcloud |
| 图谱 | Cytoscape.js |
| 图标 | Lucide Vue |
| 后端 | FastAPI (Python) |
| 数据库 | SQLite (SQLAlchemy) |
| 搜索 | FTS5 + 向量检索 |
| 认证 | JWT + API Key |
| 部署 | Nginx + Uvicorn |
