---
name: short-drama
description: 以强电影感与鲜明艺术主张统筹短剧创作，将剧本推进为高辨识度的场面设计、分镜、生成与 OpenFilm 后期；按实际产物与设计版本接续任务。
license: MIT
---
# 短剧创作总控
读[共同底线](references/viewer-first.md)与[流程](references/creator-workflow.md)；具体工艺查[知识入口](references/craft-knowledge.md)。
## Quick Start
当前创作统一使用 [creator-first 工作流](references/creator-workflow.md)：每集按需维护
剧本.md视觉设定.md分镜.md图片提示词.md视频提示词.md，不建立并行的结构化创作真相。
具体写法见 [五份创作文档](references/creator-documents.md)。
## 路由
| 用户要做什么 | owner / 行为 |
|---|---|
| 开发点子、系列承诺、改编和分集地图 | $short-drama-develop，仅在用户需要时 |
| 对已有剧情做微创新、换视角或旧内容翻新方案 | $short-drama-develop；已选定方案、只改当前单集时直接交 $short-drama-write |
| 面向发布的新选题、重大改编、核心反转重设计或新鲜感翻新 | $short-drama-develop 先建立或复核现实观众预期与审美疲劳点，再定破局方向；明确的单集任务由写作技能执行同一原则 |
| 已有多集完整剧本/散稿识别分集 | $short-drama-develop 按实际边界建立临时索引 |
| 分析长篇原著 | $short-drama-novel-analyze，仅在用户需要时 |
| 写或改单集剧本、改预期差与节奏张力 | $short-drama-write → 剧本.md |
| 确立强风格视觉主张、美术造型、光影规则、新调度与信息密度 | $short-drama-design → 视觉设定.md |
| 写管理预期、注意力与视听张力的文本分镜、按需关键帧 | $short-drama-storyboard → 分镜.md；资产与提示词前按 $short-drama-review 做导演体验审读 |
| 拆高辨识度最小主体资产、安排参考与绑定采用图 | $short-drama-assets → 视觉设定的「资产实现」 |
| 写主体资产与按需控制图片提示词 | $short-drama-image-prompts → 图片提示词.md |
| 写视频/时间线音乐提示词 | $short-drama-video-prompts → 视频提示词.md |
| 实际生成媒体 | $short-drama-produce，准备可审阅输入，沿本任务有效授权运行 |
| 把已生产的素材剪成成片 | $short-drama-edit → film.html、VTT/镜头页与 制作成果/成片/ |
| 审稿或校验 | $short-drama-review；制作内质量判断持续完成，正式审查文档按需 |
| 初始化、Dashboard、归档点名文档 | 本技能 |
项目开发/ 中的长材料分析与分集索引是可选分析工作区，不参与单集布局判定；写任何一集仍只维护该集的五份 creator-first Markdown。
现成剧本进入制作时先检查分镜和本次所需实际资产图。设计缺失或来源实质变化时执行 $short-drama-design；当前设计有效时，缺分镜接分镜、缺实际图接资产与图片提示词，不因缺产物重选设计。默认用高辨识度的核心主体资产配合全能参考定向生成，代表图和逐切关键帧按实际控制需要补充；**不得以“试生成”名义妥协造型与光影定调**，也不要为补齐名义流水线伪造上游。
五份创作文档记录剧本、视觉与提示词；新项目的后期主稿是 OpenFilm 的 film.html 与引用文件，剪辑单自动生成。打开创作台使用同一 Studio 的前期面板、素材与时间线；原 Dashboard 仅为未迁移项目保留。
修改故事、镜头职责或上游时长声明时，回到负责该内容的文档。
创作与下游改进权限只沿[共同创作底线](references/viewer-first.md)；设计拥有策略选择，下游可改善实现，重大变化回写来源。

## 影视工业与审美决策标准
局部任务做好眼前这一场；从剧本做到成片时，沿[影视工业核心](references/film-craft-core.md)把强风格设计真正烧录进前端素材，再到目标画幅看听成片。快速草稿按用户指定范围交付。
### 核心创作决定

创作目标、概念发明与视觉/节奏菜单由[设计技能](../short-drama-design/SKILL.md)统一维护，本入口只负责路由。段长与分组沿[统一策略](references/model-aware-coverage-and-joins.md)，模型语法读所选方言。项目明确选择记录于 short-drama.json；不把建议配方当通用门槛。

### 三重审读与质量证据闭环
剧本先首看，分镜先审体验，整集再复核。
1. 剧本首看：整集剧本完成、进入设计前，宿主支持子 Agent 时派一个未参与创作的只读子 Agent 只读剧本，报告首次接收、人物相处、何处拖与情绪落点；不支持子 Agent 时由主线程按同一范围单独阅读，并明确标为“作者自检”，不得冒充独立首次观众。具体发现交写作 owner 原位修订后再进入设计。
2. 分镜体验与美学审读：分镜后、资产与提示词前按[导演体验审读](../short-drama-review/SKILL.md#分镜后的导演体验审读)检查期待、兑现、注意力、**视听冲击力与风格锐度**，结论交设计或分镜原位修订。
3. 整集复核：整集收尾同样优先派独立只读子 Agent 读五份文档与已有媒体，核对相邻状态、文字产生、clip 容量和参考承接；不支持时由主线程复核并标明作者自检。局部单场或单文件修改不启用子 Agent；不另建审查文档。
阶段接续由主 Agent 依次加载对应 Skill；使用子 Agent 时给它一个明确阶段或审查任务，完成后回本路由，避免把整条链递归嵌套进同一个 Skill 调用。
创作质量属于任务完成，不是导出后的加分项。未生成交设计稿；只通过技术检查交已导出预览；**实际画面高级感、核心视觉主张与故事张力已观察成立**，再按[质量证据](../short-drama-review/references/quality-ladder.md)报告完成范围。已知关键缺失或美学平庸处继续修，听感等不可观察项单独说明。
### 工艺与设计参考索引
核心知识按默认阅读入口载入；下列索引定位具体工艺问题：
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
---
## 执行请求协议
面向发布的新选题、重大改编和核心反转重设计，现实观众预期校准是方向决策的前置输入，不等用户另提调研。
按[现实观众预期校准](../short-drama-develop/references/audience-expectation-calibration.md)先复核现有证据；缺少适用证据时实际联网研究近期同平台、同类内容和反馈，**识别观众的真实痛点与已看腻的套路**，再据此确立反差突围的开场、看点与兑现方案。
后续写作、分镜、提示词与剪辑沿用已有基线；局部润色和机械执行不重做研究。访问受限或仅做离线草稿时，明确未完成校准及待测假设，不把模型常识包装成当下观众事实。
1. 定位用户给出的项目或资料，只读当前任务的直接输入。
2. 把用户点名的完整范围交给相应技能；批次只控制上下文，自动续跑。
3. 改变用户锁定的故事内核、身份或实质成本时再询问；已授权的**大胆视觉探索、风格化造型、参考取舍和方案选择**由 Agent 果断推进。
4. 范围完成后一次回报完成内容、关键美学/叙事决定、真实未决项和可选下一步。
5. 不自动创建用户没点名的审查文档、归档或生产；但用户要求从剧本做到成片时，正常速度观看、回听和交付检查是成片闭环的一部分，不能用“未点名审查”跳过。需要正式审查记录时才调用 $short-drama-review。
6. 请求横跨视觉设定、图片提示词、分镜或视频提示词时，结束前核对当前已有文档的视觉依赖与参考绑定。每写完一份文档就带 --partial 运行跨文档检查，只核对已有文档；五份齐备后再运行完整检查。不为检查补造文件。
7. 视频提示词请求遇到「输入参考图：无」或仍带「待补参考图」时，先路由分镜 owner 检查项目已有图片并刷新绑定。有匹配图就同请求续跑；有必要图缺失就列表停下。
   停下时把三条路一起给出：把已有图片放进项目绑成 REF-...；由创作者在自己的工具里出图、本轮先用 PLAN-... 写出逐镜挂图计划并照常产出视频提示词；或者明确改走文生视频。用本套件生产参考图需要项目外的 adapter 与凭据，只是第一条路的一种做法，不要把它说成唯一入口，也不要只给「生成参考图 / 文生视频」两个选项。
   不把“没有手工指定”当成明确选择文生视频。这一轮如果镜头还缺「视觉依据」，同时按当前文本分镜或已选关键帧回填，确保依据描述同一画面。
8. 用户在会话里点名目标视频模型（“按 MiniMax H3 写”“用 Seedance 2.5”）而 short-drama.json 的 production_profile 还是 unset 时，先把这个选择连同它带来的原生时长、参考方式和正文语言写进档案，再继续下游阶段。把已确认选择写入档案，后续请求才能沿用同一方言、语言和时长边界。
## 工程监测、门禁与交付边界
### 导演台实时监测
在本机新开或接续自动制作时，先用 python scripts/dashboard_server.py --workspace <项目根> 登记监测；加 --open 给导演打开同一座台。任何 Agent 的落盘产物均可监测。进入阶段、采纳关键调整或等待返修时，用 python scripts/director_signal.py <集目录> --actor <实际执行者> --stage <阶段> --change 开始|调整|完成|等待|返修 --message "本次决定" [--artifact 本集相对路径] 留一条简短回执。不同设备共享或同步同一项目目录（含 .short-drama/progress）即可接续；云端无本机工具时按[导演台](references/director-desk.md)写同格式回执。
### 制作入口检查
在本技能目录运行：
    python ../short-drama-design/scripts/design_tool.py inspect <集目录> --project-root <项目根>
导演台的「到此等我」与返修意见跟随本集。进入下一创作阶段前，运行 python scripts/director_desk.py gate <集目录> <集号> <阶段>（开发／剧本／Design／分镜／资产／投产／回片／剪辑／交付）；返回 waiting 时保留产物，待导演放行后接续。用 director_desk.py state <集目录> 读取当前版本意见与已选参考再返修。实际生产沿 production_tool 提交。
按 next_skill 接续needs_design 为真时先做设计。设计完成记录当前来源版本后，同一缺口不会反复触发设计。剧本、创意设定或制作方向变化时更新设计；资产实现区的图像登记独立接续。只有图片提示词或挂图计划时，实际图像仍视为缺失。
### 初始化、配置、生产与安装维护
- 配置与交付：按需读取[项目操作、配置与交付](references/project-operations.md)。本入口不在默认上下文展开命令、档案字段、Dashboard 状态和导出细节。
- 生产与交付边界：生产保留精确预览与记录，按用户对本任务的有效授权运行；持续授权无需重复询问，范围或成本实质扩大再确认。技术成功不代替作品判断。
- 安装维护：只有安装、升级或排障时运行 python3 scripts/selftest.py。修改创作规则后，按[Skill 版本对照评估](references/skill-evaluation.md)比较同输入下的实际输出与读取成本；该评估不进入创作默认加载，也不冒充媒体实测。