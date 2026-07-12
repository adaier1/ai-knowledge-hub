# AI Knowledge Hub — UI 设计规范文档

> 版本: v1.0  
> 最后更新: 2026-07-08  
> 框架: Vue 3 + TypeScript + Vite + Naive UI + TailwindCSS

---

## 1. 设计语言

### 1.1 设计风格
- **Apple 极简风格**: 大量留白、圆角卡片、毛玻璃效果
- 参考: Vercel Dashboard、Linear、Apple Design
- 配色柔和，以浅色为主

### 1.2 设计原则
- Clean & Minimal: 移除不必要的装饰元素
- Data First: 数据可视化优先
- Responsive: 适配桌面端（1200px+）和平板
- Smooth: 200ms ease 过渡动画

---

## 2. 色彩系统

### 2.1 全局 CSS 变量

\`\`\`css
:root {
  --apple-blue: #0071e3;
  --apple-blue-hover: #0077ed;
  --apple-green: #34c759;
  --apple-orange: #ff9f0a;
  --apple-red: #ff3b30;
  --apple-text-primary: #1d1d1f;
  --apple-text-secondary: #6e6e73;
  --apple-text-tertiary: #86868b;
  --apple-bg: #f5f5f7;
  --apple-card: #ffffff;
  --apple-border: #e8e8ed;
  --apple-sidebar-bg: #ffffff;
  --apple-sidebar-active: #f5f5f7;
  --apple-shadow-sm: 0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04);
  --apple-shadow-md: 0 4px 12px rgba(0,0,0,0.06), 0 2px 4px rgba(0,0,0,0.03);
  --apple-shadow-lg: 0 12px 40px rgba(0,0,0,0.08), 0 4px 12px rgba(0,0,0,0.04);
}
\`\`\`

### 2.2 Dashboard 色彩（独立配色）

| 用途 | 色值 |
|------|------|
| 页面背景 | #F8FAFC |
| 卡片背景 | #FFFFFF |
| 主色 (Primary) | #3B82F6 |
| 成功 (Success) | #10B981 |
| 紫色 (Purple) | #8B5CF6 |
| 橙色 (Orange) | #F59E0B |
| 危险 (Danger) | #EF4444 |
| 边框 | #E2E8F0 |
| 主要文字 | #0F172A |
| 辅助文字 | #64748B |

---

## 3. 排版系统

### 3.1 字体
\`\`\`css
font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Text',
             'Helvetica Neue', 'PingFang SC', 'Microsoft YaHei', sans-serif;
\`\`\`

### 3.2 字号层级
| 用途 | 字号 | 字重 |
|------|------|------|
| 页面大标题 | 28px | 700 |
| 卡片标题 | 13px | 600 |
| 正文 | 13px | 400 |
| KPI 数值 | 32px | 700 |
| KPI 标签 | 12px | 500 |
| 辅助信息 | 11-12px | 400 |
| 按钮文字 | 12-13px | 500 |

### 3.3 行高与字间距
- 默认行高: 1.47059
- 默认字间距: -0.022em
- KPI 数值字间距: -0.03em

---

## 4. 布局系统

### 4.1 整体布局
\`\`\`
┌──────────┬────────────────────────────────────┐
│          │  Header (52px, 毛玻璃)              │
│  Sidebar ├────────────────────────────────────┤
│  220px   │                                    │
│  (可折叠 │  Content (padding: 24px 28px)      │
│   64px)  │                                    │
│          │                                    │
└──────────┴────────────────────────────────────┘
\`\`\`

### 4.2 Sidebar 侧边栏
- 默认宽度: 220px，折叠后: 64px
- Logo 区域: padding 24px 16px 20px
- 导航项: padding 8px 12px，border-radius 6px
- 激活状态: background #0071e3, color white
- 底部折叠按钮: border-top 分隔线

### 4.3 Header 顶栏
- 高度: 52px
- 背景: rgba(255,255,255,0.85) + backdrop-filter blur(20px)
- 底部: 1px solid border

### 4.4 Content 内容区
- padding: 24px 28px 40px
- overflow-y: auto

### 4.5 卡片
- border-radius: 10px (全局) / 12px (Dashboard)
- border: 1px solid #E2E8F0
- padding: 20px 22px
- hover: box-shadow 轻微提升

---

## 5. 组件规范

### 5.1 按钮 (Button)
\`\`\`css
button, .apple-btn {
  height: 32px;
  padding: 0 16px;
  border-radius: 16px;
  font-size: 12px;
  font-weight: 500;
  background: #0071e3;
  color: white;
  transition: all 0.12s ease;
}
.apple-btn-outline {
  background: transparent;
  border: 1px solid #e8e8ed;
  color: #1d1d1f;
}
\`\`\`

### 5.2 输入框 (Input)
\`\`\`css
.apple-input {
  height: 34px;
  padding: 6px 12px;
  border-radius: 8px;
  border: 1px solid #e8e8ed;
  font-size: 13px;
  transition: border-color 0.12s;
}
.apple-input:focus {
  border-color: #0071e3;
  box-shadow: 0 0 0 3px rgba(0,113,227,0.12);
}
\`\`\`

### 5.3 标签 (Tag)
\`\`\`css
.apple-tag {
  display: inline-flex;
  padding: 2px 10px;
  border-radius: 20px;
  font-size: 11px;
  font-weight: 500;
  background: #f5f5f7;
  color: #6e6e73;
}
\`\`\`

### 5.4 KPI 卡片 (Dashboard)
- 4 列网格: grid-template-columns: repeat(4, 1fr)
- 间距: gap 24px
- 内边距: 20px 22px 0
- 底部 Sparkline: height 65px, 100% 宽度
- 渐变填充: 与图标颜色一致

### 5.5 表格 (Data Table)
- 使用 Naive UI NDataTable 组件
- Naive UI 覆写: border-radius 10px

### 5.6 图表 (Charts)
- 使用 ECharts 6 + vue-echarts
- 词云: echarts-wordcloud (圆形布局)
- 饼图: 环形样式 (radius: 45%-70%)
- 折线图: 平滑曲线 + 渐变填充
- 通用: 不显示网格线、坐标轴标签浅灰色

### 5.7 词云 (Word Cloud)
- 形状: circle
- 字体大小范围: 12px ~ 36px
- 旋转: 0° (不旋转)
- 颜色: 10 色循环
- Hover: 加粗放大

### 5.8 知识图谱 (Graph)
- 使用 Cytoscape.js
- 布局: spherical (立体球形)
- 节点: 小圆点
- 连线: 浅灰色
- 标签: Hover 时显示

---

## 6. 页面路由

| 路径 | 名称 | 组件 | 说明 |
|------|------|------|------|
| / | Dashboard | views/dashboard/Index.vue | 总览仪表盘 |
| /knowledge | Knowledge | views/knowledge/Index.vue | 知识库列表 |
| /knowledge/:id | KnowledgeDetail | views/knowledge/Detail.vue | 知识详情 |
| /graph | Graph | views/graph/Index.vue | 知识图谱 |
| /search-log | SearchLog | views/search-log/Index.vue | 搜索日志 |
| /database | Database | views/database/Index.vue | 数据库管理 |
| /analytics | Analytics | views/analytics/Index.vue | 统计分析 |
| /mcp | MCP | views/mcp/Index.vue | MCP 服务配置 |
| /settings | Settings | views/settings/Index.vue | 系统设置 |

---

## 7. 动画规范

| 元素 | 动画 | 时长 |
|------|------|------|
| 卡片 Hover | translateY(-2px) + box-shadow | 0.15s-0.2s ease |
| 侧边栏折叠/展开 | width transition | 0.25s ease |
| 按钮 Hover | background-color | 0.12s ease |
| 输入框 Focus | border-color + box-shadow | 0.12s ease |
| 页面切换 | opacity fade | 0.15s ease |
| 词云入场 | cubicOut easing | 600ms |

---

## 8. 响应式断点

| 断点 | 说明 |
|------|------|
| >1200px | 桌面端：4列KPI，2列内容 |
| 640-1200px | 平板：2列KPI，单列内容 |
| <640px | 手机：单列全宽 |

---

## 9. 滚动条样式

\`\`\`css
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #d1d1d6; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #aeaeb2; }
\`\`\`
