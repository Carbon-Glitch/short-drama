# 成像风格与感官质感

默认从题材气质与观众体验选择成像语言，让造型、空间、光学载体、动态光线、声音和后期共同服务同一场戏的吸引力。Agent 主动确立具有辨识度的 Look；已有方向复用，关键差异用代表帧快速对比。

## 主动选择的维度（兼容实拍电影感与强风格化作品）

| 维度 | 作出可执行选择 | 写到可见/可听结果 |
|---|---|---|
| 成像媒介与防平庸护栏 | 胶片/摄影机光学性格，或二维手绘墨线/矿物平涂/定格等画材介质，以及明确避让项 | 如 35mm 电影胶片细腻颗粒与柔和滚落、拒绝对称均质大平光与塑料 CG 反光；或纯二维平涂线稿禁用 3D 体积光 |
| 色彩秩序与影调 | 有限剧组色盘（主色/辅色/点睛色）、局部冷暖分离、肤色健康/风格色准、暗部细节保留与高光过渡 | 如冷青室内保持深木纹可读，唯独台灯暖晕落在信封与指尖，不往全片泼一层统一黄滤镜 |
| 镜头成像与留白 | 焦段透视性格（广角张力/长焦压缩）、景深虚实、焦外散景形状、前景遮挡与负空间比例 | 如 85mm 浅景深把远景灯光揉成椭圆散景，前景虚化边框掠过形成视差，大面积留白衬托主体孤立 |
| 扩散与光学气氛 | 柔化强度、高光微晕（halation）、光晕、眩光、逆光空气粒子 | 如夜戏灯晕在边缘微微散开而不糊掉面部轮廓；门掩上后高光迅速收束 |
| 局部视觉引导 | 哪一处靠明暗反差、色彩纯度、锐利合焦或动态对比统治视线 | 如满室素净冷白里唯独桌面一只亮色道具刺入视线；听者脸颊短暂接住反射光 |
| 表面与物理肌理 | 皮肤毛孔、织物经纬、金属氧化、水面反射、磨损包浆或画笔肌理 | 如粗呢哑光吸光、湿衣皱褶留暗痕、皮肤保留自然微纹理与微弱光泽，不呈磨皮塑料态 |
| 时间中的质感 | 运动模糊、焦点转移、衣料与空气余动、接触阴影与反射连续 | 如推门带起微尘穿过光柱；身体移动时高光顺着缎面连续滑行 |
| 声音空间 | 远近透视、方向、遮挡闷响、混响、声场骤抽留白与瞬态冲击 | 如先听远方低沉车流，车掠近时胎噪穿框，离开后突发 1 秒极静只余呼吸 |

按场面组织主次，选出既有质感又能瞬间抓人的一组。胶片颗粒、高反差暗调、通透明亮日系、还是浓烈高饱和撞色都是主动审美选择，绝不滑回平庸均质默认光。

## 共同 Look 不是共同复制句

共同 Look 统一的是全片的**剧组色盘、成像媒介、光学性格与物理光源关系**；每张图和每段视频仍按当前状态实时计算距离、遮挡、开合与焦点。先定世界光源与色彩纪律，再写这一刻具体对象上的受光、暗部纹理、高光和反射。

例如闭门时琥珀灯只照亮玻璃内腔与近旁桌面；开门递衣后，同一盏灯随门缝斜照到衣袖与托衣的手，反光随门板角度移动，顶灯与窗外冷光不变。开门画面不能盲目继承“暖光只属于内腔”的闭门句。

需要同时读懂前景反应与背景动作时，选择能承载两者的景深或安排焦点交接；严禁写“虚化但可辨”这类自相矛盾的愿望，实际占画比例与反差必须支撑它真正可读。

## 放在哪里执行（确立 80/20 前后期边界）

**生成端（必须先承载 80% 核心美学质感）**：资产图与视频生成（Seedance 2.5 / MiniMax H3）直接决定整部片子能不能脱离廉价 AI 感。必须把**成像载体性格、镜头透视与景深虚化、剧组色盘主辅分离、局部动机布光与暗部纹理保留、材质正反物理瑕疵、动态受光与反射、声音空间透视**真切写进资产图和视频提示词像素里。

**后期端（负责 20% 精确收束与统一匹配）**：负责精确剪辑刀法、镜间色彩微调对齐、最终统一的 Look/LUT 调色曲线、成片级微颗粒统一、图形字幕叠层与混音平衡。写入 `film.html` / OpenFilm 工程参数与素材；具体 LUT 文件、CSS/着色器强度和色彩空间参数属于执行工程，绝不作为虚构参数塞给视频模型——但也绝不能拿“后期再套 LUT”当借口，纵容前端生成平庸白开水素材。

**混合设计**：将同一效果合理拆工。例如雨夜对峙：前端资产图与视频模型做出“湿面反光、局部车灯扫过脸部的光影剧变与暗部质感”；后期在 OpenFilm 中统一全集相邻镜头的黑位匹配与高光肤色微调。

## 沿用五文档与一份时间线

1. 《视觉设定.md》用“影像风格”确立剧组色盘、成像媒介、光源法则与美学禁用边界；关键项记为设计重点/声音重点。
2. 《图片提示词.md》将其落入高质感资产图与必要的风格定调代表图，先在静态像素里建立不可妥协的视觉上限。
3. 《分镜.md》将其落入景别反差、机位姿态、留白构图、光影流动、声音和“制作分工”。
4. 《视频提示词.md》按 Seedance 2.5 / MiniMax H3 各自方言把光学基调、动态光影、焦点转移与空间声场写进可复制正文。
5. OpenFilm 的 `film.html`、VTT、镜头页与真实 Look 文件负责最终剪辑与镜间统一调色。

## 视频模型的具体表达（跨模型通用的质感句法）

用具体的光学、光影行为与色彩分离代替空洞“高级感”标签。例如：

- **动态受光与高光滚落**：`35mm cinema film grain, lifted slate shadows, no plastic CGI sheen; a narrow warm amber headlight sweep travels across his damp wool shoulder and cheekbone, blooming softly before receding into cool street ambience.`
- **局部色盘分离与焦点交接**：`85mm shallow depth of field; crisp focus starts on the single saturated yellow porcelain cup against the muted monochrome tabletop, then racks cleanly to the character's unblinking eyes across the frame.`
- **材质响应与节奏反差**：`Matte charcoal coat absorbs the shadow while fine droplets catch a thin rim of cold skylight; the reflection glides continuously across the wet asphalt as distant traffic noise suddenly drops into silence.`

在 Seedance 2.5 中融入全局基调护栏与镜头过程；在 MiniMax H3 中融入 `integrated_multimodal_description` 或 `detailed_description`（声音入 `overall_soundscape`），严格遵守各模型自身结构规范。

## 比较与验收

先用代表帧与试拍短片验证**第一眼视觉魅力、去塑料感、暗部与高光宽容度、色彩纪律与空间稳定性**，再连看相邻镜头。对照创作目标挑出最有审美张力和感染力的一版。已有素材通常为 SDR 图像时，依据真实观感处理；Log 转换只用于真实 Log 输入。文字传递、画面呈现与动态验证分别记录。

方法参照：[ARRI Look Builder](https://www.arri.com/en/software/previs-software/look-builder) 的 Look/Texture/光学组合；[Blackmagic Film Look Creator](https://documents.blackmagicdesign.com/SupportNotes/DaVinci_Resolve_19_New_Features_Guide.pdf) 的色彩与成像效果分工；H3 正文结构对照 [MiniMax 官方提示词 Skill](https://github.com/MiniMax-AI/MiniMax-H3/tree/main/skills/h3-prompt-writing)。这些资料提供方法和语法，具体效果以本项目输入与输出观察决定。
