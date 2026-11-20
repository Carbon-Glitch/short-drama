---
name: short-drama-produce
description: 按已授权任务执行项目既有图片、视频、配音与音乐生产，检查实际素材是否兑现美术和视听设计，登记版本并接续后期。
license: MIT
---

# 确认后生产

## 创作目标与默认阅读

以“观众爱看、愿意停留”为第一性原理。先读[共同创作方式](../short-drama/references/viewer-first.md)和[影视工业核心](../short-drama/references/film-craft-core.md)，以及本阶段核心知识：

- [代表帧判断](../short-drama-image-prompts/references/lookdev-frame.md)
- [生成观察与修订](references/generation-test-matrix.md)
- [实际素材质量](../short-drama-review/references/production-quality-gates.md)

- [成像风格与感官质感](../short-drama/references/image-look-and-finishing.md)
- [按模型排生成段与接镜](../short-drama/references/model-aware-coverage-and-joins.md)

以上默认读取；同一轮已读且未变化的内容直接复用。按场面选择手法，接口和专门故障资料用到再查。

把当前文档与真实参考送入项目既有生产路线，观察结果是否兑现美术、表演与视听设计，再交给后期。写作和判断由当前 Agent 完成，沿用项目已选 H3/imagegen 等工具。

## 生产流程

1. 从当前 IMG/SHOT/MOTION 或台词/音乐条目准备 job，绑定真实参考、角色、用途、参数、数量与输出。
2. `prepare` 校验并给出精确预览。按用户对该任务的有效授权执行确认与生产；范围或成本有实质变化时再取得相应确认。
3. 按分镜「生成安排／接镜」排任务与依赖；需要前段出口的任务先观察采用结果，在既有制作记录登记文件版本、出口源时间/帧及后段引用。独立镜可并行，依赖段沿实际接受的出口接续；前段换版后重看受影响段。图片先观察角色妆造、场景与入景组合；视频再观察表演、空间、环境活动、光影和声音。先解决代表性素材暴露的问题，再扩展批次。
4. 相邻素材返回后按所选接法连看，比较动作/运镜、视线、光色与声音，裁剪能解决的先选可用窗，缺少必要过程才定向补段。选中的素材登记实际来源和采用版本，关键设计与接点观察随参考和正文传递。完整制作继续剪辑、预览与交付。
5. 中断先检查已提交任务，使用 `status/collect` 接续结果，避免重复生成。

## 来源与输入

| 任务 | 正文来源与实际用途 |
|---|---|
| 资产图、造型图、场景母版、入景帧 | `图片提示词.md` 的 `IMG-*` 可复制正文 |
| 某镜首帧 | `分镜.md` 的 `SHOT-*` 冻结关键帧正文 |
| 视频 | `视频提示词.md` 的 `MOTION-*` 正文、真实首帧与所选参考 |
| 配音 | 剧本原句、角色音色和表演要求；按既有接口字段传递 |
| 音乐 | 已定音乐意图与曲段职责，后期落实真实时长和落点 |

`source_entry` 选择当前条目；独立 OpenFilm 单集也可使用根目录同名文档。`reference_bindings` 按实际槽位与顺序说明身份、造型、地理、风格、首帧和音色用途。提示词语言沿项目与目标方言；附加的参考说明保留原有控制意图。

内置选择器读取 IMG/SHOT/MOTION；多镜分组和续接沿项目已接通的实际路径提交。接口细节、支持的 role、参数和恢复方法见[执行契约](references/adapter-contract.md)、[H3 接口](references/providers/minimax-h3-video.md)及所选供应商资料；素材来源与调用方式沿原项目配置。

## 命令

```text
python scripts/production_tool.py prepare <project> --job <job.json>
python scripts/production_tool.py confirm <project> --job-id <id> --confirmation "CONFIRM <id> <code>"
python scripts/production_tool.py run <project> --job-id <id> --adapter-config <outside-project-config.json>
python scripts/production_tool.py status <project> --job-id <id>
python scripts/production_tool.py collect <project> --job-id <id> --adapter-config <outside-project-config.json>
python scripts/production_tool.py audit <project>
```

工具保存当前输入指纹、任务状态和真实结果。adapter 配置与凭据继续由运行环境管理；既有脚本负责路径、引用与参数校验。

## 完成

实际素材已落盘并可追溯，检查过本轮设计重点，已选采用版本及需定向修订处清楚。技术完成、图像观察、动态观察和声音判断分别说明；完整任务接续后期。
