---
name: short-drama-produce
description: 按已授权任务执行项目既有图片、视频、配音与音乐生产，先用高质感主体资产试生成，把稳表演与视觉上限后再按实际结果补充控制并登记版本。
license: MIT
---

# 确认后生产

## 目标与输入

带着本场最想看到的一拍和本集建立的视觉气场去看回片：动作发生时，观众看得清吗？修手位以后，那点迟疑还在吗？画面本身脱不脱离“廉价 AI 感”、有没有让人停下来的质感？用当前文档与真实参考沿既有路线生产，选出能剪出这场戏的高水准素材。
试拍或返修查[生成观察](references/generation-test-matrix.md)；回片时按对象查[素材质量](../short-drama-review/references/production-quality-gates.md)。

## 生产流程

1. 先读本集导演台已采用版本与未解决意见；正式提交使用 `production_tool` 的 `run` 入口以执行本集暂停设置。按设计阶段 `inspect` 接续，从当前 IMG/SHOT/MOTION 或台词/音乐条目准备 job，绑定真实参考、用途、参数、数量与输出。默认使用最小主体资产（必要时含风格定调代表图）和文本分镜，不为每次视频生成预先补齐所有镜头图片。
2. `prepare` 校验并给出精确预览，按用户对该任务的有效授权执行确认与生产；范围或成本实质变化时再确认。
3. 在已授权的试拍里，先选最影响全片、又最拿不准的一拍（新风格建议先用低成本档位验证）。先放下提示词，按原速回看片段：**除了看谁做了什么、对方怎样接招、哪一瞬让你想继续看，还要同时审视成像质感、光影层次与色彩秩序是否守住了《视觉设定.md》**。表演成立、局部失手，就留住好表演，修那一处；若画面整体显塑料平光或姿态摆拍，**绝不带着平庸质感直接扩拍整集**——先回资产图/定调代表图、或调整动作起点与机位，试出过硬观看效果再扩拍。
4. 按实际失败定向修订：文字能解决的改正文，质感太假或主体漂移先修对应资产图/定调图，微小状态不稳补细节图，构图或切点失控补该切关键帧，好表演但局部光色有瑕，在模型与实际入口支持时可走局部 `edit`；复杂运动再选多关键帧、白模、动作参考视频或首尾帧。局部修好后重看整个场面。
5. 相邻素材按所选接法连看，比较动作/运镜、视线、光色一致性与声音。需要前段出口的任务先观察采用结果，登记文件版本、出口源时间/帧及后段引用；前段换版后重看受影响段。
6. 中断先检查已提交任务，使用 `status/collect` 接续结果，避免重复生成。

## 来源与输入

| 任务 | 正文来源与实际用途 |
|---|---|
| 人物、造型、场景、道具及按需代表图 | `图片提示词.md` 的 `IMG-*` 可复制正文 |
| 需要精确控制的某镜首帧/尾帧 | `分镜.md` 中对应 `SHOT-*` 的关键帧正文 |
| 视频 | `视频提示词.md` 的实际提交条目（逐镜 MOTION / 多镜 GROUP）正文与该条目声明的真实参考 |
| 配音 | 剧本原句、角色音色和表演要求；按既有接口字段传递 |
| 音乐 | 已定音乐意图与曲段职责，后期落实真实时长和落点 |

`source_entry` 选择当前条目。`reference_bindings` 按实际槽位与顺序说明身份、造型、地理、风格、构图、首帧和音色用途；只有实际选择的素材进入 job。接口细节与恢复方法见[执行契约](references/adapter-contract.md)及所选供应商资料。

## 命令

```text
python scripts/production_tool.py prepare <project> --job <job.json>
python scripts/production_tool.py confirm <project> --job-id <id> --confirmation "CONFIRM <id> <code>"
python scripts/production_tool.py run <project> --job-id <id> --adapter-config <outside-project-config.json>
python scripts/production_tool.py status <project> --job-id <id>
python scripts/production_tool.py collect <project> --job-id <id> --adapter-config <outside-project-config.json>
python scripts/production_tool.py audit <project>
```

工具保存当前输入指纹、任务状态和真实结果。adapter 配置与凭据继续由运行环境管理。

## 完成

实际素材已落盘并可追溯，本轮设计重点与视觉质感均已观察成立，采用版本与需定向修订处清楚。交给剪辑时说明哪段能用、该从哪一拍取、还缺哪一个反应。文件已生成、画面已看过、声音已听过，分别按真实进度说。
