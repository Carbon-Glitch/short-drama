# 资源吸收登记

资源进入短剧技能前，先记录它改变的制作决策、适用范围、授权/版本和本机验证结果。这里登记入口和吸收边界，
不复制外部教程、书籍或提示词原文。当前入口核对日期：2026-11-10；模型、站点功能、价格、授权和第三方 skill
状态变化时重新核对。

“已转化”表示已形成按需技巧卡，不表示全书/全站已读完或未来媒体效果已验证。“公开分析已核对”与
“实际媒体已看听”分开记录；没有生产观察的内容保持方法参考或待验证。

## 流程与技术基准

2026-11-16 补充核验短剧分镜/选镜/剪辑/声音与调色相关skills；固定提交、采纳与不采用项见
[分镜与后期吸收记录](../../short-drama-edit/references/absorbed-editing-skills.md)。
执行增量为FFmpeg六工具子集与原生CUT/SHOT对照，非重装整套外部流程；语义与审美仍以实际声画验收。

| 来源 | 吸收方向 | 进入方式 |
|---|---|---|
| [Blackmagic Design DaVinci Resolve Training](https://www.blackmagicdesign.com/products/davinciresolve/training) | Edit、Color、Fairlight 的阶段顺序、练习问题和交付检查 | 转成 `short-drama-edit` 的后期决策卡；不搬整套软件教程 |
| [Academy Color Encoding System（ACES）](https://docs.acescentral.com/) | 色彩管理、跨工具/跨输出的一致性边界 | 转成颜色空间、look、接镜和导出检查；不把 LUT 当叙事方案 |
| [OpenTimelineIO](https://github.com/AcademySoftwareFoundation/OpenTimelineIO) | 镜头、片段、时长、来源和外部剪辑工具的时间线交接 | 作为外部剪辑/多镜容器的交换参考；不替代当前 Markdown 真相 |
| [Dolby Creator Lab](https://www.dolby.com/creator-lab/) | 声音与画面共同承担叙事、创作者听审与交付意识 | 转成声音导演和成片回听问题；不设固定声轨数量 |
| [Netflix Timed Text Style Guide](https://partnerhelp.netflixstudios.com/hc/en-us/articles/215758617-Timed-Text-Style-Guide-General-Requirements) | 字幕持续、断行、位置与可读性 | 只进入对应交付档案，不设为所有项目的统一规范 |
| ITU-R BS.1770 / EBU R128 | 响度与真峰测量参照 | 数值按项目交付目标；不能代替对白清晰度和实际回听 |

## 已转化的创作方法

2026-11-16 通读用户提供的 `trend-aware-plot-twist` 主skill与四份reference，选择性吸收：
现实观感与剧情预期分开、群体/证据边界、完整预期差链、半步探索、逐拍四类节奏和反馈失败判读。
新增[观感、预期与半步探索](../../short-drama-develop/references/audience-expectation-calibration.md)，并融入既有
微创新、[预期差节奏](../../short-drama-write/references/expectation-rhythm.md)、分镜/剪辑交接与首次观看审查。
未复制其固定样本量、三方向/三版本配额、默认整套调研、独立节拍表或第二份主剧本；来源skill本体保留原样，
short-drama引用为自包含的方法转译，不依赖另一skill的安装或执行。

2026-11-23 通读用户提供的 `老唐电影级分镜skill-s10至臻版_v3` 主 skill、21 份参考、回归夹具与预览脚本，
选择性吸收同源审阅视图、章节级加载、长对白改例、反打光照推导、画外承受、非人表达通道、整组段界和版本对照。
新增[完整声画调度预览](../../short-drama-storyboard/references/storyboard-preview.md)与[Skill 版本对照评估](skill-evaluation.md)，
其余增量原位进入分镜和接镜资料；未采用强制确认、固定话术、规则编号导航、镜头/时长/景别配额或统一表演与亮度公式。
本机已验证真实 CLI、离线自检和链接；外部回归夹具未被当作媒体效果证据，本套件也未执行本轮媒体生产。
原始 skill 保持原样，short-drama 不依赖其安装或执行。其许可证未随包声明；本次只转译机制并重写表达与工具，未复制其模板和代码。

| 方法来源 | 按需技巧卡 | 吸收边界 |
|---|---|---|
| Judith Weston《Directing Actors》；Michael Rabiger《Directing: Film Techniques and Aesthetics》；《Actions: The Actors’ Thesaurus》 | [表演导演](../../short-drama-video-prompts/references/performance-direction.md) | 行动动词、现场目标、听者、adjustment；沿用人物内核，主动发展具体行为与可读细节 |
| Bruce Block《The Visual Story》；Vincent LoBrutto《The Filmmaker’s Guide to Production Design》；Deborah Nadoolman Landis 服装设计资料 | [视觉结构与美术叙事](visual-structure-and-art-direction.md) | 空间、服装、陈设、道具和色彩关系；不把颜色含义或美术风格当跨项目公式 |
| Michel Chion《Audio-Vision》；David Sonnenschein《Sound Design》；John Purcell《Dialogue Editing for Motion Pictures》；Fred Karlin / Rayburn Wright《On the Track》 | [叙事声音、对白后期与音乐](../../short-drama-edit/references/sound-narrative-and-music.md) | 声源/听者/时间/质感、音乐 spotting、对白和终混；不强制声轨、曲风或插件 |
| Walter Murch《In the Blink of an Eye》；Ken Dancyger《The Technique of Film and Video Editing》；《The Cutting Edge》 | [剪辑决策库](../../short-drama-edit/references/editing-decision-library.md) | 候选剪法、单变量比较和代价；不把某种剪法当高级标志 |
| Richard Williams《The Animator’s Survival Kit》；Ed Hooks《Acting for Animators》；Chris Webster《Action Analysis for Animators》 | [动画与漫剧表演](../../short-drama-storyboard/references/animation-performance.md) | 姿态、重量、时间、口型和次级运动；不把十二原则逐镜填满 |
| Kevin Goetz《Audience-ology》 | [首次观看与观众证据](../../short-drama-review/references/fresh-viewer-review.md) | 独立首看、非诱导提问和样本边界；不把 reviewer 或模型当真实市场样本 |

书目只需按当前问题核对相关章节，可通过图书馆、正版书或公开样章使用；不打包原文，不声称已经吸收整本书。

## 连续片例与视觉参考

| 来源 | 用法 | 边界 |
|---|---|---|
| [Yale Film Analysis: Mise-en-scène](https://filmanalysis.yale.edu/mise-en-scene/)、[Cinematography](https://filmanalysis.yale.edu/cinematography/)、[Editing](https://filmanalysis.yale.edu/editing/)、[Sound](https://filmanalysis.yale.edu/sound/) | 具体场景的空间、美术、摄影、剪辑和声音机制 | 已形成[连续片例库](../../short-drama-storyboard/references/sequence-case-library.md)；当前为公开分析已核对，片内时间码按所用版本另行复核 |
| ShotDeck | 按构图、光色、摄影和美术做单帧视觉方向参考 | 输出“借什么/拒绝什么/如何转译”，不直接抄提示词或图像像素；静帧不能证明连续表演与剪辑 |
| Flim | 从情绪、空间和视觉感觉寻找少量参照 | 参照必须绑定具体可观察机制，不能以标签代替观看 |
| Every Frame a Painting、Lessons from the Screenplay、Criterion/DGA 导演评论、Team Deakins | 连续场面、导演取舍和制作访谈的候选入口 | 只有定位到具体场次/访谈内容并完成当前媒体核对后，才进入正式案例；不凭片名或作者声望吸收 |

## AI 生成评测与生产证据

| 来源 | 用法 | 边界 |
|---|---|---|
| [VBench](https://github.com/Vchitect/VBench) | 身份、背景、闪烁、运动、成像和语义等评测维度 | 已形成[AI 生成风险测试矩阵](../../short-drama-produce/references/generation-test-matrix.md)；不复制权重或总分 |
| [T2V-CompBench](https://github.com/KaiyueSun98/T2V-CompBench) | 属性、空间、运动、动作、物体交互和数量等组合能力 | 只按当前镜头风险选测；不替代表演、剪辑、声音和精品判断 |
| 实际生产观察、失败记录和项目回归 | 当前模型、参考、配置和镜头类型的可复用证据 | 绑定准确输入、提示词、参考顺序、版本、结果与观察方式；不泛化成模型排名 |

## 素材与许可

| 来源 | 用法 | 边界 |
|---|---|---|
| Freesound | 查找环境声、拟音和设计声候选 | 每条素材记录实际许可；不能把素材库规模当质量证据 |
| BBC Sound Effects | 查找档案音效候选 | 使用前核对当前许可范围；不把受限用途写成商用默认 |
| 爱给网及其他音乐/LUT/画面素材库 | 当前项目的声音、音乐或调色对照 | 逐条核对许可、版本和使用区间；LUT 只用于对照，不替代色彩弧 |

## 本机已有参考

`$hypit` 的 `references/creation/` 与 `references/production/` 已有导演、审美、声音、剪辑、后期、
验收和来源边界资料。优先提炼其中的决策问题和失败信号，写入对应 short-drama skill；
不复制 Hypit 的项目文件布局、供应商路径、固定参数或另一套交付状态。

当前重点入口：`creation/sound-direction.md`、`creation/aesthetic-direction.md`、
`production/post-finishing.md`、`production/craft-cases.md`、`creation/drama-method-sources.md`。
其中真实案例的“输入—版本—观察—适用范围—复用方式”用于项目校准，不将其他项目的成功当普遍规律。

## 不作为核心规范的资源

提示词聚合站、外部 skill 目录、无独立证据的评分页、固定镜头配方和单一模型经验只能用于发现候选。
它们进入核心前必须有：真实来源、适用模型/形态、失败边界、本机复现或生产观察，以及明确的许可证。
未满足这些条件时保持“候选/待验证”，不进入默认创作上下文。
