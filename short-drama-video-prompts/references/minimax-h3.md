---
target_video_model: minimax-h3
api_scope: video-generation
official_checked_at: 2026-09-07
metadata_reviewed_at: 2026-11-24
---

# MiniMax H3 提示词方言

只在目标档案明确写 `target_video_model: minimax-h3` 时使用。推荐档案：

```json
{
  "target_video_model": "minimax-h3",
  "video_prompt_dialect": "minimax-h3",
  "video_prompt_language": "en",
  "native_duration_seconds": {"min": 4, "max": 15},
  "supported_generation_modes": ["text", "first_frame", "first_last_frame", "reference"],
  "audio_generation": "same_pass"
}
```

H3 的结构字段用英文；这不等于把中文对白翻成英文。每句中文对白保持原文并写成
<d>[Chinese] 逐字台词</d>，由稳定说话人 ID (S1)、(S2) 引出；声音 ID 与 full-reference 的 <Subject N> 是不同概念。不要在对白前增加外语、语气词或未写入剧本的开场句。
点名 MiniMax H3 只选定模型与方言，不表示创作者选了文生视频。当镜头需要人物、场景、道具或起始构图一致性时，
先按主 Skill 完成真实图片发现与缺口列表。有任何必要图片仍缺失时，不因 H3 同时支持 Base 模式就默默改用文生视频。

## Base / 首帧 / 首尾帧

文生视频、首帧和首尾帧使用三段结构：
```text
integrated_multimodal_description: [Shot 1] <Visual medium, optical lens & aesthetic tone>. ...
overall_soundscape: ...
non_diegetic_music: ...
```

integrated_multimodal_description 在 [Shot 1] 开篇即用一两句锁定影像媒介/胶片或画材性格、光学透视、局部光色秩序与防塑料护栏（而非空洞写“photorealistic”），随后展开空间左右站位、画面、动作、说话人、逐字对白和同步声音；单镜也保留 [Shot 1]。
后续切镜用 [Shot 2] At 00:03.500, the camera cuts to ...，时间递增且落在本次生成时长内。实测表明这种显式时间码切镜能显著提升切点精度与原生音轨层次；交付要求精确时仍需检查实际切点并在剪辑中调整，观察见[OBS-H3-OTHER](model-observations.md#obs-h3-other)。
overall_soundscape 汇总环境声、物理音效和非语言人声，不重复对白；对白事件留在上面的主时间线。
无非画内配乐时写 non_diegetic_music: N/A，不要留空让模型补乐——这一条有实测支撑，见[无对白镜](#无对白镜)；有明确配乐设计时写清器乐、情绪曲线与动态。
首帧模式从输入帧的可见姿态开始；首尾帧模式只改变 1–2 个核心维度（姿态、光影显露或表情转换），在清晰路径内到达上游已接受终点，不强行跨度太大导致生硬变形。

### 首帧与首尾帧的对齐句

Base 文生直接以 integrated_multimodal_description 开始，不加图片对齐句。首帧和首尾帧把对应的对齐句放在三段式正文之前，后空一行：
首帧（I2VA）：
```text
For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.

integrated_multimodal_description: [Shot 1] ...
overall_soundscape: ...
non_diegetic_music: ...
```

<Picture 1> 就是 0.00 秒的真实开场，属于 [Shot 1]。先沿用其中的风格、主体、构图和空间锚点，再写后续动态与光影流动。
首尾帧（FL2VA）：
```text
How the reference pictures align with the target video — Picture 1 (from Shot 1) aligns with the 0.00-second mark of the target video; Picture 2 (from Shot 1) aligns with the 8.00-second mark of the target video.

integrated_multimodal_description: [Shot 1] ...
overall_soundscape: ...
non_diegetic_music: ...
```

两张图分别负责开场和终点。正文写中间可见路径与光影/焦点转换，而不是把两张静图各复述一遍；终点秒数按本镜已接受时长填写。
FL2VA 优先用单镜连续变化，只有分镜已经明确多切时才写多个 [Shot N]。

## 无对白镜

在 overall_soundscape 写清全镜的环境声、音效或静默。
craft_default：优先描述需要的声轨；必要时可以补「无对白」，不因用了否定句判错。
人物嘴部状态按实际表演写，不能把无对白一律改成全程闭嘴。
无非画内配乐时保留 non_diegetic_music: N/A。小样本中省略这一层出现过额外配乐，
显式写空可作为 H3 的默认写法，不保证所有生成都遵守。
时间线总结只列本镜实际存在的声音层，不照抄包含对白的模板。

## 选哪一种模式

模式由本镜「输入参考图」里各槽位的 用途 决定，不由“想不想用多模态”决定：
| 本镜绑定的图 | H3 模式 | 正文结构 |
|---|---|---|
| 没有图，且创作者已明确选择文生视频 | Base（文生） | 三段 |
| 只有一张 用途：起始帧 | first_frame | 三段 |
| 一张 用途：起始帧 + 一张 用途：结束帧 | first_last_frame | 三段 |
| 其他任何组合（起始帧与人物/地点/道具/定调风格图同时存在，或只有人物/地点/道具图） | reference（full-reference） | 六段 |
REF-... 和 PLAN-... 在这张表里同权：模式由 用途 组合决定，与图片此刻在不在项目里无关。
创作者在 H3 的网页界面里自己挂图时，正文照这张表写，顺序 就是他挂图的次序。
H3 官方另有只给尾帧、由模型推断开场的 L2VA 模式。本套件不使用它：开场由分镜已接受的起点决定，
把它交给模型推断会让 SHOT-... 的起点失去权威。因此 结束帧 只在同时绑定 起始帧 时出现。
第四行是最常见、也最容易写错的一种。H3 的首/尾帧输入与参考输入互斥，所以「起始帧 + 角色板 +
场景板」不能拆成 first_frame 加 reference_image：整组统一走 full-reference，起始帧也以
reference_image 送入，正文按下面的标签编号引用。用哪一种模式在《视频提示词.md》里由 用途 组合读出，
不写进「生成方式」字段——该字段仍只有「文生视频」和「图生视频」两个值。

## Full-reference

任何 reference_image、reference_video 或 reference_audio 进入任务时，改用六段结构，段名和正文说明均用英文：
```text
subject_definitions: ...
summary: ...
retention_analysis: ...
detailed_description: ...
overall_soundscape: ...
non_diegetic_music: ...
```

这六段是一条提示词，一次整体提交。 它们是当前实际提交的 MOTION-... 或 GROUP-... 正文，从第一段到最后一段
一起放进那一次生成的提示词框，不是六次生成、也不是只提交第一段。三段结构的 Base / 首帧 / 首尾帧同理。
逐镜路线一镜一条正文；多镜路线整组一条正文，成员 MOTION 只保留审查依据。几个镜头装进同一次生成的条件见
[多镜容器](#多镜容器主体参考默认逐切关键帧按需)。

### 六段各自回答什么

subject_definitions：只在这里完整定义一次 Subject/Picture/Video/Audio 及其职责；后文复用同一标签，不重新定义。
summary：以方括号任务类型（如 [reference generation]）开头，再用一句话概述目标。按需使用 keyframe completion、reference generation、video editing、video continuation、audio reuse、audio reference，多项用 + 连接。
retention_analysis：逐项写该素材在哪一切生效、保留哪些职责，以及保留强度。如果挂载了专门的「风格/影调定调代表图」，用 weak_reference 或 attribute_transfer 明确声明仅提取其色彩秩序、光比反差与光学肌理，绝不继承图中无关动作。
detailed_description：开篇先用 1～2 句立住成像载体与光学性格（如 35mm Kodak Vision3 / 大画幅自然景深与柔和滚落 / 二维手绘墨线与纯平涂色块）、剧组色盘与局部光影性格，以及针对性防塑料/防均质光护栏；随后写 [Shot 1]（多镜用 [Shot 2] At 00:xx.xxx, the camera cuts to ... 衔接），写清左右空间站位、构图层次、核心动作、动态受光、说话人与同步声音。
overall_soundscape：只汇总环境底声、物理音效和非语言人声，不重复逐字对白。
non_diegetic_music：只写观众听到的配乐；没有则写 N/A。
视觉素材的保留强度：
| 标记 | 什么时候用 |
|---|---|
| fully_preserved | 该标签声明的身份、构图、地理、形制或效果全部保留 |
| partially_preserved | 主体沿用，但允许部分外观、光影调整或状态/动作变化 |
| attribute_transfer | 只把特定属性（如整体光色影调、材质肌理或运镜规律）迁移到当前画面 |
| weak_reference | 只借风格、类别、构图或氛围基调，不要求逐项复现 |
音频素材的保留强度：
| 标记 | 什么时候用 |
|---|---|
| fully_copy | 原音轨完整作为最终音轨 |
| partially_copy | 复制部分时段或声层，再增删或替换其他声音 |
| reference | 只参考音色、节奏、语言内容、音效质地或连续性，不复制原信号 |
| weak_reference | 只借大致类别或氛围 |
这些标记只描述素材职责，不证明生成结果已经保持一致；生成后仍要逐镜检查。

### 素材标签怎么编号

正文用 <Picture N>、<Video N>、<Audio N> 指向本次 job 的实际素材，<Subject N> 指向可复用的可见内容。
编号按同类素材在本镜「输入参考图」里的 顺序 递增：第 1 张图片是 <Picture 1>，第 2 张是 <Picture 2>，
视频和音频各自从 1 开始。生产端 compiler 按同一顺序附加引用契约，所以文档里手写的编号必须和 顺序 一致。
因此写 full-reference 正文前，先把本镜的槽位按 顺序 列一遍，例如：
```text
REF-SHOT-START（顺序：1；用途：起始帧）  -> <Picture 1>
REF-XIAOYU-SHEET（顺序：2；用途：身份）  -> <Picture 2>
REF-STUDY-PLATE（顺序：3；用途：地理）    -> <Picture 3>
```

这份清单不依赖文件路径，只依赖 顺序 和 用途，所以图片由创作者自己挂载时它照样成立：
把上面的 REF- 换成 PLAN-，定位符换成 SHOT-... 或 IMG-...，正文一个字都不用改。
PLAN-... 的图套件没有看过，所以 subject_definitions 和 retention_analysis 写的是
这张图按它的 用途 必须保留什么，事实取自《视觉设定.md》和当前文本分镜；已选关键帧时再沿其边界，不把安排写成对像素的观察结论。不要因为图没进项目就改写成「未验证」或省略保留强度。
subject_definitions 把每个主体绑到它的标签上，句式为
<Subject 1> is the ... in <Picture 2>, with ...；retention_analysis 逐条写保留强度和出现的镜次，每个标签在六段里保持同一写法，不留下没有定义的标签。

### 每张图带什么、不带什么

用途 决定这一张在正文里被要求保留什么，具体到哪几项由该槽位自己写下的 控制 范围决定。
需要保留构图时，在 控制 中点名构图、站位或机位高度。不得控制 记录不应照搬的内容。本镜没有起始帧时，地点图会把景别拉宽，要在 detailed_description 里写具体取景与景别比例，见[目标模型能力档案](target-model-profile.md#参考条件方式)。
起始帧 只锚定开场构图与姿态，身份 锚定这个人跨镜不变的长相与体态，地理 只锚定空间结构，风格定调 只锚定色彩秩序、光比质感与画风基调，造型状态 只锚定服装与损污。把这条差异写进 retention_analysis，不要让白底角色板把平光带入成片，也不要让场景板固定死了所有景别。
角色始终使用同一个说话人 ID；中文对白只出现在 <d>[Chinese] ...</d> 内；画内需清晰读出的招牌或文字用英文双引号 "" 包裹。禁字幕写进可见文字约束，与获准的画内文字分开。

## 调度展开深度：高信噪比表达，拒绝机械灌水

Ref2VA 生成任务的 detailed_description 建议按镜头复杂度控制在约 180–420 英文词（多镜或对白密集段落可适当展开，单镜克制戏不必硬凑到 500 词）。绝不能为了凑字数把短短几秒拆成“拇指抬起、掌心下压、指节弯折”之类的呆板人体工学清单——把宝贵的模型注意力留给以下真正决定影视质感的维度：
| 维度 | 需要落到正文的具体关系 |
|---|---|
| 视觉载体与护栏 | 成像格式/画幅性格（如 35mm 胶片、变形宽银幕或纯平涂二维墨线）、暗部纹理与高光滚落性格、针对性防塑料/防均质光边界 |
| 空间左右与留白 | 明确主体在画面左/右/前后景站位（防串位）、镜头态度、景别尺度反差与有呼吸感的负空间留白 |
| 人物、停顿与听者 | 触发 → 清晰可辨的关键微表演或克制停顿 → 听者反应与视线落点；保留半拍情绪余韵 |
| 单一干净运镜与焦点 | 单镜尽量只给一个干净清晰的主运镜或锁定静止（勿同镜混杂多套冲突运镜），写明焦点起止与转移条件 |
| 光影事件与色阶分离 | 局部动机光源方向与衰减（不染脏全片）、动态光斑/阴影移动、主体与材质各自独立的明度色阶 |
| 声音与节奏分层 | 声学演法描述、物理音效触点、环境底声退让与极静停顿；显式 At 00:xx.xxx 切镜营造快慢节奏对比 |
| 出口与邻镜 | 最后定格姿态、目光、双手/持物、方向与可剪出口 |

## H3 执行模型：镜头、参考与声音一起落地

H3 不是只收画面描述的模型。写提示词时同时决定：素材负责什么、镜头怎样变化、人物怎样表演、声音落在哪个动作或切点上。导演分析留在正文外；可复制正文只保留能指导生成的事实。

### 画面与表演

重要情绪按景别和人物选择可见反应：触发 → 接收 → 眼神/呼吸/手/重心微变 → 落点；宁用精准一拍胜过塞满十个碎动作。
动作写接触、方向、落点和身体配合，避免复杂动作脱节成木偶；同时利用环境风声、光影微动、空气微尘保持画面活人感与空间可信度。
多主体同框必须在正文前段锁死左右相对位置与朝向（on the left / on the right / facing each other），避免 H3 生成过程中发生人物位置对调或背影串联。
结合[场景视听调度](../../short-drama/references/film-craft-core.md#场景生命注意转移与声画节奏)主动运用声画先后、遮挡揭示、焦点交接与动静反差；画内需要清晰呈现的文字与标识用英文双引号 "" 包住原文。

### 运镜的语言

运镜用自然英文动作句写 motion type + amplitude + speed；单镜内部尽量只执行一个明确主运镜（或清晰时间分段后切换），不要在同一短镜内连环叠加推、摇、绕、晃导致画面失稳：
```text
The camera pushes in slowly with small amplitude toward the folded letter in her hands.
The camera pans right swiftly with large amplitude, revealing the sunlit doorway.
The camera holds a locked static shot as the runner exits the frame.
```

常用类型：Zoom In/Out、Push In/Pull Out、Pan Left/Right、Truck Left/Right、Tilt Up/Down、Pedestal Up/Down、Arc Shot、Tracking Shot、Static Shot、Shake Slightly/Strongly、POV、Roll Clockwise/Counterclockwise。

### 素材与标签

Subject 是可复用的内容单元，Picture 是具体帧或构图锚点，Video 管整段编辑/续接/时间结构，Audio 管复制或参考声音。一个 Subject 可由多份素材共同定义。
每个标签只在 subject_definitions 完整定义一次，后文沿用；保留范围由 用途 和控制边界决定。
<Picture N> 用于真实开场、关键帧、尾帧、构图或定调风格母版；只负责人物身份的图片不必另建 Picture 条目，直接写进对应 Subject。
<Video N> 不只因为“这是一段视频”就产生 video editing 或 video continuation；直接编辑或续接时才使用。
<Audio N> 与 <Video N> 各自独立编号，不暗示一一配对。
说话人 ID 按目标视频实际发声顺序分配并复用；<Subject N> (Sx) 同时保留人物与说话身份。<Audio N> 绑定说话人时沿用同一个 (Sx)，不另起编号。

### 声音时间线

说话人第一次出现时，在 <d> 外交代画内/画外、声线质感、语速、口音及真实的情绪声学演法（如低声耳语、冷笑微顿、克制微颤）；<d> 内只保留原语言与原台词。
画外音用 says in an off-screen voiceover，并在对应 <d> 后写人物嘴唇闭合；能安排背身或出画时优先用构图解决。
跨切对白用 <scenetrans> 并明确声音连续；真正有意截断才用 <cutoff>。
物理音效跟随接触和动作，明确环境声退让或骤停的留白时点。

### 多镜容器：主体参考默认，逐切关键帧按需

几个相邻镜头可以装进同一次 full-reference 生成，成员时长之和在 4–15 秒内，容器算术按[交付形态](delivery-profile.md)核对。
默认路线：主体参考＋文本分镜。 人物、场景和关键道具以 <Subject N> 复用，各切的景别跳切反差、左右站位、动态光色与 [Shot N] At 00:xx.xxx, the camera cuts to ... 切点在 detailed_description 中写清，summary 通常使用 [reference generation]。
精确逐切路线：关键帧锚点。 切点、构图或状态需要更严格控制时，为对应切提供已接受关键帧。容器用一份参考清单，各切关键帧按切序在前，共用主体图在后，<Picture N> 按实际清单顺序编号。正文在 subject_definitions 前写对齐句：
```text
<Picture 1> aligns with the 0.00-second mark as the opening frame of [Shot 1]; <Picture 2> aligns with the 3.00-second mark as the frame of [Shot 2]; <Picture 3> aligns with the 6.00-second mark as the frame of [Shot 3].
```

detailed_description 的切点与对齐句一致，retention_analysis 说明每张关键帧负责哪一切，summary 可加入 keyframe completion。

## 素材数量上限与出图成本节奏

一次生成最多 1 张首帧、1 张尾帧、9 张 reference_image、3 段 reference_video、3 段 reference_audio；
视频与音频每段 2–15 秒，且各自合计不超过 15 秒。分辨率取 768P 或 2K（MiniMax-H3-Max 另为 480P/768P）。
推荐工作节奏：新方向探索或复杂走位先用 768P 快速验证调度与光影是否成立，定稿后再 2K 生成精修交付。超过素材上限时在分镜阶段按重要性取舍，并写明放弃了哪些参考，不在正文里假装它们仍然生效。
需要精确开场且尚无起始帧图片时，可由 $short-drama-produce 从 分镜.md 的 SHOT-... 冻结关键帧生成，拿到真实文件后由分镜 owner 绑成 用途：起始帧 的 REF-...；或者由创作者把该镜的冻结关键帧正文复制到自己的工具里出图，本轮先记成 PLAN-...（用途：起始帧）、定位符写本镜 SHOT-...。
输入参考图 只登记参考图片。连续段的实际视频不写进这个字段；当前内置 creator-first 生产选择器尚不能绑定续接视频，投产时按[交付路线的接口边界](delivery-profile.md#从已生成结果续接)停靠，不把视频路径塞进图片 REF-...。

## 连续段

先按[模型与接镜](../../short-drama/references/model-aware-coverage-and-joins.md)决定是否真的需要同镜续段。H3 分段默认优先设计自然切镜或动作匹配切；单帧承接描述真实动作阶段与运镜惯性。下述双输入仅用于已启用视频参考的执行端，本机 RunningHub 空视频槽策略照常保留。
H3 的首/尾帧模式与 full-reference 模式互斥，不能在同一请求混用 first_frame/last_frame 和
reference_image/reference_video/reference_audio。连续段需要上一段实际视频和实际尾帧时，统一走 full-reference：
上一段实际视频：reference_video，正文称 <Video 1>，控制动作、节奏和声音连续；
该视频的实际尾帧：reference_image，正文称 <Picture 1>，只作为新段开场的可见姿态与构图锚点。

## 时长

默认将同场连贯表演组织为 13–15 秒左右的一次调用，按分镜安排镜内切换、完整动作和反应；短尾段或补拍按需要取短。提交时长沿上游生成安排，实际能力与素材效果共同决定采用。
structural_invariant（执行端契约）：MiniMax-H3 的 duration 必填，为 4–15 的任一整数秒，并非只有 5/10/15 三档。网页界面或 job 的时长设置要与分镜时长和正文终点一致；写在提示词里的秒数不能替代生成设置。短动作完成后按接法安排反应、环境运动或继续中的动作，避免为凑满时长统一停住；超过单次上限时回分镜按接镜方案排调用。本阶段不偷改镜头秒数。
MiniMax-H3-Max 是另一型号：5–15 秒、480P/768P，仅支持文生和首/尾帧，不支持 full-reference。不能把本页 H3 的参考音频路径或 4 秒下限套到 Max。

### 对白容量、说话人绑定与参考音频

craft_default：按 对白预算 先核对完整发声需要多久，再给主时间线安排开口、停顿与落点。口语语言、声线、声学演法与语速描述放在 <d> 外；<d> 内只放语言标签和逐字台词。稳定说话人用 (S1)、(S2)；full-reference 中同时写 <Subject N> (Sx)。小样本语速和截断见[OBS-H3-SPEECH-RATE](model-observations.md#obs-h3-speech-rate)。
无参考音频时，以自然语言交代说话方式、开口 cue、句间停顿和说完后的动作；H3 官方接口未提供独立 speech_rate 参数。同一次生成内，已接受的对白跨切镜时可以用 <scenetrans> 并声明声音连续；<cutoff> 表示视频结束时有意截断发声，只用于剧本已要求的截断。
说话人第一次出现时，在 <d> 外交代画内/画外、声线与情绪演法，台词紧跟可见动作句，不集中列在末尾：
<Subject 1> (S1), the boy on-screen with a clear high voice, speaks softly: <d>[Chinese] ...</d>。
台词期间画里还有别人的正脸时，明确那个人不说话：
The messenger does not speak; his lips remain completely closed.（观察见[OBS-H3-LIP-SYNC](model-observations.md#obs-h3-lip-sync)）。
有配音或参考音频时：先测实际发声与停顿再定镜长。只参照音色/情绪用 reference（会重新表演本镜台词）；整轨原样复用用 fully_copy；复用部分声层再加环境音用 partially_copy。参考音频走 full-reference，配合至少一张参考图或一段参考视频（每段 2–15 秒，最多三段、合计不超过 15 秒），不能与 first_frame/last_frame 混用。

## Ksr 高级镜头机制与真实案例启发（按镜头需要选用）

起幅即运动中：动作、追逐、灾难或连续航拍可从事件中段开始，硬切对齐方向、速度层级与地平线高度。
全遮挡变换：旧状态可见 → 实体完整遮挡 → 遮挡物离开 → 新状态完整揭示（只在完全不可见时换装/形态）。
分阶段特效：先兆异常 → 轮廓负形 → 材质结构落实 → 主体稳定 → 环境响应。
摄影机的物理反应：起步稍迟、短暂跟丢、焦点迟滞或单次受击震动，写清触发与修正，不加均匀伪抖动。
打斗接触与代价：建立空间左右 → 攻击路径 → 接触受力与环境反馈，逐步升级代价。
参考实测经验（Official FL2VA 雨伞 / EvoLink VTuber、眼镜、耳机、汉堡）：
首尾帧负责两端，正文写中间路径：避免复述两张静图，重点写驱动状态转变的中间力与光影运动；
多图严格分权：身份 / 界面 / 房间 / 风格各司其职，屏内精确文字用白名单（引号锁定）防伪字；
真实感来自具体的光学载体、节奏跳切和物理反馈，绝不来自空泛的“高级感”堆词。

## H3 生成前质检（preflight）


模式与素材组合是否匹配：Base、首帧、首尾帧、full-reference 是否没有混用？

I2VA/FL2VA 是否有首行对齐句，帧与镜头、终点秒数是否对应？

六段是否完整，标签是否只定义一次，Subject/Picture/Video/Audio（含风格母版）是否各自承担正确职责？

detailed_description / [Shot 1] 开篇是否锁定了成像载体/画幅光学性格、局部光色分离与防塑料护栏？

多主体镜头是否显式写死了左右相对位置与朝向？单镜内是否避免同时堆叠多种冲突运镜？

画面是否有清晰呼吸感、可见动作（而非凑字数手部体操）、真实反应与终点，而不是剧情摘要？

说话人 ID 是否稳定，<d> 前是否有恰当的声学演法，逐字对白是否只出现一次，画外音与闭嘴/背身安排是否一致？

环境声、物理音效和配乐是否分层，静音、停顿、At 00:xx.xxx 切镜与跨切声音是否明确？

BGM、字幕、引号内画内精确文字、来源事实和连续性等必要边界是否准确？

## 常见问题与局部修复

| 问题 | 优先检查 | 修复方向 |
|---|---|---|
| 画面像廉价网剧或有塑料CG感 | [Shot 1] 开篇载体与护栏、照明方式 | 开头补足光学载体/胶片或画材介质、抬升暗部细节、局部动机光源与“no plastic CGI sheen”护栏 |
| 人物左右位置对调或串脸 | 空间站位描述与素材数量 | 在镜首明确写出“A on the left, B on the right”及各自朝向，精简无关素材 |
| 切点漂移或意外乱切 | 时间码写法、单镜运镜数与逐切关键帧 | 用 [Shot N] At 00:xx.xxx, the camera cuts to ... 显式标定；每镜保留单一主运镜；必要时补逐切关键帧 |
| 口型落到别人脸上 | 正脸竞争与说话人绑定 | 优先让非说话者背身或出画；否则明确其不说话、嘴唇闭合 |
| 多余配乐或声音嘈杂 | 声音层是否缺失或重复 | 写全底声与物理音效，配乐写 N/A，对白只留在主时间线 |
| 台词赶、断或重复 | 发声窗口与切点 | 按完整原句重算容量，调整镜长、拆镜或减少竞争动作 |
| 动作跳过、卡顿或人偶感 | 动作密度是否过载 | 砍掉凑字数的机械微动作，保核心戏剧动作与稳定重心 |
| 画面假、人物与环境分离 | 光照与接触面 | 补局部光源对人物的照度衰减、反光及接触阴影 |
| 参考图把景别拉宽 | 地点图职责与具体取景 | 地点图只管地理（partially_preserved），在正文明确景别和留白比例 |
| UI 伪字或屏内内容错乱 | 文字引号锁定与屏层职责 | 精确字符用英文双引号 "" 白名单锁定，分开实拍层、屏内内容和 HUD 层 |

### Context-IR 的作用

H3-Context-IR 把多模态输入增强成结构化提示词，本身不生成视频，且仍要求调用方先给出 4–15 秒的 duration。它不能代替[对白预算](performance-action-timing.md#对白预算)。若执行端使用该服务，检查增强后的逐字台词、声音时间线、成像载体基调与原时长一致，不因使用官方增强就跳过容量检查。

## 官方与社区依据（2026-09-07 核对官方，2026-11-24 结合实测迭代校准）：

[Base 提示词指南](https://github.com/MiniMax-AI/MiniMax-H3/blob/main/skills/h3-prompt-writing/references/base-en.txt)：对白位置、说话人、语速描述、切镜时间戳与跨镜发声。
[Full-reference 指南](https://github.com/MiniMax-AI/MiniMax-H3/blob/main/skills/h3-prompt-writing/references/ref-en.txt)：六段结构、音频引用与复用语义。
[视频生成 API](https://platform.minimax.io/docs/api-reference/video-generation-v2-create)：必填时长、型号差异和输入模式互斥。
[官方 CLI 的 H3 指南](https://github.com/MiniMax-AI/cli/blob/main/skill/h3-video/references/h3-video.md)：音频配合视觉参考，声音对齐与生成后检查。
[Context-IR API](https://platform.minimax.io/docs/api-reference/video-generation-v2-h3-context-ir)：提示词增强和独立的时长输入。
[官方功能示例](https://platform.minimax.cn/docs/guides/video-prompt)：品牌、剧情、UI 与多模态真实输入输出示例。
[EvoLink 真实提示词库](https://evolink.ai/zh/minimax-h3-prompts)：带生成结果的公开案例拆解。

## 成像设计进入正式正文（修正前后期边界）

默认读[成像风格与感官质感](../../short-drama/references/image-look-and-finishing.md)。从视觉设定与分镜选定的生成职责出发，必须把 80% 决定作品高级感的光学性格、暗部层次、剧组色盘分离、局部动机光影与材质响应直接烧录进 detailed_description / integrated_multimodal_description 的生成正文里。
制作分工中的后期工程负责最终统一调色、精准剪辑接点与成片 LUT 级微调，但绝不能以“后期会调色”为理由让前端 H3 生成画面退回平庸均质的大平光。比较完整正式正文和真正请求字段，确认选定设计没有只留在解释段。