# OpenFilm 工程接口

## 所有权

`film.html` 决定当前镜序、源窗、速度、增益、样式、锁定与图层；VTT 决定字幕文字、cue 时间与版式；镜头 HTML 决定图形动画。`.short-drama/bindings.json` 只保存源事件与关联，`sync.json` 是可重建的同步缓存，`剪辑单.md` 是报告。

## 初始化与局部编辑

从技能目录运行 `python scripts/openfilm_bridge.py setup` 部署固定 OpenFilm 0.4.1。默认隔离安装于用户工具目录；可用 `SHORT_DRAMA_OPENFILM_HOME` 指定位置。安装不改 npm 全局镜像或用户已有 OpenFilm 配置。插件后端更新后重开本集专用 Studio；已有打开的文档先保存。

```sh
python scripts/openfilm_bridge.py init <集目录> --input <seed.json>
python scripts/openfilm_bridge.py state <集目录>
python scripts/openfilm_bridge.py patch <集目录> --input <patch.json>
python scripts/openfilm_bridge.py sync <集目录>
```

seed 示例（时间都是秒）：

```json
{"fps":24,"film":{"stage":{"w":1080,"h":1920},"tracks":[{"clips":[{"id":"CUT-A","src":"assets/a.mp4","time":[1,5],"at":0,"volume":1,"attrs":{"data-shot-id":"SHOT-A","data-sd-intent":"保留迟疑后的完整反应"}}]}]},"bindings":{"schema":1,"events":[{"id":"reaction","origin":"CUT-A","src":"assets/a.mp4","start":2,"end":3,"purpose":"听者反应","required":true}],"cues":{}}}
```

patch 使用 `state` 返回的 `rev`：

```json
{"rev":"当前版本","ops":[{"op":"set","clip":"CUT-A","field":"time","value":[1.2,5]},{"op":"move","clip":"CUT-A","at":0.3}]}
```

其他操作沿原生 `studio/server/ops.mjs`：`fields` 局部字段（null 删除）、`insert`、`remove`、`split`、`track`、`keyframes`。样式、overrides 仅改本次所需字段。新增独立图形使用原生页面协议 `window.film={duration,width,height,ready,frame(t)}`；frame 必须可任意 seek。

`import-asset --input payload.json` 的 payload 是 `{"file":"实际文件路径"}`，按内容哈希拷入相对 assets。`replace-source` 是 `{"clip":"CUT-A","file":"新源文件","expectedSrc":"原src"}`，同来源拆片一起更新并保留剪点；重新看新源里的语音和动作位置。

## 前期交接

`handoff <集目录>` 返回当前前期 revision、交付事项 ID、参考依赖与未落实项。`bind-handoff --input <映射.json>` 把事项指向现有层；这只是来源关系，时间/样式仍由 film/VTT/镜头页拥有。

```json
{"revision":"handoff返回值","filmRev":"state返回值","items":{"REQ-某项":{"targets":["clip:VOICE-A","cue:captions/dialogue.vtt#cue-a"]}},"dispositions":{"clip:旧图层":{"disposition":"omitted","reason":"本版改用表演表达"}}}
```

事项有意省略时也可在 items 对应项写 disposition/ reason。换素材后核对实际新源，用 `refreshSources:["clip:CUT-A"]` 更新采用版本。源文档/项目设置/参考文件变化会提示复核，已采用层被整项删除也可发现。工具检查承载关系，具体表演和语义由 Agent 观察决定。预览可以带未决项继续试剪，正式交付再收齐。

独立迁移会复制前期参考依赖并保留原相对路径；同项目使用既有根目录。旧声音包络/EQ/声像、可映射字幕样式和响度直接转换；未映射字段逐项列出。音乐 envelope 复用本地 helper，按当前对白位置计算，移动对白后随之重算。

## 联动

- `data-sd-origin` 自动补稳定来源身份，拆片继承。
- clip attrs 中 `data-sd-follow` 为 JSON 字符串，例如 `{"clip":"CUT-A","edge":"end","offset":-0.3}` 或 `{"clip":"CUT-A","source_time":2.2,"offset":0}`。独立移动 follower 会更新相对偏移。
- bindings 的 `events` 默认检查画面覆盖；音频义务声明 `channel:"audio"`。有意删掉某事件时由 Agent 写 `disposition:"omitted"` 及理由。
- `cues` 键是 `captions/dialogue.vtt#cue-id`，值 `{"clip":"VOICE-A","start":0.2,"end":1.1}` 为源秒数。手改文字/样式保留，手改时间重新绑定。连续拆片保持同一句，不连续或缺失则报告具体 cue。
- 使用普通成片 VTT，不混入 OpenFilm 的源转写 SPEECH_NOTE，以免两处重排同一字幕。
- 缺少词级时间时，真实播放与波形提供判断依据；源窗口覆盖检查不等于听审通过。

## 声音与图形

普通音量、速度、淡入淡出、轨道静音和最终混音归 OpenFilm。`sound:true` 仅用于从视频提取声音的 clip；WAV/MP3 直接作为声音，不填 sound。

复杂 EQ/音乐压低可在音频 attrs 声明 `data-sd-audio` JSON：

```json
{"source":"assets/music.wav","eq":[{"frequency":2000,"width":1,"gain":-2}],"envelope":[{"t":0,"v":0},{"t":0.3,"v":0.3},{"t":4,"v":0.3},{"t":4.2,"v":0.08}]}
```

包络使用**源时钟**。本地 FFmpeg 只处理该来源并缓存 WAV；clip 保留独立时间/速度，OpenFilm 只混音一次。修改包络后 sync 即更新预览与导出共用的声音。整体响度只在 `.short-drama/project.json` 的 `loudness` 中交给最终渲染一次；不要再次处理整片。

节拍/能量候选仍使用现有 `post_runtime.py`、Hypit 的 `music_envelope.py` 等本地 helper。BGM 乐段、退出、对白让位由 Agent 按戏剧职责决定。

交叉淡变用不同画轨重叠，上层原生 overrides `[{"fade":[0.3,0]}]`；更复杂转场/图形写可编辑镜头页。原生 CSS keyframes 可做推拉与画面效果。

## 旧项目

```sh
python scripts/openfilm_migrate.py <旧集目录> <全新目标目录> --project-root <旧项目根目录>
```

迁移器读取已有 parser，拷贝真实源文件、CUT/来源、独立配音音效、cue 与基本淡变，原剪辑单存入 `.short-drama/legacy/`。特殊图形、调色、运镜和复杂循环先做对应镜头页/音轨映射后用 seed 初始化；工具会指出未映射字段，不静默丢掉。外部工程的图层以其实际文件为准，Markdown 中的描述不是已完成映射。

## 接点回看

预览/正式渲染后自动生成同目录 `预览-接点.html` / `成片-接点.html` 与 JSON，直接播放该次导出，在当前可见画面层的起止边界附近循环。它保留真实叠化、字幕与混音，边界只是候选，不把叠层出现都判成坏切。页中同时展示上游「生成安排／接镜」与 clip 来源。

已有有效导出可运行 `python scripts/openfilm_bridge.py seams <集目录> --preview` 重建（正式版省略 `--preview`）；输入或视频变更时先重做预览。回看结论写既有制作记录，实际修剪仍改 film.html。自动页不做光流评分或审美通过判定。

## 验证与交付

`edit_tool.py preview/render` 先同步并列出交接缺口，预览允许探索未决版本，正式 render 收齐后调用一次原生 renderer。交付 receipt 保存渲染图的输入哈希和输出哈希；导出期间输入变化不记为有效交付，`verify` 识别过期成果。预览记录使用 `openfilm_bridge.py verify <集目录> --preview`。

Studio 的导出菜单是原生导出，不经过 short-drama 的额外语义检查和交付 receipt；正式交付使用上述入口。实际回看、回听和审美验收单独记录，不能用哈希通过代替。
