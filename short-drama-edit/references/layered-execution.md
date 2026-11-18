# 分轨剪辑、预览与执行计划

需要原声跨切点、独立配乐包络、画面转场或连续预览时，在剧集的 `后期配置.json` 中写 `"execution":"layered"`。入口仍是 `edit_tool.py`，内部复用已安装 hypit 的本地 FFmpeg 执行器；不进入其写作或生产流程。

《剪辑单.md》仍是唯一剪辑决定来源。工具生成 `制作成果/成片/.execution/` 下的计划与编译时间轴；改剪时改 Markdown，生成文件随时可重建。

这些参数由 Agent 按素材写入，不要求创作者手填。已有 CUT 出现“后期执行”小节时，入口也会自动采用分轨路线。

## 给已有 CUT 加执行参数

保留原来的来源、入出点、时长、取舍和字幕。需要分轨的 CUT 增加下面的小节；没有需要的字段就省略。

````markdown
### 后期执行
```json
{
  "intent": "话未完先看听者，保留听懂后的反应",
  "native_audio": false,
  "anchors": [{"start":0.4,"end":1.2,"kind":"reaction","required":true}],
  "audio": [{
    "id":"VOICE-A", "bus":"dialogue", "file":"素材/说话人.mp4",
    "start":0.2,"end":3.2,
    "at":{"clip":"CUT-EP001-001","edge":"start"}
  }],
  "captions": [{
    "audio_id":"VOICE-A","start":0.2,"end":3.2,
    "text":"本集剧本中已经确定的原句","timing":"locked"
  }]
}
```
````

示例数字仅演示时间关系，实际填写测得的素材窗口。`anchors` 是本 CUT 源秒数；对白字幕挂 `audio_id` 后使用该音频源秒数，声音连续越过切点时字幕仍跟随它。`timing:locked` 表示明确采用这些时间，不代表机器证明对齐；`measured/reviewed` 用于已有测量/回听依据。

视频原声要保留时默认 `native_audio:true`；抽出同一段声音独立播放时设 false，避免双声。`dialogue_expected:false` 只用于已观察到无对白的镜头，并写 `no_dialogue_basis`。有对白时复用本地词时间检查，发现源窗切字或丢关键反应，工具提出需要的范围，Agent更新剪辑单后继续。

## 音乐、环境与转场

`audio` 的 `bus` 可选 dialogue/native/music/ambience/sfx；每条有唯一 id、真实 file、源 start/end、成片 at。`at/until` 支持成片秒数、`{clip,edge,offset}` 或 `{clip,source_time,offset}`。用事件锚点能在改剪后自动跟随。

音乐可写 `gain_db`、`fade_in/out`、`volume:[{time,db}]` 和 `ending:cadence/ring_out/intentional_cut`。volume.time 是本音频段内秒数，也可用事件锚点。需要循环明确 `loop:true`。沿用真实选曲，按戏剧情绪选段；对白密集处用连续包络退让，或在配置 `master.duck_music` 启用已有侧链混音。

`master.duck_music:{"mode":"envelope","depth_db":-9,"lead":0.12,"release":0.35,"merge_gap":0.3}` 按已定位的发声窗口生成连续让位曲线，合并相邻句间短空隙。它与音乐事件自身的音量设计叠加；试听后选择深度、提前量与释放，不把示例数值当所有曲目的固定混音。

后一个 CUT 的执行参数可写 `transition_in:{"type":"fade","duration":0.25}`。硬切用 cut，其他已有类型包括 fadeblack、dissolve、wipeleft/wiperight、slideleft/slideright、smoothleft/smoothright。按表演与画面关系选用；重叠长度从总时长扣除，字幕和音频锚点一起换算。

`grade`、`effects`、`overlays` 采用 hypit 现有本地后期参数，见其 `references/production/editing-and-finishing.md`。旧版画面文字面板仍走原 Remotion 路线；分轨时将需要的图形明确作为 overlays 接入，不让说明文字冒充已执行效果。

## 同一计划完成预览与交付

```text
python <skill>/scripts/edit_tool.py plan <EP> --project-root <project>
python <skill>/scripts/edit_tool.py preview <EP> --project-root <project>
python <skill>/scripts/edit_tool.py render <EP> --project-root <project>
python <skill>/scripts/edit_tool.py verify <EP> --project-root <project>
```

预览输出低清 MP4 和可直接打开的 `剪辑预览.html`；点击镜号跳到成片位置。它是一次性本地报告，不启动服务器。预览与正式版使用相同源窗、声画事件和 cue，只改变画布大小。

分段、底片、混音和字幕分别缓存，修改字幕可复用底片与混音；素材或参数变化时重算相关消费者。局部执行遇到明确的临时资源占用最多重试一次，日志保留两次结果。

先看听关键段，修正源窗、声音或字的位置，再连续看整场情绪与结尾。已有完整交付授权时主动完成这轮修订，不新增逐镜审批。
