---
name: short-drama-edit
description: 在同一 OpenFilm 工程中完成短剧初剪、精剪、声画联动、字幕与成片交付；用户和 Agent 共同编辑 film.html，沿用 short-drama 前期与生产路线。
license: MIT
---

# 短剧剪辑与成片

## 创作目标与默认阅读

先把画面设计得漂亮、独特、有想象力，再以角色行为、表演和剪辑兑现故事。先读[共同创作方式](../short-drama/references/viewer-first.md)和[影视工业核心](../short-drama/references/film-craft-core.md)，以及本阶段核心知识：

- [前期情绪兑现](references/editorial-intent.md)
- [精剪手艺](references/finishing-craft.md)
- [声音与音乐叙事](references/sound-narrative-and-music.md)

- [工程 Look 执行](references/look-execution.md)
- [成像风格与感官质感](../short-drama/references/image-look-and-finishing.md)
- [按模型排生成段与接镜](../short-drama/references/model-aware-coverage-and-joins.md)

手艺资料：[按问题查影视工业知识](../short-drama/references/craft-knowledge.md)。先用本地资料，遇到方法或接口缺口再定向联网。

本阶段核心资料按当前任务读取；同轮已读未变的内容复用，接口与故障资料用到再查。

从实际表演决定剪点，让前期的预期、触发、反应与兑现落在观众真正看到和听到的时刻。先读[前期情绪到实际剪法](references/editorial-intent.md)；精修手艺默认读取[精修手艺](references/finishing-craft.md)。

## 一份后期主稿

新项目使用 `film.html`、引用的 VTT 与镜头页。Studio 与当前 Agent 修改同一份工程；`剪辑单.md` 自动生成供阅读。剧本、视觉设定、分镜及两份提示词继续拥有前期创作事实。

1. 完整制作先按设计阶段 inspect 接续分镜与实际资产图缺口；读五份前期文件中与本次剪辑有关的职责，观察实际素材、真实对白和动作窗口。听不了时用已有语音时间、波形与能量辅助，明确仍需回听的判断。
2. 承接分镜「生成安排／接镜」与真实出口记录，区分自然切镜、动作匹配、同镜续段与有意转场。从表演选源窗、镜序和听者反应，写稳定 CUT ID、SHOT/MOTION 来源与取舍。重要对白、接触、揭示和兑现绑定真实源区间。
3. 在工程中安排独立声音、J/L cut、BGM 与逐句字幕，明确演员原声、现场声、旁白、音乐与静默各自承担什么。音乐按情绪选真实曲段，关键反应前给停顿、呼吸和接触声留位置。
4. 打开短剧创作台精修。每轮先读当前版本，写清本轮变化与冻结部分；保留人工样式、锁定轨道和已经成立的声音/字幕关系，独立设计的错位照常保留。
5. 自由试剪并连续预览，检查对白、反应、声音归属、音乐和字幕。预览自动附带接点回看页；先正常速度看接点前后，再按需逐帧定位重复/冻帧、动作重启、光色或声音台阶。优先调整源窗、覆盖与声画匹配，表演或身份缺失再回生产。交付前用 `handoff` 对照前期事项，`bind-handoff` 指向实际承载层；有意省略写明创作理由。工具跟踪缺项和上游变化，OpenFilm 只渲染一次正式版。

## 采用与声画返修

换配音、改速度或剪点时，同步检查已烘焙的口型、发声指示、机械动作与听者反应。关键兑现用实际源时间窗和观察简记，复用 events/制作记录；handoff 只证明有承载层，不证明事件被看见。找不到有效源窗就补覆盖或返修该段。先完成可观察修复，缺听感证据时交待验收预览。

## 执行

从本技能目录相对调用：

```sh
python scripts/edit_tool.py init <剧集目录>
python scripts/edit_tool.py open <剧集目录>
python scripts/edit_tool.py plan <剧集目录>
python scripts/edit_tool.py preview <剧集目录>
python scripts/edit_tool.py render <剧集目录>
python scripts/edit_tool.py verify <剧集目录>
```

首个真实剪辑用 seed JSON 初始化，后续使用带版本的补丁。大胆决定剪法、转场与声音，把交接对账交给工具；字段、素材更新、音频处理与迁移见[工程接口](references/openfilm-workflow.md)。初始化/打开时自动部署固定版本的隔离 OpenFilm 运行时。

素材生产仍由 `$short-drama-produce` 和项目已有 H3/imagegen 路线负责。当前 Agent 做写作、分析与审美判断；素材测量、节拍、波形与音频处理复用本地 helper。OpenFilm 独占新工程的预览和最终混音/渲染。

旧项目没有 `film.html` 时保持原执行路线。用户选择迁移后，导入独立副本；旧格式按需读[旧工程工作流](references/legacy-edit-workflow.md)。复杂图形转成可编辑镜头页，特殊效果注明实际保留范围。
