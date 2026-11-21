---
name: short-drama
description: 统筹短剧制作，剧本后接视觉创意与场面设计，再推进资产图、分镜、生成与 OpenFilm 后期；按实际产物与设计版本接续任务。
license: MIT
---

# 短剧创作路由

## 创作目标与默认阅读

先把画面设计得漂亮、独特、有想象力，再以角色行为、表演和剪辑兑现故事。先读[共同创作方式](references/viewer-first.md)和[影视工业核心](references/film-craft-core.md)，以及本阶段核心知识：

- [创作流程](references/creator-workflow.md)
- [主动美术与视觉结构](references/visual-structure-and-art-direction.md)

- [成像风格与感官质感](references/image-look-and-finishing.md)

手艺资料：[按问题查影视工业知识](references/craft-knowledge.md)。先用本地资料，遇到方法或接口缺口再定向联网。

本阶段核心资料按当前任务读取；同轮已读未变的内容复用，接口与故障资料用到再查。

本技能负责项目初始化、跨阶段路由、制作形态与 Dashboard。各阶段正文由对应技能完成。

## Quick Start

当前创作统一使用 [creator-first 工作流](references/creator-workflow.md)：每集按需维护
`剧本.md`、`视觉设定.md`、`分镜.md`、`图片提示词.md`、`视频提示词.md`，不建立并行的结构化创作真相。
具体写法见 [五份创作文档](references/creator-documents.md)。

## 路由

| 用户要做什么 | owner / 行为 |
|---|---|
| 开发点子、系列承诺、改编和分集地图 | `$short-drama-develop`，仅在用户需要时 |
| 对已有剧情做微创新、换视角或旧内容翻新方案 | `$short-drama-develop`；已选定方案、只改当前单集时直接交 `$short-drama-write` |
| 面向发布的新选题、重大改编、核心反转重设计或新鲜感翻新 | `$short-drama-develop` 先建立或复核现实观众基线，再选方向；明确的单集任务由写作技能直接执行同一原则 |
| 已有多集完整剧本/散稿识别分集 | `$short-drama-develop` 按实际边界建立临时索引 |
| 分析长篇原著 | `$short-drama-novel-analyze`，仅在用户需要时 |
| 写或改单集剧本、改预期差节奏 | `$short-drama-write` → `剧本.md` |
| 视觉创意、美术细化、新调度与情绪节奏 | `$short-drama-design` → `视觉设定.md` |
| 拆资产、安排图种与状态、绑定采用图 | `$short-drama-assets` → 视觉设定的「资产实现」 |
| 写资产图片提示词 | `$short-drama-image-prompts` → `图片提示词.md` |
| 做镜头和冻结关键帧 | `$short-drama-storyboard` → `分镜.md` |
| 写视频/时间线音乐提示词 | `$short-drama-video-prompts` → `视频提示词.md` |
| 实际生成媒体 | `$short-drama-produce`，准备可审阅输入，沿本任务有效授权运行 |
| 把已生产的素材剪成成片 | `$short-drama-edit` → `film.html`、VTT/镜头页与 `制作成果/成片/` |
| 审稿或校验 | `$short-drama-review`；制作内质量判断持续完成，正式审查文档按需 |
| 初始化、Dashboard、归档点名文档 | 本技能 |

`项目开发/` 中的长材料分析与分集索引是可选分析工作区，不参与单集布局判定；写任何一集仍只维护
该集的五份 creator-first Markdown。

现成剧本进入制作时先检查分镜和本次所需实际资产图。缺任一项先执行 $short-drama-design，集中完成视觉与场面设计，再接资产安排、图片和分镜；当前来源已完成设计则复用并补下游缺口。
不要为补齐名义流水线伪造上游。

五份创作文档记录剧本、视觉与提示词；新项目的后期主稿是 OpenFilm 的 `film.html` 与引用文件，剪辑单自动生成。打开创作台使用同一 Studio 的前期面板、素材与时间线；原 Dashboard 仅为未迁移项目保留。
修改故事、镜头职责或上游时长声明时，回到负责该内容的文档。

## 制作入口检查

在本技能目录运行：

    python ../short-drama-design/scripts/design_tool.py inspect <集目录> --project-root <项目根>

按 next_skill 接续；needs_design 为真时先做设计。设计完成记录当前来源版本后，同一缺口不会反复触发设计。剧本、创意设定或制作方向变化时更新设计；资产实现区的图像登记独立接续。只有图片提示词或挂图计划时，实际图像仍视为缺失。

## 执行请求

面向发布的新选题、重大改编和核心反转重设计，现实观众预期校准是方向决策的前置输入，不等用户另提调研。
按[现实观众预期校准](../short-drama-develop/references/audience-expectation-calibration.md)先复核现有证据；缺少适用证据时实际联网研究近期同平台、同类内容和反馈，再决定开场、看点与兑现。
后续写作、分镜、提示词与剪辑沿用已有基线；局部润色和机械执行不重做研究。访问受限或仅做离线草稿时，明确未完成校准及待测假设，不把模型常识包装成当下观众事实。

1. 定位用户给出的项目或资料，只读当前任务的直接输入。
2. 把用户点名的完整范围交给相应技能；批次只控制上下文，自动续跑。
3. 改变用户锁定的故事内核、身份或实质成本时再询问；已授权的视觉探索、参考取舍和方案选择由 Agent 推进。
4. 范围完成后一次回报完成内容、关键决定、真实未决项和可选下一步。
5. 不自动创建用户没点名的审查文档、归档或生产；但用户要求从剧本做到成片时，正常速度观看、回听和交付检查
   是成片闭环的一部分，不能用“未点名审查”跳过。需要正式审查记录时才调用 `$short-drama-review`。
6. 请求横跨视觉设定、图片提示词、分镜或视频提示词时，结束前核对当前已有文档的视觉依赖；
   图片提示词和分镜并行完成时，也要同步两支的引用。每写完一份文档就带 `--partial` 运行跨文档检查，只核对已有文档；五份齐备后再运行完整检查。不为检查补造文件。
7. 视频提示词请求遇到「输入参考图：无」或仍带「待补参考图」时，先路由分镜 owner 检查项目已有图片并刷新绑定。有匹配图就同请求续跑；有必要图缺失就列表停下。
   停下时把三条路一起给出：把已有图片放进项目绑成 `REF-...`；由创作者在自己的工具里出图、本轮先用
   `PLAN-...` 写出逐镜挂图计划并照常产出视频提示词；或者明确改走文生视频。用本套件生产参考图需要项目外的
   adapter 与凭据，只是第一条路的一种做法，不要把它说成唯一入口，也不要只给「生成参考图 / 文生视频」两个选项。
   不把“没有手工指定”当成明确选择文生视频。这一轮如果镜头还缺「视觉依据」，
   同时按已成稿的冻结关键帧回填；两条依据描述同一格画面，不要只补一条。
8. 用户在会话里点名目标视频模型（“按 MiniMax H3 写”“用 Seedance 2.5”）而 `short-drama.json` 的
   `production_profile` 还是 `unset` 时，先把这个选择连同它带来的原生时长、参考方式和正文语言写进档案，
   再继续下游阶段。把已确认选择写入档案，后续请求才能沿用同一方言、语言和时长边界。

## 初始化、Dashboard、配置与交付

按需读取[项目操作、配置与交付](references/project-operations.md)。本入口只保留路由和创作者决策，
不在默认上下文展开命令、档案字段、Dashboard 状态和导出细节。

## 项目级创作决定

沿用用户已定的制作形态、视觉方向、播放面和集长；未定的普通视觉选择由 Agent 主动设计。每个新场景默认做轻量视觉开发与角色入景判断，成熟方向复用；需要比较时展开 Look Development。项目档案、节奏档案和接受状态按[项目操作、配置与交付](references/project-operations.md)
处理，下游只读取已接受值，不把套件默认数值当成质量门槛。

核心知识按默认阅读入口载入；下列索引定位具体问题：

- 规则分级与 owner 路由：[规则与路由索引](references/knowhow-index.md)
- 影视工业优先、导演判断、分遍剪辑、声音、灯光、色彩与精品质量门：[影视工业核心](references/film-craft-core.md)
- 视觉结构、美术叙事、服装陈设与色彩弧：[视觉结构与美术叙事](references/visual-structure-and-art-direction.md)
- 外部资源、官方基准与本机已有影视资料的吸收边界：[资源吸收登记](references/resource-registry.md)
- 输出语言、稳定 ID、所有权与安全边界：[契约与所有权](references/contract-and-ownership.md)
- 实拍、二维、三维、水墨、Q 版、国漫的形态差异：[制作形态](references/production-form-profiles.md)
- 需要比较代表帧时：[Look Development](references/look-development.md)
- 参考图能控制什么：[参考角色](references/reference-roles.md)
- 遮挡、延迟揭示和观众知情时机：[观众揭示](references/audience-reveal.md)
- 母版、补拍和替代版的职责：[补拍与替代](references/pickup-and-alternate.md)

## 影视工业工作模式

单文件或快速任务以当前阶段的创作目标为准，不自动增加导演稿、审查表或后期文档。跨越剧本、分镜、生产、剪辑
到成片的完整请求，默认启用轻量精品路径：先读取[影视工业核心](references/film-craft-core.md)，把工作重心放到
观众体验、表演、摄影、声音、剪辑和实际验收，再按需调用各阶段的 craft reference。只有用户明确要求快速草稿时，
才把验收范围降到“可生成”或“可剪”。

创作质量属于任务完成，不是导出后的加分项。未生成交设计稿；只通过技术检查交已导出预览；实际画面吸引力、关键设计与故事职责已观察成立，再按[质量证据](../short-drama-review/references/quality-ladder.md)报告完成范围。已知关键缺失继续修，听感等不可观察项单独说明。

## 生产与交付边界

生产保留精确预览与记录，按用户对本任务的有效授权运行；持续授权无需重复询问，范围或成本实质扩大再确认。归档与导出见[项目操作](references/project-operations.md)。技术成功不代替作品判断。

## 安装维护

只有安装、升级或排障时运行 `python3 scripts/selftest.py`。
