#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把站点的 PHP 版本切换到 82（使用宝塔官方 SetPHPVersion 接口）。"""
import sys, os, json, traceback

os.chdir("/www/server/panel")
sys.path.insert(0, "/www/server/panel")
sys.path.insert(0, "/www/server/panel/class")

import public
from panelSite import panelSite


class Obj(object):
    """兼容属性访问与 .get()"""
    def __init__(self, d):
        self.__dict__.update(d)

    def get(self, key, default=None):
        return self.__dict__.get(key, default)

    def __contains__(self, key):
        return key in self.__dict__


DOMAINS = [
    "lhsy.online",
    "file.lhsy.online",
    "api.lhsy.online",
    "api.zhanjhn.cn",
]

PHPVER = "82"

site = panelSite()

for d in DOMAINS:
    print("\n" + "=" * 50)
    print("切换 {} -> PHP-{}".format(d, PHPVER))
    print("=" * 50)

    conf = "/www/server/panel/vhost/nginx/{}.conf".format(d)
    if not os.path.exists(conf):
        print("  配置不存在，跳过")
        continue

    # 当前引用
    cur = public.readFile(conf) or ""
    import re
    m = re.search(r"enable-php-[\w-]+\.conf", cur)
    print("  当前:", m.group() if m else "(无)")

    try:
        get = Obj({
            "siteName": d,
            "version": PHPVER,
        })
        r = site.SetPHPVersion(get)
        print("  返回:", json.dumps(r, ensure_ascii=False) if isinstance(r, dict) else r)
    except Exception as e:
        print("  异常:", e)
        traceback.print_exc()

print("\n\n" + "=" * 50)
print("最终检查")
print("=" * 50)
import re
for d in DOMAINS:
    conf = "/www/server/panel/vhost/nginx/{}.conf".format(d)
    c = public.readFile(conf) or ""
    m = re.search(r"enable-php-[\w-]+\.conf", c)
    print("  {:<22} -> {}".format(d, m.group() if m else "(无)"))

print("\n数据库 version 字段:")
for x in public.M("sites").select():
    print("  id={} {:<22} version={!r}".format(x["id"], x["name"], x.get("version")))
