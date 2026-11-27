---
name: short-drama-video-prompts
description: 将分镜与真实参考精准转译为 Seedance 2.5、MiniMax H3 等目标模型的高可执行视频提示词；以物理动作预算、参考权责隔离与两步编译保证成片质感与工具合规。
license: MIT
---

# 视频与时间线音乐提示词

把已确认分镜与真实参考编译为《视频提示词.md》。每镜保留 MOTION 与 SHOT 对应；多镜正文只写 GROUP，成员不重复展开。

## 1. 最小读取与接续

读取当前场次的视觉设定、分镜（含生成安排/接镜）、准确对白来源，以及命中的一套模型方言。Seedance 2.5 读方言与执行模型，H3 读 H3 方言；排障时再加载专项参考，不先通读全库。

设计有效时直接补下游缺口，不因缺图重做设计。控制路线沿[分镜路线分流](../short-drama-storyboard/SKILL.md#生成路线分流)，段长与分组沿[统一策略](../short-drama/references/model-aware-coverage-and-joins.md)。本阶段不擅自更换路线、时长、对白或已接受参考职责。

真实 REF 可编译投产输入；PLAN 可交可复制正文但不能冒充本机可提交素材；待补时先找项目现有图，再按[备图边界](../short-drama-assets/SKILL.md#备图边界)判断是否真缺生产输入，普通全能参考不因缺单镜画面停工。明确选择文生时写全静态锚点。字段、路径、编号与 GROUP 格式沿[提交正文规范](references/submit-entry-format.md)。

## 2. 通用目标

- 声音在叙事时序上紧贴触发动作，说清说话人、听者与声源；具体字段位置与标签只服从目标方言。
- 每句逐字对白在一个提交正文中出现一次，并来自当前剧本；声音概述不再次抄写台词。
- 描写与参考图的当前状态一致，把篇幅用在表演、摄影、动态光影与声音变化，不重复无关静态细节。
- 对动作和发声预算负责，拥挤时回分镜调整；不把复杂调度机械压成固定动作数量。
- 质感与屏幕图形/文字分工沿[通用成像配方](../short-drama-image-prompts/references/common-recipe.md)。后期文字只在说明区保存原文，生成正文正向描述预留承载面，不用带引号的待合成文字或否定句再次触发该文字；此限制不禁用合法对白和真正需要画内生成的文字。

## 3. 先导演起稿，再合规编译

### 阶段 A · 导演起稿

若分镜遗漏本场关键设计，或只附效果名却没有触发与可读画面，先在原 SHOT 补齐过程再编译；不在视频正文里另造一版与分镜脱节的戏。

文件项目可运行 `python ../short-drama/scripts/creator_context.py <集目录> --shots <SHOT编号…>` 取得完整原文切片；导演台按关联自动提供同类上下文。

编译一个 GROUP 时读取完整成员镜头、关联 DESIGN 原文、场次共用设定和必要邻镜状态。保留观看顺序、听者反馈、声画触发与实际操作过程；仅合并重复的公共描述。

落实本镜的起点、表演转向、构图/焦点、动态受光、声画触发、终点及接续。保住选定表达，改进与回写沿[共同创作底线](../short-drama/references/viewer-first.md)。出口可以继续运动，不默认定格等切。导演理由留在说明区，正文写可见可听事实。

### 阶段 B · 工程合规编译

提交前按[导演自查](../short-drama-review/references/director-self-check.md)检查字面画面、参考职责与动作容量。

按命中方言转换结构、素材标签、对白与时间语法，不混用模型模板。核对输入模式、素材编号、字段、参考职责、逐字引文、容量与引用完整性；已有检查器负责能机械验证的部分，尚未覆盖的规则按方言清单人工核对，不宣称自动保障。

连续性锁按现有契约继承。续接仅在所选入口支持、真实前段输入就绪时可提交，具体输入条件由方言规定；普通切镜不强制续接。正文不放内部ID、本地路径、审批或检查结论。

## 4. 完成与交接

每个实际提交单元只有一份完整正文，所选设计、表演、声音与相邻状态均可追溯。运行现有跨文档 partial 检查，五份齐备后完整核对；文本通过不代表媒体质量通过。

本技能不调用生成服务；转生产准备精确 job 并沿任务有效授权执行。时间线音乐仅在明确要求时增加区间、功能、进退与动态，歌词来自用户提供或接受的文本。只需静态关键帧和配音的任务可直接接生产预览。

## 按需查阅索引（仅遇对应问题时加载）

- **主力模型方言（二选一默认读）**：
  - Seedance 2.5：[Seedance 2.5 方言](references/seedance-2.5.md) + [2.5 执行模型](references/execution-model-25.md)
  - MiniMax H3：[MiniMax H3 方言](references/minimax-h3.md)
- **其他模型方言**：[Seedance 2.0](references/seedance-2.0.md) ｜ [Wan 3.0](references/wan-3.0.md)
- **接口与交付格式**：[提交正文规范](references/submit-entry-format.md) ｜ [目标模型能力档案](references/target-model-profile.md) ｜ [交付形态](references/delivery-profile.md)
- **专项排障与规范**：[运动配方](references/motion-recipe.md) ｜ [表演导演](references/performance-direction.md) ｜ [表演与动作时序](references/performance-action-timing.md) ｜ [摄影与声音连续性](references/camera-audio-continuity.md) ｜ [可生成性](references/generability.md) ｜ [审查与示例](references/review-and-fixtures.md)
