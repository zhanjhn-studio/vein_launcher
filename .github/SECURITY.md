# 安全策略 / Security Policy

## 支持的版本

仅**最新发布版本**获得安全修复（当前为 `v0.1.0`）。旧版本请先升级，再确认问题是否仍然存在。

## 如何报告漏洞

**不要开公开 issue，也不要在任何公开渠道贴 token。** 请使用以下私密渠道之一：

- 邮箱：`security@zhanjhn-studio.example`（占位地址，正式邮箱由负责人替换）
- 或私信仓库维护者 `@macbo2013`

报告请包含：受影响版本、复现步骤、影响面（账号令牌泄露 / 任意文件读写 / 命令注入 / 启动参数注入等）、
是否已在公开场合暴露，以及可用于验证的最小样本（**脱敏后**）。

## 请勿公开的内容

- Microsoft / LittleSkin 的 access token、refresh token、设备码
- 日志中的账号 UUID 与邮箱（`VeinLauncher/log/` 下的文件请先脱敏再贴）
- Azure 应用配置（client id / client secret）
- 内部文档 `*.docx`（仅本地留存，不入库、不上传）

## 响应时间

我们会在 **3 个工作日内**确认收到，并在修复版本发布后于 Release Notes 中致谢（如需匿名请注明）。
