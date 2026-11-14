#!/bin/bash
# 宝塔站点创建脚本 - 4 个域名，统一 listen 81
set -e

VHOST=/www/server/panel/vhost/nginx
WWWROOT=/www/wwwroot
OWNER=www:www

create_site() {
    local DOMAIN="$1"
    local ROOTDIR="$2"
    local CONF="$VHOST/${DOMAIN}.conf"

    echo "--- 创建 $DOMAIN -> $ROOTDIR ---"
    mkdir -p "$ROOTDIR"
    chown -R $OWNER "$ROOTDIR" 2>/dev/null || true

    # 首页（仅当不存在时创建，不覆盖已有内容）
    if [ ! -f "$ROOTDIR/index.html" ]; then
        cat > "$ROOTDIR/index.html" <<HTML
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>${DOMAIN}</title>
<style>
  body{margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;
       font-family:system-ui,-apple-system,"Segoe UI",sans-serif;
       background:linear-gradient(135deg,#0f172a,#1e293b);color:#e2e8f0}
  .box{text-align:center;padding:3rem 4rem;border:1px solid #334155;border-radius:16px;
       background:rgba(30,41,59,.7);backdrop-filter:blur(8px)}
  h1{margin:0 0 .6rem;font-size:2rem;letter-spacing:.02em}
  p{margin:.3rem 0;color:#94a3b8;font-size:.95rem}
  code{color:#38bdf8;background:#0f172a;padding:.15rem .45rem;border-radius:5px}
</style>
</head>
<body>
<div class="box">
  <h1>${DOMAIN}</h1>
  <p>站点已就绪</p>
  <p>根目录 <code>${ROOTDIR}</code></p>
</div>
</body>
</html>
HTML
        chown $OWNER "$ROOTDIR/index.html"
    fi

    cat > "$CONF" <<'NGINXEOF'
server
{
    listen 81;
    server_name __SERVER_NAME__;
    index index.html index.htm;
    root __ROOT_DIR__;

    #SSL-START SSL相关配置，请勿删除或修改下一行带注释的404规则
    #error_page 404/404.html;
    #SSL-END

    #ERROR-PAGE-START  错误页配置，可以注释、删除或修改
    error_page 404 /404.html;
    #ERROR-PAGE-END

    # 站点日志
    access_log  /www/wwwlogs/__SERVER_NAME__.log;
    error_log  /www/wwwlogs/__SERVER_NAME__.error.log;

    # 禁止访问的敏感文件
    location ~* (\.user.ini|\.htaccess|\.htpasswd|\.env.*|\.project|\.git|\.svn|\.DS_Store|\.log|\.sql)$
    {
        return 404;
    }

    # 静态资源缓存
    location ~ .*\.(gif|jpg|jpeg|png|bmp|swf)$
    {
        expires      30d;
        access_log off;
    }

    location ~ .*\.(js|css)?$
    {
        expires      12h;
        access_log off;
    }
}
NGINXEOF

    sed -i "s|__SERVER_NAME__|${DOMAIN}|g" "$CONF"
    sed -i "s|__ROOT_DIR__|${ROOTDIR}|g" "$CONF"
    chmod 600 "$CONF"
    echo "    配置: $CONF"
}

# 主站
create_site "lhsy.online"      "$WWWROOT/lhsy.online"

# 文件站
create_site "file.lhsy.online" "$WWWROOT/file.lhsy.online"

# lhsy 的 API
create_site "api.lhsy.online"  "$WWWROOT/api.lhsy.online"

# 另一个 zone 的 API
create_site "api.zhanjhn.cn"   "$WWWROOT/api.zhanjhn.cn"

echo
echo "=== 校验 nginx 配置 ==="
nginx -t
