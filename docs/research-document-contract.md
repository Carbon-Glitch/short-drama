# 文档契约与影视词库编辑调研

2026-11-26。仅调研，未修改应用或文档格式。

## 当前实查

- `director-desk/backend/store.py` 已用 SQLite 保存结构化实体、依赖、版本、事件与快照。无需重新选择数据库架构。
- `documents.py` 从实体渲染文档；外部文件通过 `document_sync.py` / `storyboard_sync.py` 差异合并到导演台副本，不能把界面编辑误称为自动改写外部原件。
- `library.py:fields` 用单行正则提取字段；实测 `- 运镜：先推近` 后另起缩进行“再侧移到听者”，运镜字段只有“先推近”。续行可能留在补充正文，但语义归属丢失。
- `StoryboardSync.specs` 仅识别 SHOT 编号标题。实测 `## 镜头一` 返回零镜头，而非明确报错。
- `agent_worker.py` 已传入 Skill 和项目上下文，并要求 JSON 输出；但外层 schema 中 operations_json 是字符串。结构化外壳不等于逐类型业务字段校验。
- `store.py:_validate` 核对实体类型、关联存在性及循环等，尚不足以定义完整的镜头字段契约。
- `web/src/main.jsx` 已有景别机位、运镜等编辑字段，适合增设字段旁词库按钮。

## 建议

固定身份 ID、章节类型、字段键、引用、数值单位和格式版本；保留动作、设计、声音等长文本表达。草稿允许缺项，标明缺口；阶段完成和生产提交使用各自完整性校验。不能把所有阶段变成固定长度表格。

建立一份可执行字段定义，派生 Markdown 模板、解析/渲染、表单与 Agent 操作契约。纯 Skill 项目继续写规范 Markdown；导演台内部继续以实体存储为权威。旧文件按版本和明确别名规范化；未知标题或漏解析必须显示诊断，保留原文，不静默丢条目。外部原件同步继续显式处理。

镜头摄影字段逐步拆为景别、角度、构图、光学、运动序列及自由补充；兼容旧 camera 字符串，无法可靠拆分时留为原文，不猜。词库选中项有稳定 ID、中文名、英文别名、自写解释、目标字段与来源。

交互从字段旁“选择”展开搜索面板：常用项优先、专业项折叠、自绘图示/动画、保留自由输入。选择景别只替换景别，不能覆盖机位与光影；运动可按先后组合并设置起止、速度和触发。场景/全片 Look 与单镜摄影分层。生成前展示最终正文，不把器材名当作服务真实支持的参数。

必要验收：多行字段保留；未知镜头标题提示；旧格式可导入；界面改景别保留其他叙述；错误 Agent 字段不写入；文档往返保留 ID、正文与引用；缺参考画面不强制生图。

## 外部依据

- [JSON Schema 对象约束](https://json-schema.org/understanding-json-schema/reference/object)：字段类型、required 和 additionalProperties 可用于结构约束；创意质量仍需单独判断。
- [StudioBinder 可配置分镜列表](https://www.studiobinder.com/blog/shot-lists-complete-customization-intuitive-interface/)：按景别、类型、运动与器材选择；借鉴分类与渐进展开，不照搬页面或图片。
- [Boords 多种分镜视图](https://boords.com/docs/storyboard-views)：列表和视觉视图适合服务不同编辑任务；不据此要求每镜生成参考图。

实施顺序：先修契约与导入反馈；再做景别/角度/运镜选择；再扩光学、布光、摄像机与胶片 Look。术语资料见同目录 research-cinema-term-picker.md。
