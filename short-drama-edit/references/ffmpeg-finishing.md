# FFmpeg 后期执行工具

规格不一致、对白/音乐需要分开处理、最终响度、明确的颜色处理或局部抽帧时读取。
艺术取舍由当前分镜和剪辑单决定；工具只执行已选参数。常规剪辑继续使用 `edit_tool.py`。

## 入口

```text
python <skill>/scripts/ffmpeg_finish.py --ffmpeg-bin <ffmpeg及ffprobe所在目录> <工具> <参数>
```

Python 3.10+；后端要求 FFmpeg 6.1+，具体滤镜取决于实际构建。FFmpeg 已在 PATH 时省略 `--ffmpeg-bin`，
也可在当前进程设置 `SHORT_DRAMA_FFMPEG_BIN`。这不会修改系统 PATH、账户配置或安装另一个skill。
`edit` 工具可在同一运行环境调用原生 `edit_tool.py`，例如 `... edit conform <EP> --project-root <项目>`。

只带入上游六个工具及其共享执行代码；`--version` 查看固定来源，`<工具> --help` 查看真实参数。
没有引入上游全套自动剪辑策略、平台预设、安装器或MCP。

| 工具 | 何时用 | 示例参数（接在工具名后） |
|---|---|---|
| `probe` | 探测实际时长、画幅、帧率、颜色/声音流 | `素材.mp4 --json` |
| `fit` | 按已选输出规格整理素材 | `素材.mp4 --width 1080 --height 1920 --fit pad --fps 24 -o 规格版.mp4 --dry-run --json` |
| `audio` | 提取/替换音轨、对白轻处理、配乐让路 | `粗剪.mp4 --music 配乐.wav --duck --music-volume -20 --duck-amount 8 --music-fade-out 0.8 -o 混音版.mp4 --dry-run --json` |
| `loudness` | 测量或按项目目标两遍归一化并复测 | `混音版.mp4 --measure-only --json`；`混音版.mp4 -I -16 --tp -1 --sample-rate 48000 -o 母版.mp4 --json` |
| `color` | 执行已选曝光/主色校正、LUT或HDR→SDR | `素材.mp4 --correct --exposure 0.2 -o 校正版.mp4 --dry-run --json` |
| `look` | 切点/事件抽帧、相邻版本并排或概览 | `母版.mp4 --at 1.2 --compare 旧版.mp4 -o 对比.png --json`；`母版.mp4 --tiles 3x2 -o 概览.png --json` |

表中数字仅用于展示调用格式，不是所有短剧的画幅、帧率、音量、响度或校正默认值。
多轨文件通过 `--audio-stream` 明确目标轨；主声音只有原生混音时，其他已有音乐/音效也可能触发ducking。

## 执行闭环

1. 只探测本次依赖的真实文件；把已决定的规格/处理写回当前剪辑单。
2. 长耗时或破坏性处理先 `--dry-run --json` 检查；探测/测量可能仍读取媒体，不承诺“完全不运行工具”。
3. 用新输出路径执行，读取退出码与JSON中的实际结果；修改图像后抽相关帧查看，修改声音后回听。
4. 混音与后期完成后再做最终响度处理，并测编码后的实际文件。源窗、裁切或帧率改变时刷新下游时间。
5. 原生 `verify` 仍测它的 `制作成果/成片/成片.mp4`；后期另存的母版必须对那个真实路径重新
   `probe`、`loudness --measure-only` 和看听，不能拿旧出口的verify当作新母版证据。

## 短剧专属取舍

- `fit` 不传 `--duration`，除非已明确选择变速/裁切。不能靠统一加速、补静帧或拉对白凑时长。
- 保留原声中已成立的对白、呼吸、拟音与空间，不默认静音重配。ASR定位字音，台词仍以剧本为准。
- `audio --fade-out` 淡掉整个混音，包括对白；只收音乐用 `--music-fade-out`。主轨触发ducking是幅度判断，
  不是角色/对白语义识别；起落时间、掩蔽和尾音仍要回听。
- 裁切先保证动作/证据/听者可读；输出规格整理在最终字幕/图形之前完成，避免后裁丢字。
- 先确认颜色空间和素材状态，再做shot matching与创意look。改颜色标签不是实际颜色变换，SDR不套Log还原。
  本子集没有接入OCIO/ACES工程，不把参考库的该能力算作本机已实现。
- 色彩和降噪只能处理可修复问题；身份漂移、错说话人、缺失接触/反应仍回对应制作阶段。
- 图集只能证明所看的帧，波形/响度只能证明测量；完整表演、对白和节奏要常速声画联合验收。

## 来源与维护

执行代码来自 `kajisho5/ffmpeg-skill` 3.10.1，固定 `f1c97cbffeac71b8fdfca2f790ceb00db3bcce65`，MIT；
原文件未改写，许可和逐文件SHA256在 `scripts/ffmpeg_backend/LICENSE` 与 `UPSTREAM.json`。
本项目新增的启动器只转发参数、临时选择工具目录、保留退出码；不声称移植了上游其余工具。
具体采纳依据见[吸收记录](absorbed-editing-skills.md)。
