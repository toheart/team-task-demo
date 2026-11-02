---
name: antd-design-system
description: 已采用 Ant Design 的 React 管理台组件与主题规范。仅在 frontend/package.json 已声明 antd，或当前设计已明确批准接入 antd 时使用；不适用于默认的普通 CSS 模板。
---

# Antd Design System

## 适用前提

当前 starter 使用 React 19 + TypeScript + Vite，样式在 `frontend/src/styles/index.css`，
没有安装 `antd` 或 `@ant-design/icons`，也没有固定的主题目录。

使用前先读 `frontend/package.json`、实际的主题装配代码和本次 `design.md`。
未采用 antd 时跳过本 Skill，沿用现有组件与 CSS；不要为了满足 Skill 自动安装依赖。
例如默认首页使用 `<button>` 与 CSS class，不改成不存在的 `Button` 或 `ConfigProvider`。

## 已采用 Ant Design 时

- 以项目安装版本的 API 为准，不假定 antd 大版本或 React 版本。
- 通过代码搜索定位现有 `ConfigProvider`、主题 Token 与布局，不假定 `src/theme/index.ts` 存在。
- 沿用项目已有主色、圆角、字体与间距。简单样式按现有做法写；媒体查询与伪类使用 CSS。
- 表单通过 `Form.Item` 展示字段错误；提交期间禁用重复提交并显示 loading。
- 表格按数据量决定固定表头、分页与操作列，不给短列表强加固定布局。
- Modal/Drawer 关闭后清理状态；错误反馈说明原因与下一步；空状态提供可用操作。
- 图标复用已安装的图标库，不自动引入第二套库。
- 保留语义化元素、键盘操作、可见焦点；图标按钮提供 `aria-label`。

## 避免

- 引用代码库中不存在的主题或组件路径。
- 为一次局部变更替换全局字体、颜色或布局。
- 为每个操作设置 primary；一个操作区只突出主要动作。
- 嵌套 Modal 或层层嵌套 Card；复杂操作使用已批准的页面或 Drawer 流程。

实际入口从 `frontend/src/App.tsx`、`frontend/src/components/` 和
`frontend/src/styles/index.css` 开始搜索。主题与组件选择有冲突时返回本次设计，不自行选择。
