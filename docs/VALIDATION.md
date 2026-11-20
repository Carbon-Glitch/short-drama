# Validation scope / 验证范围

Snapshot: 2026-11-20. These are development observations, not performance or audience benchmarks. 本页记录开发阶段实测，不是效果排名或留存承诺。

| Area / 范围 | Observed / 结果 | Limit / 边界 |
|---|---|---|
| Native export / 原生导出 | 35.000 s, 1080×1920, 24fps, 840 frames, H.264/AAC | One existing episode; no new H3 generation in this test / 使用已有素材 |
| Human + Agent editing / 共编 | Manual style survived UI → Agent patch → reopen | Targeted tested edits, not every possible operation / 定向验证 |
| Handoff / 交接 | Source edits, missing adopted layers and source replacements surfaced for review | Structural coverage does not prove semantic quality / 承载检查不等于审美验收 |
| Audio / 声音 | EQ, pan and envelope migration; synthetic PCM test measured a −12 dB music-gain change after moving dialogue | Synthetic signal measurement, not an audience listening score / 非观众听感评分 |
| H3 text / 提示词 | 3 synthetic scenes, 22 selected decisions reached compiled text and offline request fields | No online video submission; mock route/schema/upload fixtures / 无实际生成 |
| Writer context / 写作上下文 | 3 scenes × 5 modes = 15 guide-loading checks | Includes a customized local Hypit writer not bundled here / 配套 writer 补丁未包含 |

T2VA text uses `integrated_multimodal_description`, `overall_soundscape`, `non_diegetic_music`. Ref2VA uses all six sections: `subject_definitions`, `summary`, `retention_analysis`, `detailed_description`, `overall_soundscape`, `non_diegetic_music`. `detailed_description` alone is not the complete Ref2VA prompt.

The primary path uses the current Agent for creative decisions. The optional Hypit writer-context integration was tested in the developer's paired installation; publishing these 11 skills does not install that separate patch. 本仓库主流程由当前 Agent 阅读技能并创作，不能把本机配套测试等同于所有新环境都具备该可选集成。

Source snapshot hashes are in [source-manifest.json](source-manifest.json). They record the 11 shared skill directories copied for this release, excluding caches. Private episode media, credentials and runtime state are not distributed. This document summarizes development records; it is not a bundled end-to-end reproducibility package.

Fresh-machine installation, broad cross-genre generated-video quality and audience retention remain unmeasured. Legacy effect migration reports unsupported fields rather than promising universal lossless conversion. 正式交付仍需观看实际画面与判断声音；本地结构检查不能代替这一步。

## Model-aware joins update / 模型分段与接镜补强

- Three synthetic scene documents with generation/join notes passed existing document validation and the real offline H3 request compiler; no provider request was submitted.
- Native OpenFilm rendered a 2-second, 48-frame, 540×960 preview and automatically generated its join-review page. Browser playback and frame stepping were checked.
- The existing 35-second development film produced 13 visual-layer boundary candidates. These include layer transitions, not necessarily 13 editorial cuts or defects.
- Targeted checks covered native media kinds, speed/source-window mapping, overlapping layers, hidden/disabled/audio exclusions, non-gating handoff notes and stale-project rejection.
- No new H3 generation or audience test was run. The update does not add latent-context generation, reopen video-reference inputs or promise seamless output. Private development media and local test artifacts are not included.

分镜中的「生成安排／接镜」是可读制作说明，沿现有文档版本追踪；没有新增逐项审批。接点页使用已导出的原生影片，不引入第二套合成器或权威时间线。
