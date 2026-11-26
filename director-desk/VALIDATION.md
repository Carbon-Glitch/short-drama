# 验证范围

已验证本地项目创建与导入、编辑/自动保存/撤销、稳定引用和局部待复核、参考图/音色设置、文本分镜与视频覆盖、画布引用连线、外部文档/素材合并、项目导出恢复、OpenFilm初剪与本机原生导出。独立测试副本完成过一次真实Codex改稿。

自动测试使用本地夹具验证生产协议，另有实际适配器的离线参数编译；这不代表真实远端生成服务、账号权限或模型画面/声音质量已经验收。尚无完整离线依赖安装包。新增外部整集自动接续、无编号标题的身份迁移等仍待完善。

源码验证（仓库根目录）：

```powershell
python -X utf8 short-drama/scripts/selftest.py
python -X utf8 -m unittest discover -s director-desk/backend -q
node --test director-desk/web/src/*.test.js
npm --prefix director-desk/web run build
```

部分原生剪辑测试需要本机OpenFilm/FFmpeg，不具备依赖时会跳过。各项测试只证明其覆盖的契约，不能代替实际创作验片。
