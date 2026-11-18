# 分镜与后期 Skill 吸收记录 · 2026-11-16

截至日期内的第一手源码快照；未做全网穷尽或大师效果排行。以下是本套件自行转译的方法，
只有FFmpeg六工具子集复制了可执行代码并保留MIT许可，其余不复制原模板或引入外部项目状态。

| 来源与固定提交 | 已吸收的增量 | 不采用/尚未接入 |
|---|---|---|
| [video-use](https://github.com/browser-use/video-use/tree/43cfc566833548093455c9d4a46bd69913b7e552) · MIT | 以同一剧情拍点比较候选表演；可疑切点看局部影格/波形；源时钟与成片时钟分开 | 强制Scribe、全片固定30ms淡变、额外critic/审批、EDL作为第二真相 |
| [Cinematic Director](https://github.com/wuwangzhang1216/DirectorSKILL/tree/c65ae0d14457053efb1e354c7e7f7e120d97fad1) · MIT | 相邻镜的接剪意图、可剪余量、声音桥与转场重叠算术 | 固定镜长/景别比例、盲裁头尾、默认丢原声、用转场遮缺失接触 |
| [山音导演](https://github.com/Shanyin-ai/shanyin-director-master/tree/30f0daecaf0754e08cf88ece83fabf3a2372a016) · MIT | 叙事镜头组、情节压力/情感重量双轨节奏、动作—反应变体 | 出彩比例、xlsx权威、逐步审批、导演擅改对白；叙事组不等于GROUP生产容器 |
| [Story-Film-Skills](https://github.com/badgids/Story-Film-Skills/tree/5ec9daf3950a987424a879ab5fef583b013afa8a) · Apache-2.0 | shot-design的最低覆盖和cut intent、take-selection相邻匹配、editorial-reconciliation全SHOT对账 | 完整feature状态数据库、take/manifest重复真相、外部生成适配器 |
| [video-shotcraft](https://github.com/Vincentwei1021/video-shotcraft/tree/253ae59081cd8f85cee47074eec9ad1121f2e5ad) · Apache-2.0 | 实际SFX瞬态对齐、渲后复测、按需分层交付 | 产品/UI镜头库当短剧核心、全片卡鼓点、固定AAC延迟补偿常数 |
| [ffmpeg-skill](https://github.com/kajisho5/ffmpeg-skill/tree/f1c97cbffeac71b8fdfca2f790ceb00db3bcce65) · MIT | 六个按需后期工具；先probe、可预览参数、真实输出再测 | 独立大入口、42工具全装、静音裁剪、自动压时长与平台响度预设 |
| [video-editing-skill](https://github.com/kajisho5/video-editing-skill/tree/c473780deee151ec5091a23b56af5bf6ae6176ea) · MIT | 精确source→timeline映射与执行/语义分离，用于原生conform输出 | 另一套typed项目图、全图执行器；映射不能证明表演正确 |
| [audio-production-skill](https://github.com/kajisho5/audio-production-skill/tree/d179cacb31d160c7e0b131d228134b914e28ee09) · MIT | 显式混音目标、stem/混合轨边界、最终编码后测响度 | 整套typed操作图、未安装的分轨混音引擎 |
| [color-grading-skill](https://github.com/kajisho5/color-grading-skill/tree/0ddeaac21d651f407549fbfabb4ac277be9e1750) · MIT | 颜色空间/标签/实际变换分开；技术校正与创意look分开 | 自动大师审美、OCIO/ACES运行时或MATCH_CAMERA已接入的声明 |

## 进入现有流程的位置

- 分镜：[分镜先为剪辑设计](../../short-drama-storyboard/references/editorial-coverage.md)。
- 选镜、时钟、分镜源窗落实：[分镜落实与精剪](editorial-conform.md)。
- 音轨/规格/颜色/抽帧：[FFmpeg后期执行工具](ffmpeg-finishing.md)。
- `edit_tool.py check/conform/verify` 核对已给分镜的全部SHOT，包括只有视频CUT时缺失的SHOT。
  `conform` 输出计划时码、源窗、职责及未验证项，不产生新的创作文档。

## 其他查到但不整合的候选

`AI Film Director Workbench`（`ff4791412231b95550db456b58659c4b17dbc6a4`）的职责追踪已有同类能力，
第三方万物生语料不在其MIT覆盖中；`cinema-skills`（`b3d96caaf90729f086ce8bfa96654f40fd98e4e5`）
增量有限。`smixs/visual-skills`（`61a60d317f0fa0c3dc98902e58a7cb178838ae3f`）有可参考的调度/视线问题，
但每镜三细节、固定节奏梯形和感情符号不纳入核心。

Remotion官方skills（`7e541aa4d7361dfaca0780a565a47307eb7bdfbb`）与现有HyperFrames更适合字幕、
精确文字、动效和合成，按已有路径读取；不替换叙事剪辑决策。Clipwing/real-sfx
（`edbefcbc3474869e6cc1e8a7ca583b0efd0dab7e`）可供音效候选定位，但其特定库和不听音的数值流程
不等于完成短剧听审，本次未接入该运行时。

是否达到“顶级剪辑/后期效果”需真实素材、具体版本和观看/回听比较；以上来源与工具测试不构成审美验收。
