# 成像风格与感官质感

默认从观众体验选择成像语言，让人物、空间、光线、运动、声音和后期成为同一场面的表达。Agent 主动提出并选用适合本场的 Look；已有方向复用，有价值的差异用代表帧对比。

## 主动选择的维度

| 维度 | 作出可执行选择 | 写到可见/可听结果 |
|---|---|---|
| 色彩与影调 | 冷暖关系、肤色、中间调、黑位、高光过渡、饱和度、局部色彩 | 如冷环境中的自然肤色、柔和高光里仍读得出湿衣纹理 |
| 镜头成像 | 透视、拍摄距离、景深、焦外、焦点交接、边缘表现 | 近景前景掠过形成视差；焦点从热气后的手转到人物眼神 |
| 扩散与光学气氛 | 柔化强度、高光辉光、光晕、眩光、逆光空气 | 车灯高光轻微扩散，面部和衣料仍有形状；灯离开后辉光收束 |
| 局部视觉引导 | 哪处更亮、清晰、饱和或有动态对比 | 听者脸短暂接住反射光，环境仍可读而注意转向他 |
| 表面与影像纹理 | 皮肤、织物、金属、水面、微对比、锐度、颗粒 | 湿粗呢吸光、皮肤有细微高光、金属反射随视角移动 |
| 时间中的质感 | 运动模糊、焦点变化、衣料与水的余动、接触/阴影/反射连续 | 手离开后蒸汽恢复上升；移动时受光沿身体表面连续变化 |
| 镜间统一与发展 | 场景共同 Look、人物肤色、光源关系、质感尺度、表达性变化 | 同场相邻镜保持视觉世界，情绪变化通过明确的光色或节奏发展 |
| 声音空间 | 远近、方向、遮挡、频率、混响、动态、底声与瞬态 | 先听湿路胎噪，车经过时掠近，远去后雨声重新占据注意 |

按场面组织主次，选择有表现力的一组。滤镜、胶片感、柔光或锋利清晰都是创作选择，细节可以服务美感、触感与情绪。

## 放在哪里执行

**生成端**负责与世界、表演和摄影紧密耦合的观感：透视/景深、人物与空间的受光、高光如何随车灯变化、皮肤织物的表面表现、合理运动模糊、接触与反射、声源距离变化。资产图和真实首帧先建立静态基础，H3 正文写出时间中的变化。

**后期端**负责选定的可控处理：统一色彩转换、镜间校正、最终 Look/LUT、颗粒与局部精修、音量和频段处理。写入实际工程的参数与素材。具体 LUT、CSS/着色器、滤镜强度和色彩空间属于执行工程，不作为视频模型的虚构 API 参数。

**混合设计**将同一效果拆成不同职责。例如雨夜：生成做车灯照到湿脸的真实变化；后期统一冷环境与肤色关系。两端各做一次自己负责的部分。需要后期颗粒时，生成保留可用表面细节；采用生成的扩散效果时，后期根据实际素材决定是否再处理。

## 沿用五文档与一份时间线

1. 《视觉设定.md》用“影像风格”概述场景 Look；关键项记为设计重点/声音重点，注明生成、后期或混合职责。
2. 《图片提示词.md》将它落实为资产与角色入景画面，比较服装、肤色、背景、光源和焦点的共同效果。
3. 《分镜.md》把选择放入景别、机位、动作、声音和“制作分工”：对象、触发、强度变化及落点清楚。
4. 《视频提示词.md》把生成端的选择写进实际可复制正文；H3 参考素材负责静态基础，正文负责动态变化。
5. OpenFilm 的 film.html、VTT、镜头页与真实 Look 文件负责后期执行；绑定与检查记录所选设计的承载和当前版本。

## H3 的具体表达

用画面行为代替笼统形容词或工具名。例如：

- `A narrow headlight sweep travels from his wet shoulder across his cheek; the highlight blooms gently and fades as the vehicle passes, leaving his eyes readable in the cooler street ambience.`
- `Focus begins on the steamer rim, then settles on the hands exchanging the paper bag; the market behind them remains recognizable with soft spatial separation.`
- `The cloth stays matte in shadow while droplets briefly catch the moving light; the reflection travels continuously across the wet pavement.`
- `The tire hiss approaches offscreen, passes close, and recedes; nearby rain becomes prominent again after it leaves.`

将适用内容融入三段式的 integrated_multimodal_description 或六段式的 detailed_description；在 overall_soundscape 汇总空间声层。正式正文保持所选模式的段名与顺序。

## 比较与验收

先看代表帧与短片段的注意中心、肤色/材质、高光、暗部、空间和时间稳定性，再连续看相邻镜头。对照目标和实际输出选择更有表现力的一版。已有素材通常为已显示的 SDR 图像时，依据真实元数据和观感处理；摄影机 Log 转换只用于相应输入。文字已传递、画面已呈现和动态已验证分别记录。

方法参照：[ARRI Look Builder](https://www.arri.com/en/learn/camera-systems/tools/look-builder) 的 Look/Texture/光学组合；[Blackmagic Film Look Creator](https://documents.blackmagicdesign.com/SupportNotes/DaVinci_Resolve_19_New_Features_Guide.pdf) 的色彩与成像效果分工；H3 正文结构对照 [MiniMax 官方提示词 Skill](https://github.com/MiniMax-AI/MiniMax-H3/tree/main/skills/h3-prompt-writing)。这些资料提供方法和语法，具体效果以本项目输入与输出观察决定。
