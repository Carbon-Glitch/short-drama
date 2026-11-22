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

## Design-stage restructuring / 设计阶段重构 — 2026-11-21

- The installed suite now contains 12 skills. The five creative Markdown documents remain the source of truth; scene design lives in the existing visual-design document.
- 15 routing/version cases passed: missing assets/storyboards, prompt-only input, empty shot headings, design reuse, source changes, legacy projects and explicit text-to-video.
- Three synthetic five-document cases passed existing validation and real offline H3 compilation. Four staging additions per case reached the request text; no video generation was submitted.
- All 12 added staging events reached OpenFilm handoff. Rhythm and exit-state notes were retained; design edits invalidated the earlier handoff.
- Scene/asset section isolation, repeated staging fields and multi-scene order were checked. The 17 existing core self-tests passed.
- Optional Hypit writer context checks used the paired local installation: design-role messages received the design guides; H3-role messages received the selected scene design without repeating recent-work research. This separate Hypit writer change is not bundled here.
- At this snapshot, rich audiovisual design and longer-clip preferences were creative defaults. Their effect on generated-video quality or audience retention was not established by these structural checks; the 2026-11-22 revision below replaces the richness default with content- and audience-specific choices.

本次发布包含技能、资料与执行脚本，未包含私人制作工程、视频、凭据或运行时状态。近期作品搜索集中到设计阶段；其他阶段按问题查影视工业方法。

## Experience and director review / 体验与导演审读 — 2026-11-22

- All 12 skill directories in the release copy passed skill validation. The six skills with numbered Python self-tests passed 44 cases in total; the short-drama-edit self-test suite also passed.
- A synthetic breakfast-shop scene passed the complete five-document validator using the release-copy script. It uses four subject references and one 16-second multi-shot prompt, with no per-shot keyframes and no generated media.
- The text test checked early expectation, two visible payoffs, attention handoff, prop counts, hand/prop continuity, focus and sound. It does not establish generated-image quality, audience preference or retention.
- README and README.en now describe the current order: experience design → text storyboard → director-experience review → minimal subject assets → video prompts. No new creative document or review artifact was added.

本轮还复核了设计路由与版本用例、五文档传递用例和视频单正文回归；未向图片或视频服务提交任务，也未上传短测项目、本机路径、缓存或凭据。
