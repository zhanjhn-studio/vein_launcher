#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""新建一个站点，绑定 4 个域名，listen 81，PHP-82。
   主域名 vl.zhanjhn.cn，其余 3 个作为附加域名。"""
import sys, os, json, traceback, re

os.chdir("/www/server/panel")
sys.path.insert(0, "/www/server/panel")
sys.path.insert(0, "/www/server/panel/class")

import public
from panelSite import panelSite


class Obj(object):
    def __init__(self, d):
        self.__dict__.update(d)

    def get(self, key, default=None):
        return self.__dict__.get(key, default)

    def __contains__(self, key):
        return key in self.__dict__


MAIN = "vl.zhanjhn.cn"
EXTRA = [
    "veinlauncher.zhanjhn.cn",
    "vl.lhsy.online",
    "veinlauncher.lhsy.online",
]
PORT = 81
PHPVER = "82"

site = panelSite()

print("=" * 62)
print("新建站点，绑定 4 个域名")
print("  主域名 :", MAIN)
print("  附加   :", ", ".join(EXTRA))
print("=" * 62)

if public.M("sites").where("name=?", (MAIN,)).count():
    print("站点已存在，跳过创建")
else:
    webname = json.dumps({
        "domain": MAIN,
        "port": str(PORT),
        "domainlist": EXTRA,
        "count": len(EXTRA),
    }, ensure_ascii=False)

    get = Obj({
        "webname": webname,
        "type": "PHP",
        "port": str(PORT),
        "ps": "VeinLauncher 官网",
        "path": "/www/wwwroot/" + MAIN,
        "type_id": "0",
        "version": PHPVER,
        "ftp": "false",
        "sql": "false",
        "codeing": "utf8",
        "set_ssl": "0",
        "force_ssl": "0",
    })
    try:
        r = site.AddSite(get)
        print("建站返回:", json.dumps(r, ensure_ascii=False) if isinstance(r, dict) else r)
    except Exception as e:
        print("异常:", e)
        traceback.print_exc()

# ---- 确保 PHP 82 ----
print()
print("=" * 62)
print("确保 PHP-82")
print("=" * 62)
try:
    r = site.SetPHPVersion(Obj({"siteName": MAIN, "version": PHPVER}))
    print("返回:", json.dumps(r, ensure_ascii=False) if isinstance(r, dict) else r)
except Exception as e:
    print("异常:", e)

# ---- 检查结果 ----
print()
print("=" * 62)
print("结果检查")
print("=" * 62)

conf = "/www/server/panel/vhost/nginx/{}.conf".format(MAIN)
if os.path.exists(conf):
    c = public.readFile(conf) or ""
    m = re.search(r"listen\s+([^;]+);", c)
    print("listen      :", m.group(1) if m else "?")
    m = re.search(r"server_name\s+([^;]+);", c)
    print("server_name :", m.group(1).strip() if m else "?")
    m = re.search(r"enable-php-[\w-]+\.conf", c)
    print("PHP 引用    :", m.group() if m else "?")

print()
print("域名绑定表:")
for x in public.M("domain").where("pid=?", (public.M("sites").where("name=?", (MAIN,)).getField("id"),)).select():
    print("   {:<28} port={}".format(x["name"], x["port"]))
