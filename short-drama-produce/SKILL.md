---
name: short-drama-produce
description: 按已授权任务执行项目既有图片、视频、配音与音乐生产，先用主体资产试生成，再按实际结果补充控制并登记版本。
license: MIT
---

# 确认后生产

## 创作目标与默认阅读

先把画面设计得漂亮、独特、有想象力，再以角色行为、表演和剪辑兑现故事。先读[共同创作方式](../short-drama/references/viewer-first.md)和[影视工业核心](../short-drama/references/film-craft-core.md)，以及本阶段核心知识：

- [按需代表图](../short-drama-image-prompts/references/lookdev-frame.md)
- [生成观察与修订](references/generation-test-matrix.md)
- [实际素材质量](../short-drama-review/references/production-quality-gates.md)
- [成像风格与感官质感](../short-drama/references/image-look-and-finishing.md)
- [按模型排生成段与接镜](../short-drama/references/model-aware-coverage-and-joins.md)

手艺资料：[按问题查影视工业知识](../short-drama/references/craft-knowledge.md)，同轮已读未变的内容复用。

把当前文档与真实参考送入项目既有生产路线，观察结果是否兑现美术、表演与视听设计，再交给后期。写作和判断由当前 Agent 完成，沿用项目已选 H3/imagegen 等工具。

## 生产流程

1. 按设计阶段 inspect 接续，从当前 IMG/SHOT/MOTION 或台词/音乐条目准备 job，绑定真实参考、用途、参数、数量与输出。默认使用最小主体资产和文本分镜，不为每次视频生成预先补齐所有镜头图片。
2. `prepare` 校验并给出精确预览，按用户对该任务的有效授权执行确认与生产；范围或成本实质变化时再确认。
3. 优先用全能参考组织同场长 clip，观察人物、空间、关键道具、表演、焦点、受光、反射和声音是否兑现设计。关键段先证明卖点/动作/反应可见，再扩展批次。
4. 按实际失败定向修订：文字能解决的改正文，主体漂移修对应资产，微小状态不稳补细节图，构图或切点失控补该切关键帧；复杂运动再选多关键帧、白模、动作参考视频或首尾帧。局部修好后重看整个场面。
5. 相邻素材按所选接法连看，比较动作/运镜、视线、光色与声音。需要前段出口的任务先观察采用结果，登记文件版本、出口源时间/帧及后段引用；前段换版后重看受影响段。
6. 中断先检查已提交任务，使用 `status/collect` 接续结果，避免重复生成。

## 来源与输入

| 任务 | 正文来源与实际用途 |
|---|---|
| 人物、造型、场景、道具及按需代表图 | `图片提示词.md` 的 `IMG-*` 可复制正文 |
| 需要精确控制的某镜首帧/尾帧 | `分镜.md` 中对应 `SHOT-*` 的关键帧正文 |
| 视频 | `视频提示词.md` 的 `MOTION-*` 正文与所选真实参考 |
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

实际素材已落盘并可追溯，本轮设计重点已观察，采用版本与需定向修订处清楚。技术完成、图像观察、动态观察和声音判断分别说明；完整任务接续后期。
