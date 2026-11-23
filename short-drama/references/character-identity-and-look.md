# Character / Look 共享概念

- **Character**：跨 Look 仍能认出同一人物的稳定身份，如面部比例、体态、永久特征、基础发质或长期配饰。
- **Look**：有效范围内的一次完整外观：服装、发型、妆容、鞋履、临时配饰、伤势、湿污和身体绑定配件。
- **状态 delta**：相对 Character + Look 的变化，写 before/after、原因、来源、有效范围和受影响项。
- **镜头瞬态**：姿势、视线、左右手、站位、表情和机位，由分镜/连续性管理，不升级为身份或新 Look。

临时伤污、制服和当天妆容属于 Look/delta；手持剧情道具归 Prop/State。

锚点必须有区分度、可观察且后续需要保持，不用审美词代替，也不为独特新造特征。
侧面/背面/远景分别选轮廓、重心、发型剪影、发际、肩背或步态等通道；浅小面部细节不承担所有景别识别。
群像写相对身高差及绝对参照；鞋、外套和盘发不改写 Character 的尺度关系。

一个 Look 只容纳同一时刻能共存的组合，先点明 Character，再写差异及 cause、valid_from、valid_until。
跨场持续、需要复用、独立参考图或改变观众识别时才新建 Look。变体写基准、差异、保持项、原因和有效范围；
改变身份事实先回资产 owner，不在 edit prompt 偷换。

制作形态只改变识别通道和颗粒度，不改写身份、Look 组成、持物、文字政策和故事状态。
同一锚点按形态转译，不以写实程度判错。模板默认值不得覆盖已确认身份；冲突时身份优先，
删除不能追溯到当前人物的重复句。

分工：assets 决定身份、Look、delta 与复用；image-prompts 选择视图、构图、材质和光色；
storyboard 拥有镜头瞬态；design 决定妆造与视觉发展。阶段细节见
[资产人物与造型](../../short-drama-assets/references/character-and-look.md)和
[图片人物设定图](../../short-drama-image-prompts/references/character-and-look.md)。
