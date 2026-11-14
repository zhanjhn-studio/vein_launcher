#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""为 file.lhsy.online 建站并配置反向代理到 Cloudreve (127.0.0.1:5212)"""
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


DOMAIN = "file.lhsy.online"
TARGET = "http://127.0.0.1:5212"
PORT = 81

site = panelSite()

# ---------- 1. 建站点（如果不存在） ----------
print("=" * 60)
print("步骤 1: 检查/创建站点", DOMAIN)
print("=" * 60)

n = public.M("sites").where("name=?", (DOMAIN,)).count()
if n:
    print("  站点已存在，跳过创建")
else:
    get = Obj({
        "webname": json.dumps({
            "domain": DOMAIN,
            "port": str(PORT),
            "domainlist": [],
            "count": 0,
        }, ensure_ascii=False),
        "type": "PHP",
        "port": str(PORT),
        "ps": "Cloudreve 网盘",
        "path": "/www/wwwroot/" + DOMAIN,
        "type_id": "0",
        "version": "82",
        "ftp": "false",
        "sql": "false",
        "codeing": "utf8",
        "set_ssl": "0",
        "force_ssl": "0",
    })
    try:
        r = site.AddSite(get)
        print("  建站返回:", json.dumps(r, ensure_ascii=False) if isinstance(r, dict) else r)
    except Exception as e:
        print("  建站异常:", e)
        traceback.print_exc()

# ---------- 2. 添加反向代理 ----------
print()
print("=" * 60)
print("步骤 2: 添加反向代理 ->", TARGET)
print("=" * 60)

get = Obj({
    "proxyname": DOMAIN,
    "sitename": DOMAIN,
    "proxydir": "/",
    "proxydir/s": "/",
    "proxysite": TARGET,
    "todomain": "$host",
    "type": "0",
    "cache": "0",
    "subfilter": json.dumps([]),
    "advanced": "0",
    "cachetime": "0",
    "nocheck": "",
})
try:
    r = site.CreateProxy(get)
    print("  返回:", json.dumps(r, ensure_ascii=False) if isinstance(r, dict) else r)
except Exception as e:
    print("  异常:", e)
    traceback.print_exc()

# ---------- 3. 检查结果 ----------
print()
print("=" * 60)
print("步骤 3: 结果检查")
print("=" * 60)

conf = "/www/server/panel/vhost/nginx/{}.conf".format(DOMAIN)
if os.path.exists(conf):
    c = public.readFile(conf) or ""
    m = re.search(r"listen\s+(\d+)", c)
    print("  listen 端口:", m.group(1) if m else "?")
    m = re.search(r"server_name\s+([^;]+)", c)
    print("  server_name:", m.group(1) if m else "?")
    has_proxy = "proxy_pass" in c
    print("  含 proxy_pass:", has_proxy)
    # 打印代理片段
    for line in c.splitlines():
        if "proxy_pass" in line:
            print("   ->", line.strip())

print()
print("  站点列表:")
for x in public.M("sites").select():
    print("    id={} {:<22} path={}".format(x["id"], x["name"], x["path"]))
