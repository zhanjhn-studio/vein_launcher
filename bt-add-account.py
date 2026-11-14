#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""新建 account.zhanjhn.cn 站点，listen 81，PHP-82"""
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


DOMAIN = "account.zhanjhn.cn"
PORT = 81
PHPVER = "82"

site = panelSite()

print("=" * 60)
print("创建站点:", DOMAIN)
print("=" * 60)

if public.M("sites").where("name=?", (DOMAIN,)).count():
    print("站点已存在，跳过创建")
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
        "ps": "账号管理",
        "path": "/www/wwwroot/" + DOMAIN,
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

print()
print("=" * 60)
print("确保 PHP-82")
print("=" * 60)
try:
    r = site.SetPHPVersion(Obj({"siteName": DOMAIN, "version": PHPVER}))
    print("返回:", json.dumps(r, ensure_ascii=False) if isinstance(r, dict) else r)
except Exception as e:
    print("异常:", e)

print()
print("=" * 60)
print("结果检查")
print("=" * 60)

conf = "/www/server/panel/vhost/nginx/{}.conf".format(DOMAIN)
if os.path.exists(conf):
    c = public.readFile(conf) or ""
    for line in c.splitlines():
        s = line.strip()
        if s.startswith("listen ") or s.startswith("server_name ") or "root " in s or "enable-php" in s:
            print("  ", s)
else:
    print("  配置不存在！")
