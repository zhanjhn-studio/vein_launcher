#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把已建好的 nginx 站点登记进宝塔面板数据库，让面板列表可见。"""
import sqlite3
import time

DB = '/www/server/panel/data/default.db'

SITES = [
    ("lhsy.online",      "/www/wwwroot/lhsy.online"),
    ("file.lhsy.online", "/www/wwwroot/file.lhsy.online"),
    ("api.lhsy.online",  "/www/wwwroot/api.lhsy.online"),
    ("api.zhanjhn.cn",   "/www/wwwroot/api.zhanjhn.cn"),
]

now = time.strftime("%Y-%m-%d %H:%M:%S")

conn = sqlite3.connect(DB)
cur = conn.cursor()

for name, path in SITES:
    # 幂等：已存在就跳过
    row = cur.execute("SELECT id FROM sites WHERE name=?", (name,)).fetchone()
    if row:
        print(f"  已存在，跳过: {name} (id={row[0]})")
        site_id = row[0]
    else:
        cur.execute(
            'INSERT INTO sites (name, path, status, "index", ps, addtime) '
            "VALUES (?, ?, ?, ?, ?, ?)",
            (name, path, "1", "index.html index.php", "", now),
        )
        site_id = cur.lastrowid
        print(f"  已写入 sites: {name} (id={site_id}) -> {path}")

    # 域名绑定表
    drow = cur.execute(
        "SELECT id FROM domain WHERE pid=? AND name=?", (site_id, name)
    ).fetchone()
    if drow:
        print(f"    已存在域名绑定，跳过: {name}")
    else:
        cur.execute(
            "INSERT INTO domain (pid, name, port, addtime) VALUES (?, ?, ?, ?)",
            (site_id, name, 81, now),
        )
        print(f"    已写入 domain: {name} -> port 81")

conn.commit()

print("\n=== 登记结果 ===")
print(f"{'id':<4} {'站点名':<22} {'状态':<6} 根目录")
for r in cur.execute("SELECT id, name, status, path FROM sites ORDER BY id"):
    print(f"{r[0]:<4} {r[1]:<22} {r[2]:<6} {r[3]}")

print("\n域名绑定：")
for r in cur.execute("SELECT pid, name, port FROM domain ORDER BY pid"):
    print(f"  pid={r[0]:<4} {r[1]:<22} port={r[2]}")

conn.close()
