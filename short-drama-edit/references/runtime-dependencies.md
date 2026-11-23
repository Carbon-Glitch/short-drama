# 运行时依赖

基础 short-drama Python 工具只使用标准库，要求 Python 3.9+。本机验证版本为 Python 3.12.10。
不要因为可选功能未安装就把基础剧本、资产、分镜或提示词工作判为不可用。

## 媒体执行

- `ffmpeg` 与 `ffprobe`：渲染、探测和部分验收所需；本机验证为 9.0.2。缺失时对应功能明确报未测，不静默跳过。
- `faster-whisper`：可选的本地语音识别后端，使用本目录的 `requirements-optional.txt` 安装；本机验证为 1.2.1。
- `openai-whisper` CLI 或 `whisper.cpp`：另外两种可选 ASR 路径，不是基础依赖。OpenAI Whisper 当前未安装。

## Remotion 字幕与画面文字

`assets/remotion/package.json` 固定 React 19.0.0、Remotion 4.0.418 和字体版本，并有 `package-lock.json`。
在该目录运行 `npm ci`，再按 [Remotion 叠层](../assets/remotion/README.md) 使用。当前验证 Node 24.13.0、npm 11.6.2；
这些只是已验证版本，不声明为最低版本。`node_modules/` 不进入版本控制。

## OpenFilm

`assets/openfilm-plugin/package.json` 当前没有第三方 npm 依赖，不需要为其单独安装包。
OpenFilm 的外部运行时、访问方式和所需本地文件按现有 OpenFilm 工作流检查，不从 package.json 推断已经可用。
