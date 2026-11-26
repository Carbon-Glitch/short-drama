# AI 影视平台模块复用核查

核查日期：2026-11-25。范围：上游官方文档、GitHub 文件树与具体源码；**未安装、未启动、未做模型调用或嵌入试跑**。下文“可复用”是源码级接入判断，不能当成已集成。导演台技术基线按本次任务提供的 React/Vite、SQLite、OpenFilm、ReactFlow、elkjs、Artplayer 评估。

## 决策

优先从 **StoryBored 拆取候选素材选用与角色引用组件**，从 **script2video 拆取字幕草稿工具**。保留导演台的文本分镜与 Skill 数据作为主数据；不把外部平台的“每镜先出一张图”流程变成必经阶段。Ludwig 的 embed 是真实存在的整页工作区入口，适合另开实验页验证，不宜直接替代主工作流。ViMax 适合作为以后可选执行后端；waoowaoo 当前版本不适合作为轻量组件来源。

| 项目 | 已核查的复用入口 | 实际边界 | 本次建议 |
| --- | --- | --- | --- |
| LudwigKienle/ai-video-production-editor | `packages/storyboard-embed-sdk`、`src/sdk/StoryProjectEmbed.tsx`、`StoryProjectPage.tsx` | iframe + postMessage 的整页工作区；根项目 GPL-3.0-or-later | 保留为隔离试验候选，暂不进入主应用 |
| storybored-app/storybored | React `Lightbox.tsx`、`MentionTextarea.tsx`；FastAPI/SQLite 队列与引擎 pack | MIT；小组件可拆，整个平台偏 ComfyUI + still → I2V | 第一优先：拆小组件并接现有数据 |
| reaink/script2video | `lib/utils/vtt.ts`、`lib/providers/*`、`lib/types.ts` | MIT；Next.js + Zustand + IndexedDB | 字幕草稿工具可复用；不整体搬状态层 |
| HKUDS/ViMax | `tools/protocols.py`、`interfaces/shot_description.py` | MIT；Python 生成与 agent 编排系统 | 后端适配候选，不接管 Skill 导演流程 |
| waooAI/waoowaoo | 当前 README 与 LICENSE | ELv2；Next.js/MySQL/Temporal/Redis/MinIO | 作为完整替代平台比较，不做本轮组件来源 |

许可证来源：[Ludwig NOTICE](https://github.com/LudwigKienle/ai-video-production-editor/blob/ecef50e164fb0c9b58f73babe01ea3a5dacbde02/NOTICE)、[StoryBored](https://github.com/storybored-app/storybored/blob/b368140dec0ccb43276b375afa887b2688027b0c/LICENSE)、[script2video](https://github.com/reaink/script2video/blob/63ea5ddeba233e35efaadaf0d36c81d8788eabd2/LICENSE)、[ViMax](https://github.com/HKUDS/ViMax/blob/fd4b72e7731be6e5f88486206d25ea59849b0285/LICENSE)、[waoowaoo](https://github.com/waooAI/waoowaoo/blob/dfec20e32298ed675050329e4a41477024148399/LICENSE)。

## 1. Ludwig embed：能嵌入，但不是独立分镜组件

- 官方提供 `embed.html`，宿主通过 `STORY_PROJECT_INIT` 传入 storyBible、shotPrompts、references，通过 change 事件收回编辑结果；可以只显示 script/storyboard，并关闭部分 AI 动作。SDK 是 host-side wrapper，仍需自行构建、托管完整 embed。文档只给出本地 build 与 publish checklist，不能据此声称 npm 已发布可用。[embed 文档](https://github.com/LudwigKienle/ai-video-production-editor/blob/ecef50e164fb0c9b58f73babe01ea3a5dacbde02/docs/storyboard-embed.md)、[SDK README](https://github.com/LudwigKienle/ai-video-production-editor/blob/ecef50e164fb0c9b58f73babe01ea3a5dacbde02/packages/storyboard-embed-sdk/README.md)
- 数据所有权可以留给导演台：宿主从 SQLite 映射初始值，监听事件保存，再由宿主回填。但 iframe 中有自己的 React state；持久化桥接需要我们实现。`STORY_PROJECT_STATE` 的 state 不包含 mediaItems，媒体通过事件发出；不能仅靠 requestState 做完整媒体备份。[Embed 源码](https://github.com/LudwigKienle/ai-video-production-editor/blob/ecef50e164fb0c9b58f73babe01ea3a5dacbde02/src/sdk/StoryProjectEmbed.tsx)
- `StoryProjectPage` 最终渲染完整 `ProjectHubWorkspace`；后者直接导入多家生成服务、角色资产、场面墙、云同步等。allowedPhases 控制可见阶段，并不等于拆出了独立分镜域。[Page](https://github.com/LudwigKienle/ai-video-production-editor/blob/ecef50e164fb0c9b58f73babe01ea3a5dacbde02/src/sdk/StoryProjectPage.tsx)、[Workspace](https://github.com/LudwigKienle/ai-video-production-editor/blob/ecef50e164fb0c9b58f73babe01ea3a5dacbde02/src/workspaces/ProjectHubWorkspace.tsx)
- SDK 自带 `ShotPrompt` 仅声明 shot/prompt，而工作区内部类型更丰富；SDK phase 枚举未含内部已出现的 worldbuilding。集成前必须校对两端 schema，保留原始 Skill 分镜，不能以这个简化类型反向覆盖本地记录。SDK package.json 未声明单独许可证，不把它推定为 MIT；也不把 iframe 当成自动排除根 GPL 义务的依据。[SDK types](https://github.com/LudwigKienle/ai-video-production-editor/blob/ecef50e164fb0c9b58f73babe01ea3a5dacbde02/packages/storyboard-embed-sdk/src/types.ts)、[package](https://github.com/LudwigKienle/ai-video-production-editor/blob/ecef50e164fb0c9b58f73babe01ea3a5dacbde02/packages/storyboard-embed-sdk/package.json)

**可审议试验**：仅 script/storyboard，禁用全部生成动作；用两条本地文本分镜往返一次，确认编辑保存、刷新恢复、字段不丢失，再决定是否值得承担完整工作区的维护成本。当前没有执行该试验。

## 2. StoryBored：最具体的小模块来源

- `Lightbox.tsx` 以 takes/index/pickedId/onPick 为输入，支持图片、视频、左右切换和选用；主要外部依赖是 React、lucide、Take 类型与 mediaUrl。可以保留交互实现，改媒体地址解析与 take 映射，视频预览继续交给现有 Artplayer。它是顺序浏览选用器，**不是已经具备同步双屏对比的组件**。[源码](https://github.com/storybored-app/storybored/blob/b368140dec0ccb43276b375afa887b2688027b0c/frontend/src/components/Lightbox.tsx)
- `MentionTextarea.tsx` 有光标处 @token 检测、键盘候选选择和插入；当前直接通过 TanStack Query 请求 `/api/characters`，token 正则只接受英文数字等字符。要改为导演台传入资产候选，允许角色/场景/道具和中文检索，保留稳定资产 ID，而非直接照搬 LoRA handle 作为唯一身份。[源码](https://github.com/storybored-app/storybored/blob/b368140dec0ccb43276b375afa887b2688027b0c/frontend/src/components/MentionTextarea.tsx)
- `ShotDrawer.tsx` 的 take tile 和按 manifest 生成参数表单值得局部复用；整个 drawer 绑定 health、API、Query、LoRA、workflow 与 shot 状态，不建议整文件直接搬入。[源码](https://github.com/storybored-app/storybored/blob/b368140dec0ccb43276b375afa887b2688027b0c/frontend/src/components/ShotDrawer.tsx)
- 后端是 SQLite 持久队列、SSE、ComfyUI workflow pack，模型配置与代码分开，值得借鉴。但单 GPU 串行 lane 是其本地算力假设，不宜照搬为 RunningHub 云任务限流；其 approved still → video 状态链也不能作为全能参考模式门禁。[架构](https://github.com/storybored-app/storybored/blob/b368140dec0ccb43276b375afa887b2688027b0c/ARCHITECTURE.md)
- 文档支持选中静帧作为 first **或** last anchor；这不等于同时首尾帧 FL2V，更不等于默认多角色、多场景全能参考。[合同](https://github.com/storybored-app/storybored/blob/b368140dec0ccb43276b375afa887b2688027b0c/docs/CONTRACT.md)

## 3. script2video：只拆工具，不照搬生成路线

`lib/utils/vtt.ts` 提供每镜与全片 VTT/SRT 构建，可改小型输入类型后复用；它按句子平均分配镜头时长，适用于分镜预览字幕，不能宣称是对白对齐或听审结果。[源码](https://github.com/reaink/script2video/blob/63ea5ddeba233e35efaadaf0d36c81d8788eabd2/lib/utils/vtt.ts)

Shot 类型已有 camera/composition/ambiance/dialogue/sfx，但参考图是单个 `referenceImageIndex`，不足以承载带职责的多参考绑定。MiniMax adapter 调的是官方 `api.minimax.io`，列出 Hailuo 2.3/02，只有可选 `first_frame_image`；不是现成 RunningHub H3/FL2V/全能参考 adapter。保留其 start/poll/download 的拆分思路即可，不能把老模型代码接上就称 H3 已支持。[类型](https://github.com/reaink/script2video/blob/63ea5ddeba233e35efaadaf0d36c81d8788eabd2/lib/types.ts)、[MiniMax adapter](https://github.com/reaink/script2video/blob/63ea5ddeba233e35efaadaf0d36c81d8788eabd2/lib/providers/minimax.ts)

整站是 Next.js + Zustand/IndexedDB；默认开启 frame synthesis 与 serial tail-frame。不要引入第二份项目真源，也不要用这个默认链覆盖导演台按需关键帧路线。[README](https://github.com/reaink/script2video/blob/63ea5ddeba233e35efaadaf0d36c81d8788eabd2/README.md)

## 4. 补充候选：ViMax 与 waoowaoo

**ViMax** 的 `ImageGenerator` / `VideoGenerator` Protocol 接收 prompt + reference_image_paths + kwargs，是清晰的执行后端边界；可在未来单独 Python 进程提供适配，不需要搬它的整个 agent loop。其 ShotDescription 明确含首帧、尾帧、motion 和 variation 字段，偏帧规划；默认完整接入仍可能把关键帧变成前置要求。当前只推荐研究后端边界，不替换本地 Skill 分镜与生产提示词。[Protocol](https://github.com/HKUDS/ViMax/blob/fd4b72e7731be6e5f88486206d25ea59849b0285/tools/protocols.py)、[ShotDescription](https://github.com/HKUDS/ViMax/blob/fd4b72e7731be6e5f88486206d25ea59849b0285/interfaces/shot_description.py)

**waoowaoo** 当前代码已是 Next.js 16/React 19 + MySQL/Prisma + Temporal + Redis + MinIO 的整个平台，根许可证为 Elastic License 2.0，限制向第三方提供具有其大量功能的托管服务。它是值得比较的完整自托管平台，但不应按网上旧介绍假定为 MIT 可随意拆入，也不值得为两个组件引入整套服务。[README](https://github.com/waooAI/waoowaoo/blob/dfec20e32298ed675050329e4a41477024148399/README.md)、[许可证原文](https://github.com/waooAI/waoowaoo/blob/dfec20e32298ed675050329e4a41477024148399/LICENSE)

## 最小复用提案与验收边界

1. 先提取 StoryBored 的 take 选用器、@资产引用交互；以现有 SQLite/API 提供数据，保留上游 MIT notice 与固定 commit 来源。验收：已有素材能打开、切换、选用，刷新后选用仍在；文本分镜没有图也正常编辑。
2. 如确有预览字幕需求，再提取 script2video VTT/SRT 工具；明确显示“按镜头时长生成的字幕草稿”。现有 OpenFilm 管剪辑，Artplayer 管播放，ReactFlow/elkjs 管空间关系，不再建第二套。
3. 生产方式属于镜头/生成组的可选配置：默认 `full_reference`，按需 `i2v` 或 `fl2v`。参考资产带职责和版本；只有选择需要帧图的模式才显示对应输入。此处是项目接入建议，不是声称上述上游已实现该默认行为。
4. 以上本次均未实现。真正复用时只验证组件数据往返和已选择模式的必要字段；模型产出、视听质量、云服务可用性须另有实际证据。

## 已接入：StoryBored 选片交互

2026-11-25：从上述固定版本 Lightbox.tsx 适配为 `web/src/vendor/TakeViewer.jsx`，保留 MIT notice，许可证放 `licenses/StoryBored-MIT.txt`。替换媒体地址/类型与采用回调，使用现有 SQLite 采用记录；未引入其 API、队列或 still→video 流程。窄窗口默认逐个看，仍可切回原双屏对比。浏览器已验证左右切换、采用、刷新保持、撤销；测试仅操作恢复副本。角色引用组件与其余候选仍未接入。
