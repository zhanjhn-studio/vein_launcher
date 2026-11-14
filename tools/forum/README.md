# Vein 广场（帖子系统）

部署在 `https://api.zhanjhn.cn/`：同一目录同时提供前端页面与 `/api/*` REST 接口。

## 文件

| 文件 | 用途 |
|---|---|
| `index.html` | 广场前端（列表 / 详情 / 发帖 / 点赞，无构建步骤） |
| `api.php` | REST API（PHP 8.2 + PDO MySQL） |

服务端另有：

- `/_private.php`（webroot 内，640，nginx `deny`）——数据库连接配置
- nginx 扩展：`/www/server/panel/vhost/nginx/extension/api.zhanjhn.cn/api.conf`
  ```nginx
  location = /_private.php { deny all; return 404; }
  location ^~ /api/ { rewrite ^/api/(.*)$ /api.php last; }
  ```
- MySQL 库 `veinlauncher`：`posts / tags / post_tags / likes / rate_limits`

## 接口

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/health` | 健康检查 |
| GET | `/api/posts?tag=&sort=hot\|new&page=&limit=` | 列表（热度 = likes / (小时数+2)^1.5） |
| GET | `/api/posts/{id}` | 详情 |
| POST | `/api/posts` | 发帖 `{title, content, tags[], author}`，需 `X-Author`（或 body.author） |
| POST | `/api/posts/{id}/like` | 点赞，`X-User` 幂等 |
| GET | `/api/tags` | 标签与帖子数 |

## 约束

- 标题 4–120 字，正文 2–20000 字，标签 ≤5 个、每个 ≤32 字
- 同一 IP 每小时最多发 3 帖（`rate_limits` 表）
- 点赞用 `(post_id, user_key)` 主键保证幂等；`user_key` 默认取 IP+UA 哈希
- 正文只存纯文本/Markdown 源，前端做转义后的轻量渲染
