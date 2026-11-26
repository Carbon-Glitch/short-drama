---
name: short-drama-assets
description: 从视觉设计与文本分镜拆解高质感、可复用的最小人物、造型、场景、道具及定调代表图资产，科学拆分参考职责并严审后登记实际采用图片。
license: MIT
---

# 最小主体资产与参考安排

摊开《视觉设定.md》和文本分镜，挑出下一镜还得一眼认出的核心视觉锚点：这个人鲜明的骨相神态与造型、这间屋子独有的光影与空间秩序，或那件会改变局面的关键道具。**这里的资产图直接决定下游视频模型的像素上限**——既要精准可控，更要先把全片的高级质感立住。手艺查[身份与变体](references/identity-vs-variant.md)、[连续性](references/continuity-lock.md)和[知识入口](../short-drama/references/craft-knowledge.md)。

## 接续

分镜或实际资产图缺失时先按[设计阶段](../short-drama-design/SKILL.md)检查；当前设计完成后先形成文本分镜，再按各镜可见需求安排资产。

## 做法

1. **筛选必画资产与关键状态**：从设计重点和各镜画面挑两类参考：跨镜要认得出的主体，以及一旦画错、这场戏就失去意味的关键状态。后者即使只出现一次，也值得先画；日常普通物件随人物或场景入图。
2. **按实际消费需求拆资产**：人物身份、一次Look、场景空间与道具状态分清；角色肖像、全身、空景视角、细节或定调代表图按真实缺口制作，不机械配套。路线沿[分镜分流](../short-drama-storyboard/SKILL.md#生成路线分流)，质感与屏幕图形处理只按[通用成像配方](../short-drama-image-prompts/references/common-recipe.md)。
3. **写清复用与控制契约**：在「## 资产实现」简记 IMG 项、对应设计、用途、状态和复用范围。为每张图点名用处与不控制项：哪一镜靠它认人，哪一镜靠它锁空间，哪处变化值得另做一个状态。
4. **返图检查与采用**：生产返回后按设计重点与[通用成像配方](../short-drama-image-prompts/references/common-recipe.md#8-完成与真实图像检查)检查；记录实际采用版本，再绑定REF。PLAN仍只是挂图计划。

5. **主动用好定调代表图与按需控制图**：
   - **风格/构图代表图（影调母版）**：强风格作品、高反差美学或仅凭中性角色/场景板难以让视频模型稳住高级影调时，主动安排 1～2 张代表图锁死全片色彩与光影气场，也用于新方向比较；
   - **细节与关键帧**：微小关键状态不稳补细节图；某一切构图或时间点失控补该切关键帧。补充素材针对当前问题制作，不预先盲目扩展全套。
6. **双向修正闭环**：出图若暴露出造型太俗、空间平庸等设计问题，直接回《视觉设定.md》升级造型方案；采用图刷新后同步更新分镜、视频提示词与生产绑定。

## 完成

本次生成所需主体资产（及必要的影调定调代表图）、用途、控制边界和引用明确，采用图真实存在且视觉质感过关（或有可执行的 `PLAN`）。后续补充图片由实际生成问题触发，直接接续视频提示词与生产。

格式见[五份文档](../short-drama/references/creator-documents.md)、[参考角色](../short-drama/references/reference-roles.md)，完成判断见[资产检查](references/asset-review-checklist.md)。

按问题查[地点与视角](references/location-and-view.md)、[道具与状态](references/prop-and-state.md)、[连续性变化](references/continuity-delta.md)、[时代特征](references/era-anchors.md)；从长剧本找复用对象时查[出场提取](references/occurrence-extraction.md)。
