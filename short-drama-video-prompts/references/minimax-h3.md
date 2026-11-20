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
`<d>[Chinese] 逐字台词</d>`，由稳定说话人 ID `(S1)`、`(S2)` 引出；声音 ID 与 full-reference 的 `<Subject N>` 是不同概念。不要在对白前增加外语、语气词或未写入剧本的开场句。

点名 MiniMax H3 只选定模型与方言，不表示创作者选了文生视频。当镜头需要人物、场景、道具或起始构图一致性时，
先按主 Skill 完成真实图片发现与缺口列表。有任何必要图片仍缺失时，不因 H3 同时支持 Base 模式就默默改用文生视频。

## Base / 首帧 / 首尾帧

文生视频、首帧和首尾帧使用三段结构：

```text
integrated_multimodal_description: [Shot 1] ...
overall_soundscape: ...
non_diegetic_music: ...
```

- `integrated_multimodal_description` 按 `[Shot 1]`、`[Shot 2]` 写画面、动作、说话人、逐字对白和同步声音；
  单镜也保留 `[Shot 1]`。第一镜不加切镜时间戳，后续切镜用 `[Shot 2] At 00:03.500, ...`，时间递增且落在本次生成时长内。
  小样本观察到切点接近要求，但仍有偏差；交付要求精确时应检查实际切点并在剪辑中调整。
- `overall_soundscape` 汇总环境声、物理音效和非语言人声，不重复对白；对白事件留在上面的主时间线。
  无非画内配乐时写 `non_diegetic_music: N/A`，不要留空让模型补乐——这一条有实测支撑，见
  [无对白镜](#无对白镜)。
- 首帧模式从输入帧的可见姿态开始；首尾帧模式只能到达上游已接受终点，不发明过渡后的新状态。

### 首帧与首尾帧的对齐句

Base 文生直接以 `integrated_multimodal_description` 开始，不加图片对齐句。首帧和首尾帧把对应的对齐句放在三段式正文之前，后空一行：

- **首帧（I2VA）**：

  ```text
  For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.

  integrated_multimodal_description: [Shot 1] ...
  overall_soundscape: ...
  non_diegetic_music: ...
  ```

  `<Picture 1>` 就是 0.00 秒的真实开场，属于 `[Shot 1]`。先沿用其中的风格、主体、构图和空间锚点，再写后续动作。

- **首尾帧（FL2VA）**：

  ```text
  How the reference pictures align with the target video — Picture 1 (from Shot 1) aligns with the 0.00-second mark of the target video; Picture 2 (from Shot 1) aligns with the 8.00-second mark of the target video.

  integrated_multimodal_description: [Shot 1] ...
  overall_soundscape: ...
  non_diegetic_music: ...
  ```

  两张图分别负责开场和终点。正文写中间可见路径，而不是把两张静图各复述一遍；终点秒数按本镜已接受时长填写。
  FL2VA 优先用单镜连续变化，只有分镜已经明确多切时才写多个 `[Shot N]`。

## 无对白镜

在 `overall_soundscape` 写清全镜的环境声、音效或静默。
**`craft_default`**：优先描述需要的声轨；必要时可以补「无对白」，不因用了否定句判错。
人物嘴部状态按实际表演写，不能把无对白一律改成全程闭嘴。

无非画内配乐时保留 `non_diegetic_music: N/A`。小样本中省略这一层出现过额外配乐，
显式写空可作为 H3 的默认写法，不保证所有生成都遵守。
时间线总结只列本镜实际存在的声音层，不照抄包含对白的模板。

## 选哪一种模式

模式由本镜「输入参考图」里各槽位的 `用途` 决定，不由“想不想用多模态”决定：

| 本镜绑定的图 | H3 模式 | 正文结构 |
|---|---|---|
| 没有图，且创作者已明确选择文生视频 | Base（文生） | 三段 |
| 只有一张 `用途：起始帧` | `first_frame` | 三段 |
| 一张 `用途：起始帧` + 一张 `用途：结束帧` | `first_last_frame` | 三段 |
| 其他任何组合（起始帧与人物/地点/道具图同时存在，或只有人物/地点/道具图） | `reference`（full-reference） | 六段 |

`REF-...` 和 `PLAN-...` 在这张表里同权：模式由 `用途` 组合决定，与图片此刻在不在项目里无关。
创作者在 H3 的网页界面里自己挂图时，正文照这张表写，`顺序` 就是他挂图的次序。

H3 官方另有只给尾帧、由模型推断开场的 L2VA 模式。本套件不使用它：开场由分镜已接受的起点决定，
把它交给模型推断会让 `SHOT-...` 的起点失去权威。因此 `结束帧` 只在同时绑定 `起始帧` 时出现。

第四行是最常见、也最容易写错的一种。H3 的首/尾帧输入与参考输入**互斥**，所以「起始帧 + 角色板 +
场景板」不能拆成 `first_frame` 加 `reference_image`：整组统一走 full-reference，起始帧也以
`reference_image` 送入，正文按下面的标签编号引用。用哪一种模式在《视频提示词.md》里由 `用途` 组合读出，
不写进「生成方式」字段——该字段仍只有「文生视频」和「图生视频」两个值。

## Full-reference

任何 `reference_image`、`reference_video` 或 `reference_audio` 进入任务时，改用六段结构，段名和正文说明均用英文：

```text
subject_definitions: ...
summary: ...
retention_analysis: ...
detailed_description: [Shot 1] ...
overall_soundscape: ...
non_diegetic_music: ...
```

**这六段是一条提示词，一次整体提交。** 它们是同一个 `MOTION-...` 的可复制正文，从第一段到最后一段
一起放进那一次生成的提示词框，不是六次生成、也不是只提交第一段。三段结构的 Base / 首帧 / 首尾帧同理。
默认一镜一次生成，下一镜换成它自己那条完整正文；几个镜头装进同一次生成的条件见
[多镜容器](#多镜容器每切一张关键帧)。

### 六段各自回答什么

- `subject_definitions`：只在这里完整定义一次 Subject/Picture/Video/Audio 及其职责；后文复用同一标签，不重新定义。
- `summary`：以方括号任务类型（如 `[reference generation]`）开头，再用一句话概述目标。按需使用 `keyframe completion`、`reference generation`、`video editing`、
  `video continuation`、`audio reuse`、`audio reference`，多项用 ` + ` 连接。只有直接编辑或续接视频才用后两个视频任务词；
  仅参考运镜、剪辑或节奏时通常是 `reference generation`。
- `retention_analysis`：逐项写该素材在哪一切生效、保留哪些职责，以及保留强度。
- `detailed_description`：按实际播放顺序写画面、动作、运镜、说话人与声音。先给一两句整体风格，再写 `[Shot 1]`；
  这是正文主体，不能退化成剧情摘要或素材关系表。
- `overall_soundscape`：只汇总环境底声、物理音效和非语言人声，不重复逐字对白。
- `non_diegetic_music`：只写观众听到的配乐；没有则写 `N/A`。

视觉素材的保留强度：

| 标记 | 什么时候用 |
|---|---|
| `fully_preserved` | 该标签声明的身份、构图、地理、形制或效果全部保留 |
| `partially_preserved` | 主体沿用，但允许部分外观、状态或动作变化 |
| `attribute_transfer` | 只把特定属性迁移到另一个主体或对象 |
| `weak_reference` | 只借风格、类别、构图或氛围，不要求逐项复现 |

音频素材的保留强度：

| 标记 | 什么时候用 |
|---|---|
| `fully_copy` | 原音轨完整作为最终音轨 |
| `partially_copy` | 复制部分时段或声层，再增删或替换其他声音 |
| `reference` | 只参考音色、节奏、语言内容、音效质地或连续性，不复制原信号 |
| `weak_reference` | 只借大致类别或氛围 |

这些标记只描述素材职责，不证明生成结果已经保持一致；生成后仍要逐镜检查。

### 素材标签怎么编号

正文用 `<Picture N>`、`<Video N>`、`<Audio N>` 指向本次 job 的实际素材，`<Subject N>` 指向可复用的可见内容。
**编号按同类素材在本镜「输入参考图」里的 `顺序` 递增**：第 1 张图片是 `<Picture 1>`，第 2 张是 `<Picture 2>`，
视频和音频各自从 1 开始。生产端 compiler 按同一顺序附加引用契约，所以文档里手写的编号必须和 `顺序` 一致；
两套编号不一致时模型会收到互相矛盾的素材说明，而接口不会报错。

因此写 full-reference 正文前，先把本镜的槽位按 `顺序` 列一遍，例如：

```text
REF-SHOT-START（顺序：1；用途：起始帧）  -> <Picture 1>
REF-XIAOYU-SHEET（顺序：2；用途：身份）  -> <Picture 2>
REF-STUDY-PLATE（顺序：3；用途：地理）    -> <Picture 3>
```

这份清单不依赖文件路径，只依赖 `顺序` 和 `用途`，所以图片由创作者自己挂载时它照样成立：
把上面的 `REF-` 换成 `PLAN-`，定位符换成 `SHOT-...` 或 `IMG-...`，正文一个字都不用改。
创作者按 `顺序` 在生成界面里挂图，`<Picture N>` 就对得上。

`PLAN-...` 的图套件没有看过，所以 `subject_definitions` 和 `retention_analysis` 写的是
**这张图按它的 `用途` 必须保留什么**，事实取自《视觉设定.md》和本镜冻结关键帧，而不是对像素的观察结论。
两种槽位的句式相同：`用途` 决定保留什么，本来就不是看图看出来的。不要因为图没进项目就改写成
「未验证」或省略保留强度——那会让执行端收不到本镜真正的保留要求。

`subject_definitions` 把每个主体绑到它的标签上，句式为
`<Subject 1> is the ... in <Picture 2>, with ...`；`retention_analysis` 逐条写保留强度和出现的镜次，
视觉素材用 `fully_preserved`、`partially_preserved`、`attribute_transfer`、`weak_reference`，
音频素材用 `fully_copy`、`partially_copy`、`reference`、`weak_reference`，例如
`<Subject 1> (appears in [Shot 1]): fully_preserved - 短发轮廓、连帽外套配色与鞋型保留`。
每个标签在六段里保持同一写法，不留下没有定义的标签。

### 每张图带什么、不带什么

`用途` 决定这一张在正文里被要求保留什么，具体到哪几项由该槽位自己写下的 `控制` 范围决定。

需要保留构图时，在 `控制` 中点名构图、站位或机位高度。
`不得控制` 记录不应照搬的内容，生成后仍需检查实际参考影响，不能把文字声明当成模型保证。
本镜没有起始帧时，地点图会把景别拉宽，要在 `detailed_description` 里写具体取景，见
[目标模型能力档案](target-model-profile.md#参考条件方式)。

`起始帧` 只锚定开场构图与姿态，`身份` 锚定这个人跨镜不变的长相与体态（角色板同时固定本集造型时，
`控制` 里会写明），
`地理` 只锚定空间关系，`造型状态` 只锚定服装与损污。把这条差异写进 `retention_analysis`，
不要让角色板顺带决定构图，也不要让场景板顺带决定人物长相。

角色始终使用同一个说话人 ID；中文对白只出现在 `<d>[Chinese] ...</d>` 内。禁字幕写进可见文字约束，
与获准的画内文字分开。
Full-reference 的逐字对白与同步声音放在 `detailed_description` 的对应事件里，`overall_soundscape` 仍只汇总底声与音效。
不要为了“多模态”把所有资产图都带上；每镜只绑定它真正可见且需要保持的起始帧、人物、地点或关键道具图。

### 一个完整例子

分镜里的槽位（三张图：本镜起始帧、角色板、场景板）：

```markdown
- 输入参考图：REF-SHOT002-START（顺序：1）· 剧集/EP001/制作成果/images/SHOT-EP001-002.png《SHOT-EP001-002 起始帧》（用途：起始帧；控制：起始构图、男孩坐姿与桌面位置；不得控制：尚未发生的动作、终态）；REF-XIAOYU-SHEET（顺序：2）· 输入/参考图/小雨定妆.png《小雨定妆照》（用途：身份；控制：脸型、发型剪影、身高比例；不得控制：构图、动作、表情）；REF-STUDY-PLATE（顺序：3）· 输入/参考图/家庭书房.png《家庭书房场景图》（用途：地理；控制：书桌方位、书架墙、灯位；不得控制：人物身份、动作、道具状态）
```

对应的完整8秒单镜示意（`生成方式：图生视频`，模式为 `reference`）：假定已确认分镜为男孩翻页发现地图、手指停在地图边缘；开场图与下述姿态、灯位一致。此例仅示范展开精度，不是已生成验收的案例，不将它的剧情、风格或时长套到其他镜头。

```text
subject_definitions: <Subject 1> is the elementary-school boy in <Picture 2>, with a round short black haircut and a light grey-blue hooded jacket over a white inner shirt. <Subject 2> is the home study in <Picture 3>, with the desk against the window wall, a full bookshelf on the left and a warm desk lamp. <Picture 1> is the opening composition of this shot.
summary: [keyframe completion + reference generation] In one continuous eight-second shot, the boy turns a textbook page, notices the printed map and stops his tracing finger at its edge.
retention_analysis: <Picture 1> (appears in [Shot 1]): fully_preserved - overhead framing, desk edge position and the boy's seated placement open the shot exactly as supplied. <Subject 1> (appears in [Shot 1]): fully_preserved - face shape, hair silhouette and the jacket-over-shirt layering stay identical; his pose and expression are set by this shot, not by <Picture 2>. <Subject 2> (appears in [Shot 1]): partially_preserved - desk orientation, bookshelf wall and lamp position are kept; the props on the desk follow this shot.
detailed_description: The target video is photographic live action with natural skin and paper texture. Warm light from the desk lamp falls across the open book; cooler window light separates the boy's sleeve from the darker desktop. Preserve the opening light directions in <Picture 1> as his hands move.
[Shot 1] Begin in the overhead composition anchored by <Picture 1>, with <Subject 1> seated at the desk in <Subject 2>. His head and shoulders occupy the upper part of the frame, the open textbook lies below them, and both forearms remain visible. His left palm rests beside the spine while his right fingertips hold the outer corner of the right-hand page. The desk edge and the lamp base establish stable positions around the book. The camera initially holds still, giving the viewer time to read his hands and the unfinished page turn.
He lifts the corner with his right thumb and index finger and carries the page leftward across the spine. His left fingers briefly rise to let it pass, then settle on the newly turned page to keep it flat. The sheet bends before landing; its moving edge casts a narrow shadow across the opposite page. A dry paper rustle follows the lift and softens as the sheet settles. His shoulders incline toward the book without changing his seated position.
As the printed map becomes visible, his right index finger approaches its outer edge. His gaze follows the finger, then stops ahead of it. The finger slows and comes to rest against the page beside the map rather than continuing across it. His left hand stays on the turned page. A small pause in his breathing and the sudden stillness of the searching hand make the discovery readable from overhead; the shot does not depend on seeing a tiny facial expression.
When his finger slows, the camera begins a gentle physical push toward the book, retaining both hands and the lower edge of his head. The desk edge gradually leaves the frame while the book grows larger; this is a continuous move rather than a cut. Keep the map and fingertip clear together, with the far desk surface becoming softer. End on the stopped fingertip, the open map and the supporting left hand, preserving the quiet pause. No dialogue, non-diegetic subtitles, captions or dialogue text overlays appear at any time.
overall_soundscape: Quiet indoor room tone persists throughout. Paper friction follows the page turn, followed by a light fingertip contact and close natural breathing. The final pause retains room tone without new speech or sound events.
non_diegetic_music: N/A
```

三张图各自只负责一件事：`<Picture 1>` 给构图，`<Picture 2>` 给身份，`<Picture 3>` 给地理。
把这条差异写进 `retention_analysis`，生成后检查身份、构图与地理是否分别保留。

## 调度展开深度：先充分表达，再去重

Ref2VA生成任务的 **detailed_description通常为350–500英文词**，指这一段本身，不是六段总和，也不是每切配额；单镜不自动构成缩短理由。对白密集内容优先容纳完整发声时间线，视频编辑随复杂度调整。这个官方建议不是所有模式或每个短镜的最低词数；短于参考时查是否漏掉有效决定，长于参考时查重复与冲突。

写正文前，在现有分镜内确认本镜实际采用的调度与成像维度，再沿播放顺序合并成自然语言，不新增必填表：

| 维度 | 需要落到正文的具体关系 |
| --- | --- |
| 构图与空间 | 景别、机位/视点、前中后景、人物/道具位置、遮挡及运镜所需起始空间 |
| 人物与听者 | 触发、行动意图对应的行为、身体/持物/接触过程、停顿、听者反应及可见落点 |
| 摄影与焦点 | 起始构图→触发→路径/方向与必要幅度速度→视差/揭示→终点；焦点起止与转移条件 |
| 光源与材质 | 世界光源、软硬/明暗关系、脸和关键物件的受光、移动及接触造成的光影变化 |
| 成像与局部注意 | 透视/景深、柔化/高光扩散、皮肤/织物/水的表面响应、注意中心；用可见结果表达所选 Look |
| 时间与跨镜质感 | 运动模糊、焦点、接触阴影/反射、材质余动随动作连续变化；同场相邻镜沿用共同成像基础 |
| 声音与节奏 | 发声者、时间关系、空间远近、同步接触、停顿底声及声桥；不要重复逐字台词 |
| 出口与邻镜 | 最后姿态、目光、双手/持物、屏幕方向、信息落点和可剪出口 |

积极展开本镜选定的摄影、光影、表演和声音，以情绪、气氛和感官效果决定强度。缺少导演决定时回到分镜补齐，随后把选定方案完整实现。

一个主导戏剧变化可以让人物、听者、摄影机、焦点、光影和声音同时协作；明确先后与并行，避免互斥动作及注意力竞争。参考图可以承载静态身份和基础构图，不能代替转身受光、移动视差、清晰度交接或声音距离变化。

回读最终可复制正文，将上游已选择的每项调度与其实际表达对应：保留“触发→变化→可见/可听结果→落点”。删减先去重复定义、质量口号及无关装饰；保留空间关系、关键反应、动态光照、焦点、声音和终点。合批/整集不应使每镜变成摘要。字数、时间戳和镜头术语都不构成模型精确执行保证。

## H3 执行模型：镜头、参考与声音一起落地

H3 不是只收画面描述的模型。写提示词时同时决定：素材负责什么、镜头怎样变化、人物怎样表演、
声音落在哪个动作或切点上。导演分析留在正文外；可复制正文只保留能指导生成的事实。

### 画面与表演

- 重要情绪按景别和人物选择可见反应：触发 → 接收 → 目光/呼吸/手/重心变化 → 行动落点。
  以景别和情绪目标选择幅度、节奏与身体通道，形成可感知的转向。
- 动作写接触、方向、落点和身体配合。需要时才补稳定件、补偿件和不自主反应，避免只动一个部位。
- 主动检查场景持续状态：已建立的水、空气、机械、人群等是否继续；配角怎样听与反应；接触后衣物、液面、阴影与反射怎样反馈和收束。环境可提供生活感与空间可信度，不限于直接推动情节；主角停下不等于场景全停。
- 写清实际元素、方向/强度、持续或触发条件、与主动作的并行/延迟及落点，组织前后景和声音主次；按观看节奏选择动静、反差和持续活动；需要的环境、资产与声音在现有视觉设定/分镜补全后使用。
- 默认结合[场景视听调度](../../short-drama/references/film-craft-core.md#场景生命注意转移与声画节奏)选择声画先后、遮挡揭示、焦点交接、动静反差或物理余韵。主动组合技巧形成鲜明表达，让固定与运动镜头分别发展画内关系和观看立场。
- 光照写到实际表面：主光方向、照射部位、反射光、阴影来源和材质反射；按景别选择可见细节。
- 主动组织前景、中景、背景和空气层的深度、运动与光影，以场次设计中的具体元素实现画面层次。

### 运镜的语言

运镜用自然英文动作句写 **motion type + amplitude + speed**，需要时才写幅度和速度：

```text
The camera pushes in with small amplitude at slow speed toward the folded letter in her hands.
The camera pans right with large amplitude at fast speed, revealing the open doorway.
The camera holds a static shot as the runner exits the frame.
```

常用类型：`Zoom In/Out`、`Push In/Pull Out`、`Pan Left/Right`、`Truck Left/Right`、`Tilt Up/Down`、
`Pedestal Up/Down`、`Arc Shot`、`Tracking Shot`、`Static Shot`、`Shake Slightly/Strongly`、`POV`、
`Roll Clockwise/Counterclockwise`。推拉机位与变焦不是同一件事，固定机位也要说明它让观众看清什么。
切点必须带来主体、空间、状态、视角或时间的新信息；只改距离或角度时，优先考虑机位内移动。

### 素材与标签

- Subject 是可复用的内容单元，Picture 是具体帧或构图锚点，Video 管整段编辑/续接/时间结构，
  Audio 管复制或参考声音。一个 Subject 可由多份素材共同定义。
- 每个标签只在 `subject_definitions` 完整定义一次，后文沿用；保留范围由 `用途` 和控制边界决定。
- `<Picture N>` 用于真实开场、关键帧、尾帧或构图锚点；只负责人物身份的图片不必另建 Picture 条目，
  直接写进对应 Subject。
- `<Video N>` 不只因为“这是一段视频”就产生 `video editing` 或 `video continuation`；直接编辑或续接时才使用。
- `<Audio N>` 与 `<Video N>` 各自独立编号，不暗示一一配对。普通视频不因为自带声音就自动创建 Audio 条目。
- 说话人 ID 按目标视频实际发声顺序分配并复用；`<Subject N> (Sx)` 同时保留人物与说话身份。
  `<Audio N>` 绑定说话人时沿用同一个 `(Sx)`，不另起编号。

### 声音时间线

- 说话人第一次出现时，在 `<d>` 外交代画内/画外、年龄或声线、语速和口音；`<d>` 内只保留原语言与原台词。
- 画外音用 `says in an off-screen voiceover`，并在对应 `<d>` 后写人物嘴唇闭合；能安排背身或出画时优先用构图解决。
- 跨切对白用 `<scenetrans>` 并明确声音连续；真正有意截断才用 `<cutoff>`。
- 物理音效跟随接触和动作：脚步落地、杯子碰桌、开门、布料、机械、呼吸与停顿各有发生时点。
- 配乐写配器、速度、节奏与动态变化；画内广播、手机、现场演奏属于画面声音事件，不放进观众配乐层。

### 多镜容器：每切一张关键帧

**`taste_option`**：几个相邻镜头可以装进同一次 full-reference 生成，每切挂它自己的已接受关键帧。
**`craft_default`**：装容器的条件是三条都满足：

- 每个成员镜头都有已接受的起始帧图片（`REF-...` 或 `PLAN-...`，`用途：起始帧`）；缺一张就逐镜生成；
- 成员已接受时长之和在 4–15 秒内，且成员资格与容器算术按 [交付形态](delivery-profile.md) 的多镜容器记账；
- 容器用一份参考清单：各切关键帧按切的顺序排在前面，共用的身份、地点图接在后面，
  `<Picture N>` 按这份清单的 `顺序` 编号，不照抄逐镜时的编号。

正文第一行、`subject_definitions` 之前，写一句对齐句把每张关键帧钉到它那一切的起点：

```text
<Picture 1> aligns with the 0.00-second mark as the opening frame of [Shot 1]; <Picture 2> aligns with the 3.00-second mark as the frame of [Shot 2]; <Picture 3> aligns with the 6.00-second mark as the frame of [Shot 3].
```

`detailed_description` 里后续各切照常写 `[Shot 2] At 00:03.000, ...`，秒数与对齐句一致；
`retention_analysis` 为每张关键帧写它负责的那一切。一组 9 秒三切的小样本（要求 3.0/6.0 秒切）：
每切挂关键帧，切点落在 2.88–3.04 / 6.00–6.04 秒，各切与关键帧的构图相似度接近三次逐镜首帧生成，
生成次数为三分之一；只挂第一切的关键帧时，切点偏到 2.92–3.88 / 5.88–6.21 秒，第 2、3 切的构图
明显偏离关键帧，还出现过一次多出来的切。所以没有逐切关键帧时不装容器。

## 素材数量上限

一次生成最多 1 张首帧、1 张尾帧、9 张 `reference_image`、3 段 `reference_video`、3 段 `reference_audio`；
视频与音频每段 2–15 秒，且各自合计不超过 15 秒。分辨率取 `768P` 或 `2K`（`MiniMax-H3-Max` 另为 `480P`/`768P`）。
超过上限时在分镜阶段按重要性取舍，并写明放弃了哪些参考，不在正文里假装它们仍然生效。

本镜还没有起始帧图片时有两条路：由 `$short-drama-produce` 从 `分镜.md` 的 `SHOT-...` 冻结关键帧生成，
拿到真实文件后由分镜 owner 绑成 `用途：起始帧` 的 `REF-...`；或者由创作者把该镜的冻结关键帧正文复制到
自己的工具里出图，本轮先记成 `PLAN-...（用途：起始帧）`、定位符写本镜 `SHOT-...`。
两种写法本阶段都原样抄入，正文写法相同。

`输入参考图` 只登记参考**图片**。连续段的实际视频不写进这个字段；下面说明支持双输入的执行端
怎样绑定视频与尾帧。当前内置 creator-first 生产选择器尚不能绑定续接视频，投产时按
[交付路线的接口边界](delivery-profile.md#从已生成结果续接)停靠，不把视频路径塞进图片 `REF-...`。

## 连续段

H3 的首/尾帧模式与 full-reference 模式互斥，不能在同一请求混用 `first_frame`/`last_frame` 和
`reference_image`/`reference_video`/`reference_audio`。连续段需要上一段实际视频和实际尾帧时，统一走
full-reference：

- 上一段实际视频：`reference_video`，正文称 `<Video 1>`，控制动作、节奏和声音连续；
- 该视频的实际尾帧：`reference_image`，正文称 `<Picture 1>`，只作为新段开场的可见姿态与构图锚点。

实际尾帧在该模式下使用 `reference_image`，以满足首尾帧输入与 full-reference 输入互斥的接口契约。

## 时长

**`structural_invariant`（执行端契约）**：MiniMax-H3 的 `duration` 必填，为 4–15 的任一整数秒，
并非只有 5/10/15 三档。网页界面或 job 的时长设置要与分镜时长和正文终点一致；写在提示词里的秒数
不能替代生成设置。短动作在合法镜长内完成并保持已接受终点；超过 15 秒的镜头回分镜按闭合状态拆开。
本阶段不偷改镜头秒数。

`MiniMax-H3-Max` 是另一型号：5–15 秒、480P/768P，仅支持文生和首/尾帧，不支持 full-reference。
不能把本页 H3 的参考音频路径或 4 秒下限套到 Max。

### 对白容量与自然语速

**`craft_default`**：按 [对白预算](performance-action-timing.md#对白预算) 先核对完整发声需要多久，
再给主时间线安排开口、停顿与落点。分镜镜长够长但开口太晚，一样会赶词。
H3 中文小样本可参考约 4.1 个可发声字/秒；用实际可发声区间估算，生成后核对台词完整性。
样本出现过赶词与静默截断，不能据此确定通用截断阈值。
口语语言、声线与语速描述放在 `<d>` 外；`<d>` 内只放语言标签和逐字台词，不放秒数或表演指令。
稳定说话人用 `(S1)`、`(S2)`；full-reference 中说话人物同时写 `<Subject N> (Sx)`。

无参考音频时，以自然语言交代说话方式、开口 cue、句间停顿和说完后的动作；文本估时区间只留在镜头说明中，
不把每个词硬塞进小数秒槽。实际有音频对齐依据或已接受的精确时点时，才据此细化声音时序。
H3 官方接口未提供独立 `speech_rate` 参数，也没有公布「中文每秒固定几字」的可靠公式；
提示词中的语速与时机是生成指导，不能当作秒级执行保证。仅追加“自然语速”无法补上缺失的发声时间。

同一次生成内，已接受的对白跨切镜时可以用 `<scenetrans>` 并声明声音连续；它不会增加总时长，也不能
保证两个独立 job 的音频无缝衔接。`<cutoff>` 表示视频结束时有意截断发声，只用于剧本已要求的截断，
不用于处理装不下的完整台词。

### 说话人绑定

**`craft_default`**：说话人第一次出现时，在 `<d>` 外交代他在画内还是画外、以及音色（年龄、性别、高低），
台词跟在他的可见动作句后面（仍只出现一次），不集中列在正文末尾：
`<Subject 1> (S1), the boy on-screen with a clear high voice, opens his mouth and calls out: <d>[Chinese] ...</d>`。
台词期间画里还有别人的正脸时，把那个人明写成不说话：
`The messenger does not speak; his lips remain completely closed.`——与官方画外音写法
`while his lips remain completely closed` 是同一句式。

一镜实测（远处小孩喊一句，近处骑手不说话，骑手在台词期间仍正对镜头）：现行写法 3 次中 2 次口型落在骑手、
小孩闭嘴；加上述两条后 3 次全部落在小孩。19 条样本的发声基频都在儿童区间——模型没有选错声音，
只是把口型放到画面里最显眼的正脸上。骑手已出画或背对时，两种写法 12 次全部正确。所以分镜能安排时，
先让不说话的人出画或背身；不能时才靠这两条兜底，生成后仍核对口型落在谁脸上。

### 有配音或参考音频时

**`craft_default`**：已有同句同表演音频时，先测实际发声与停顿，再确定镜长。没有现成音频仍可按文本估计
写提示词，不为完成本阶段自动调用 TTS 或生成服务。

- 只参照音色、情绪或说话方式：使用 `reference`；它会重新表演本镜台词，不能拿参考音频的文件长度
  当作新台词时长，也不携带参考音频里无关的原话。
- 已接受完整声音轨原样复用：`fully_copy` 表示整条最终音轨；只用对白层或片段并另加环境声时使用
  `partially_copy`，写清源片段与目标时间的对应。复用用到的发声区间要完整容纳，不为适配镜长压缩语速。
- 参考音频走 full-reference，配合至少一张参考图或一段参考视频；每段音频 2–15 秒，最多三段、合计
  不超过 15 秒。图片改用 `reference_image`，不能与 `first_frame`/`last_frame` 混用。

`fully_copy` 等是官方提示词的复用意图，不是逐样本一致的验收证明。生成后核听逐字内容、语速、停顿、
尾音完整性与口型；项目需要精确锁定已有音轨时，以后期保留该音轨并核对画面同步作为最终依据。

## Ksr 高级镜头机制（按镜头需要选用）

这些是从课程与真实画布中提炼的可选机制，不要求每镜使用。

- **起幅即运动中**：动作、追逐、灾难或连续航拍可从事件中段开始，人物、机器和相机已经有方向和速度。
  硬切仍要读成同一次运动时，对齐方向、速度层级、地平线高度和主体出入方向。
- **全遮挡变换**：旧状态可见 → 实体完整遮挡 → 遮挡物继续离开 → 新状态在第一帧完整揭示。
  遮挡期间保持步态、通话、道具、重心和摄影机运动；只在完全不可见时换衣服或形态。
- **分阶段特效**：先兆与环境异常 → 轮廓或负形 → 材质与结构逐步落实 → 主体稳定 → 环境响应。
  主体尚未成立时，相关物理反馈尚未发生；简单变化不必强凑阶段。
- **摄影机的物理反应**：需要纪实感时，可用起步稍迟、短暂跟丢、追过头再修正、焦点迟滞或冲击造成的单次震动。
  写清触发与修正结果，不给画面附加均匀抖动。
- **打斗接触与代价**：先建立空间，再写攻击路径、接触点、双方受力、位移和环境反馈。
  连续打击逐步升级破坏、失衡和伤势，速度服务动作可读性。

## 真实提示词案例怎样转成 H3 写法

以下案例用于提取写法，不把公开可见等同于全网爆款证明。正文仍按本镜事实重写，不复制剧情。

### 官方 FL2VA：雨伞从闭合到撑开

官方示例先用首尾帧对齐句固定两端，再写松手、抬伞、推升、开伞、走到伞下和归位，
用动作路径连接图片，而不是分别复述两张静图。`non_diegetic_music: N/A` 明确不补配乐。
可迁移点：**首尾帧负责两端，正文负责中间过程；动作完成后再落到尾帧构图。**

### EvoLink：VTuber 开播

原案例把每张图分别限定为身份、平台界面、房间和开播卡片，音频负责人声身份与表演。
它还把 0–2.4 秒写成无对白区，人物视线主要看向聊天栏，并只允许多条指定聊天文字清晰可读。
可迁移点：
- 素材职责和控制边界要具体到“身份 / 界面 / 房间 / 卡片”，避免一张图包办所有内容。
- 音频的静音前奏也属于时间线；不要只写台词，不写等待和停顿。
- 表演任务写成“读聊天并反应”，视线、点头、眉部和小手势围绕这个任务，而不是站桩口播。
- 屏内精确文字采用白名单，其余信息弱化，减少伪字和 UI 漂移。

### EvoLink：眼镜与耳机广告

眼镜案例分别用主视觉、人物细节和产品图控制三类事实，并用包覆曲面、几何轮廓、镜面反射和流线镜腿描述产品。
耳机案例按材质特写 → 拉远主视图 → 爆炸分解 → 重新合拢的顺序组织四段，产品几何始终稳定。
可迁移点：**参考图承担身份与形制，正文承担镜头顺序和动作；不要把时间花在重复外观上。**

### EvoLink：汉堡 vlog

案例用一张产品图锁定汉堡比例与配料，再把开盒、急推、芝士拉丝、咬后反应拆成短镜，
用自然对焦呼吸、手持瑕疵和硬跳切形成真实 UGC 感。
可迁移点：**真实感来自具体物理、动作节奏和摄影瑕疵，不来自“高级电影感”堆词。**

## H3 生成前质检（preflight）

- [ ] 模式与素材组合是否匹配：Base、首帧、首尾帧、full-reference 是否没有混用？
- [ ] I2VA/FL2VA 是否有首行对齐句，帧与镜头、终点秒数是否对应？
- [ ] 六段是否完整，标签是否只定义一次，Subject/Picture/Video/Audio 是否各自承担正确职责？
- [ ] `summary` 的任务类型和 `retention_analysis` 的保留强度是否符合素材实际用途？
- [ ] 画面是否有可见起点、动作、反应与终点，而不是只有剧情摘要？
- [ ] 已选的空间、人物/听者、摄影/焦点、动态受光、声音和出口是否落实到正文？参考关系是否挤占了过程描述？并行行为是否相容、关键表演是否可读？
- [ ] 说话人 ID 是否稳定，逐字对白是否只出现一次，画外音与闭嘴/背身安排是否一致？
- [ ] 环境声、物理音效和配乐是否分层，静音、停顿与跨切声音是否明确？
- [ ] 切点、运镜、动作负载和参考范围是否相容？
- [ ] 主角以外本应持续的环境、听者与物理反馈是否遗漏？静止是否符合已接受现场？次级动态和声音是否有主次、先后与收束，而非全场同步运动？
- [ ] BGM、字幕、画内文字、来源事实和连续性等必要边界是否准确？

## 常见问题与局部修复

| 问题 | 优先检查 | 修复方向 |
|---|---|---|
| 切点漂移或额外切镜 | 时间戳与逐切关键帧 | 对齐实际时长；需要逐切控制时给每切一张关键帧，或改逐镜生成 |
| 人物/场景换脸换景 | 素材职责是否越权 | 减少无关参考，分开身份、地理、构图和造型状态 |
| 口型落到别人脸上 | 正脸竞争与说话人绑定 | 优先让非说话者背身或出画；否则明确其不说话、嘴唇闭合 |
| 多余配乐或声音嘈杂 | 声音层是否缺失或重复 | 写全底声与物理音效，配乐写 `N/A`，对白只留在主时间线 |
| 台词赶、断或重复 | 发声窗口与切点 | 按完整原句重算容量，调整镜长、拆镜或减少竞争动作 |
| 动作跳过或人偶感 | 动作量与身体配合 | 保核心动作，补稳定件、补偿件和不自主反应，或拆镜 |
| 画面假、人物与环境分离 | 光照与接触面 | 补实际光源到人物/材质的影响，以及脚踩、手扶等接触反应 |
| 参考图把景别拉宽 | 地点图职责与具体取景 | 地点图只管地理，在正文明确画面切到哪里、主体占多少 |
| UI 伪字或屏内内容错乱 | 文字白名单与屏层职责 | 精确字符逐字限定，分开实拍层、屏内内容和 HUD 层 |
| 真实感不足 | 动作与摄影是否过度工整 | 按内容需要加入对焦呼吸、手持迟滞、自然遮挡或背景微动 |

### Context-IR 的作用

H3-Context-IR 把多模态输入增强成结构化提示词，本身不生成视频，且仍要求调用方先给出 4–15 秒的
`duration`。它不能代替对白预算。若执行端使用该服务，检查增强后的逐字台词、声音时间线与原时长一致，
不因使用官方增强就跳过容量检查。

官方依据（2026-09-07 核对）：

- [Base 提示词指南](https://github.com/MiniMax-AI/MiniMax-H3/blob/main/skills/h3-prompt-writing/references/base-en.txt)：对白位置、说话人、语速描述、切镜时间戳与跨镜发声。
- [Full-reference 指南](https://github.com/MiniMax-AI/MiniMax-H3/blob/main/skills/h3-prompt-writing/references/ref-en.txt)：六段结构、音频引用与复用语义。
- [视频生成 API](https://platform.minimax.io/docs/api-reference/video-generation-v2-create)：必填时长、型号差异和输入模式互斥。
- [官方 CLI 的 H3 指南](https://github.com/MiniMax-AI/cli/blob/main/skill/h3-video/references/h3-video.md)：音频配合视觉参考，声音对齐与生成后检查。
- [Context-IR API](https://platform.minimax.io/docs/api-reference/video-generation-v2-h3-context-ir)：提示词增强和独立的时长输入。
- [官方功能示例](https://platform.minimax.cn/docs/guides/video-prompt)：品牌、剧情、UI 与多模态真实输入输出示例。
- [EvoLink 真实提示词库](https://evolink.ai/zh/minimax-h3-prompts)：带生成结果的公开案例，本文拆解其 VTuber、眼镜、耳机和汉堡写法；传播量不作爆款证明。

## 成像设计进入正式正文

默认读[成像风格与感官质感](../../short-drama/references/image-look-and-finishing.md)。从视觉设定与分镜选定的生成职责出发，把色彩/影调、成像/景深、光源/局部注意、材质、动态连续和声音空间写成对象、变化与结果。静态基础可由明确参考承担，变化仍进入 detailed_description 或 integrated_multimodal_description。

制作分工中的后期 LUT、最终颗粒、精确调色参数留在工程；生成正文写出需要的素材外观与动态，不重复要求后期负责的同一处理。比较完整正式正文和真正请求字段，确认选定设计没有只留在解释段。
