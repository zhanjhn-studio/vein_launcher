# 发布检查清单 / Release Checklist

> **红线**：未经负责人明确指令，**不得**创建 / 修改 Release，**不得**删除任何分支、tag 或 release 资产。
> 自动化发布（`release.yml`）**尚未批准**；本清单是当前唯一认可的发布流程。
> 本清单不涉及 `.docx`：内部文档始终本地留存，不入库、不上传。

## 0. 前置确认

- [ ] 负责人已明确下达「发布 vX.Y.Z」指令（团队沟通中有记录）
- [ ] `main` 上待发布提交已全部合并，工作区干净（`git status` 无输出）
- [ ] `python -m unittest discover -s tests` 全绿（贴 `Ran N tests in Xs OK`）
- [ ] `python -m compileall -q vein_launcher` 无输出、退出码 0

## 1. 版本号与基线

- [ ] 版本号与 tag 一致：`v0.x.y`（当前 0.x 阶段）
- [ ] 版本号来源同步：`vein_launcher/presentation/context.py`
- [ ] `teamwork.md` 的「Current baseline」更新（版本、Release 链接、测试数）
- [ ] `RELEASE_NOTES.md` 写好中英双语正文 —— Release body **直接取自该文件**，不再另写
- [ ] 记录发布基准提交：`git rev-parse HEAD` → `<sha>`（tag 必须打在这个提交上）

## 2. 构建

- [ ] 前端：`vein_launcher/presentation/webui/build.ps1`（需要 esbuild）
- [ ] 打包：PyInstaller onedir（`packaging/`），产物 `packaging/dist/VeinLauncher/`
- [ ] 冒烟：解压即用 → 欢迎页 → 设置 → 关于 可打开；离线账号能启动一次游戏
- [ ] 压缩为 `VeinLauncher-<version>-win64.zip`（文件名必须与 `latest.json` 的 `asset` **完全一致**）
- [ ] 生成 `latest.json`，字段必须齐全：
      `version` / `tag` / `name` / `asset` / `url` / `html_url` / `notes`；
      `url` 必须是 `https://github.com/zhanjhn-studio/vein_launcher/releases/download/v<version>/<asset>`

## 3. 上传

- [ ] 先建 **draft** Release，tag 指向第 1 步记录的提交
- [ ] 上传**两个**资产：`VeinLauncher-<version>-win64.zip` + `latest.json`（缺一不可 ——
      更新器在 GitHub API 限流时回退到 `releases/latest/download/latest.json`）
- [ ] 正文粘贴 `RELEASE_NOTES.md`，勾选 **Set as the latest release**
- [ ] 从 draft 发布为正式 Release
- [ ] **不删除、不覆盖**任何既有 release 的资产（包括 v0.1.0）

## 4. 发布后校验（立即做，不要等用户反馈）

- [ ] `latest.json` 兜底路径可访问且版本正确：

  ```powershell
  curl.exe -sL https://github.com/zhanjhn-studio/vein_launcher/releases/latest/download/latest.json
  ```

  返回的 `version` 必须是新版本
- [ ] zip 直链存在且大小与本地一致：

  ```powershell
  curl.exe -sIL https://github.com/zhanjhn-studio/vein_launcher/releases/download/v<version>/VeinLauncher-<version>-win64.zip
  ```

- [ ] 用上一版启动器执行一次「检查更新」，确认能发现新版本并开始下载（不要求装完）
- [ ] 从 GitHub 下载 zip、解压、启动一次（验证上传未截断）

## 5. 留痕

- [ ] `teamwork.md` 追加记录：版本、tag、commit、zip sha256 / size、latest.json sha256、发布时间
- [ ] 本表（本地留存，不入库）：

| 项 | 值 |
|---|---|
| tag / commit | `vX.Y.Z` / `<sha>` |
| zip | `VeinLauncher-<version>-win64.zip` |
| zip sha256 | `Get-FileHash .\VeinLauncher-<version>-win64.zip -Algorithm SHA256` |
| zip size | `<bytes>` |
| latest.json sha256 | `Get-FileHash .\latest.json -Algorithm SHA256` |

## 回滚

已发布版本有阻断性问题时：**不要删除资产**。先把上一版重新标记为 Latest，再尽快发修复版；
删除 Release / 资产 / tag 必须由负责人确认后单独执行。
