#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""用宝塔自己的 AddSite 接口建站（对象式参数），保证面板可见。"""
import sys, os, json, traceback

os.chdir("/www/server/panel")
sys.path.insert(0, "/www/server/panel")
sys.path.insert(0, "/www/server/panel/class")

import public
from panelSite import panelSite

DOMAINS = [
    "lhsy.online",
    "file.lhsy.online",
    "api.lhsy.online",
    "api.zhanjhn.cn",
]


class Obj(object):
    """既支持 obj.attr 也支持 obj.get('key')，兼容宝塔 AddSite 的两种访问方式"""
    def __init__(self, d):
        self.__dict__.update(d)

    def get(self, key, default=None):
        return self.__dict__.get(key, default)

    def __getitem__(self, key):
        return self.__dict__[key]

    def __setitem__(self, key, value):
        self.__dict__[key] = value

    def __contains__(self, key):
        return key in self.__dict__


def make_get(domain, port=81):
    """构造 AddSite 需要的对象"""
    webname = json.dumps({
        "domain": domain,
        "port": str(port),
        "domainlist": [],
        "count": 0,
    }, ensure_ascii=False)
    d = {
        "webname": webname,
        "type": "HTML",
        "port": str(port),
        "ps": "",
        "path": "/www/wwwroot/" + domain,   # 必须显式指定，否则为空被当根目录
        "type_id": "0",
        "version": "00",
        "ftp": "false",
        "sql": "false",
        "codeing": "utf8",
        "set_ssl": "0",
        "force_ssl": "0",
    }
    return Obj(d)


site = panelSite()

for d in DOMAINS:
    print("\n" + "=" * 50)
    print("创建:", d)
    print("=" * 50)

    # 已存在则跳过
    n = public.M("sites").where("name=?", (d,)).count()
    if n:
        print("  已存在，跳过")
        continue

    try:
        get = make_get(d)
        r = site.AddSite(get)
        print("  返回:", json.dumps(r, ensure_ascii=False) if isinstance(r, dict) else r)
    except Exception as e:
        print("  异常:", e)
        traceback.print_exc()

print("\n\n" + "=" * 50)
print("最终检查")
print("=" * 50)
rows = public.M("sites").select()
print("站点数:", len(rows))
for x in rows:
    print("  id={}  {:<22} path={}".format(x.get("id"), x.get("name"), x.get("path")))
