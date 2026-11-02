---
name: frontend-design
description: Create distinctive, production-grade frontend interfaces with high design quality. Use this skill for UI tasks that build web components, pages, or applications. Generates creative, polished code that avoids generic AI aesthetics.
license: Complete terms in LICENSE.txt
---

Use this skill to design and implement bold, production-ready frontends when the request involves UI. Combine it with the repository's actual UI constraints: `openspec/specs/frontend-typescript-style/spec.md`, `openspec/specs/api-conventions/spec.md`, and the current change's `design.md`（含验收矩阵与 Review Checklist）.

现有项目的组件、样式与用户确认的设计方向优先。当前模板使用 React 19 与
`frontend/src/styles/index.css`，未安装 Ant Design；修改已有页面时沿用这些事实。
只有新页面或用户明确要求重新设计时才选择新的视觉方向，不因本 Skill 自动引入字体、组件库或依赖。

## Design Thinking

Before coding, lock in a clear, memorable direction:
- **Purpose**: What problem does the interface solve? Who uses it?
- **Tone**: Commit to a strong aesthetic (e.g., brutalist/raw, retro-futuristic, editorial/magazine, luxury/refined, playful/toy-like, industrial/utilitarian). Choose one and execute it precisely.
- **Constraints**: Framework, performance, accessibility, build tooling.
- **Differentiation**: What makes this unforgettable? Aim for a single standout idea.

Then build working code (HTML/CSS/JS, React, templ, etc.) that is:
- Production-grade and functional
- Visually striking with a cohesive point of view
- Meticulous in spacing, motion, and detail

## Frontend Aesthetics Guidelines

- **Typography**: Preserve the project's existing font stack and hierarchy. Use new fonts only when the approved design calls for them.
- **Color & Theme**: Define a strong palette with CSS variables; prefer decisive dominance + accents over timid mixes.
- **Motion**: Use meaningful animations (page load, staggered reveals, purposeful hover states). Prefer CSS; keep motion aligned to the chosen aesthetic.
- **Spatial Composition**: Consider asymmetry, overlap, generous negative space or intentional density. Avoid cookie-cutter layouts.
- **Background & Details**: Build atmosphere with gradients, meshes, textures, layered transparencies, dramatic shadows, decorative borders, custom cursors, or grain overlays—matching the aesthetic.

Avoid generic AI-looking designs (purple-on-white defaults, predictable layouts, overused fonts, interchangeable components). Each UI should feel intentionally crafted for its context. Match implementation effort to the chosen style: maximalism demands rich effects; minimalism demands precise restraint.
