"""构建原版 MLC Java agent（无 mod 加载器）。

流程：
  1. 下载并缓存 1.20.1 官方 client mappings
  2. 解析出 Minecraft / LocalPlayer / 实体等混淆名
  3. 用这些名字渲染 Java 源码（反射访问，不依赖 Mixin）
  4. javac 编译 + jar 打包（Premain-Class）

产物：VeinLauncher/agent/vein-agent-<version>.jar
用法：游戏启动参数加 -javaagent:<jar> -Dvein.agent.port=25566
"""

from __future__ import annotations

import json
import re
import shutil
import ssl
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(r"Z:\Vein Launche")
CACHE = ROOT / "build" / "mappings"
AGENT_DIR = ROOT / "VeinLauncher" / "agent"
SRC_DIR = ROOT / "build" / "agent-src"
VERSION = "1.20.1"
MANIFEST = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"
UA = {"User-Agent": "VeinLauncher/0.5"}
JDK = ROOT / "VeinLauncher" / "java" / "temurin-17" / "jdk-17.0.21+9" / "bin"

JAVA_TEMPLATE = r'''package vein.agent;

import java.io.*;
import java.lang.reflect.*;
import java.net.*;
import java.nio.charset.StandardCharsets;
import java.util.*;

/**
 * Vein Launcher MLC agent —— 原版（无加载器）游戏内桥。
 *
 * 通过反射读取 Minecraft 客户端状态，并在本地 127.0.0.1:port 提供 JSON 行协议：
 *   {"cmd":"ping"}                    -> {"ok":true}
 *   {"cmd":"state"}                   -> {"inGame":bool,"player":{...}}
 *   {"cmd":"chat","text":"/time set day"} -> {"ok":true}
 */
public final class VeinAgent {
    private static final String MC_CLASS = "__MC_CLASS__";
    private static final String F_INSTANCE = "__F_INSTANCE__";
    private static final String F_PLAYER = "__F_PLAYER__";
    private static final String F_LEVEL = "__F_LEVEL__";
    private static final String M_GETX = "__M_GETX__";
    private static final String M_GETY = "__M_GETY__";
    private static final String M_GETZ = "__M_GETZ__";
    private static final String M_HP = "__M_HP__";
    private static final String M_FOOD = "__M_FOOD__";
    private static final String M_NAME = "__M_NAME__";
    private static final String M_CHAT = "__M_CHAT__";
    private static final String M_CONNECTION = "__M_CONNECTION__";
    private static final String M_GETSTRING = "__M_GETSTRING__";
    private static final String M_DIMENSION = "__M_DIMENSION__";

    public static void premain(String args, java.lang.instrument.Instrumentation inst) {
        int port = Integer.getInteger("vein.agent.port", 25566);
        Thread server = new Thread(() -> serve(port), "vein-agent");
        server.setDaemon(true);
        server.start();
        System.out.println("[vein-agent] listening on 127.0.0.1:" + port);
    }

    private static void serve(int port) {
        try (ServerSocket socket = new ServerSocket(port, 16, InetAddress.getByName("127.0.0.1"))) {
            while (true) {
                try (Socket client = socket.accept()) {
                    handle(client);
                } catch (Exception ignored) {
                }
            }
        } catch (Exception e) {
            System.out.println("[vein-agent] server failed: " + e);
        }
    }

    private static void handle(Socket client) throws IOException {
        BufferedReader in = new BufferedReader(new InputStreamReader(client.getInputStream(), StandardCharsets.UTF_8));
        PrintWriter out = new PrintWriter(new OutputStreamWriter(client.getOutputStream(), StandardCharsets.UTF_8), true);
        String line;
        while ((line = in.readLine()) != null) {
            String response;
            try {
                response = dispatch(line);
            } catch (Throwable t) {
                response = "{\"ok\":false,\"error\":\"" + escape(String.valueOf(t)) + "\"}";
            }
            out.println(response);
        }
    }

    private static String dispatch(String raw) {
        String cmd = field(raw, "cmd");
        if (cmd == null) return "{\"ok\":false,\"error\":\"missing cmd\"}";
        switch (cmd) {
            case "ping": return "{\"ok\":true,\"agent\":\"vein\"}";
            case "state": return state();
            case "chat": {
                String text = field(raw, "text");
                if (text == null || text.isEmpty()) return "{\"ok\":false,\"error\":\"empty text\"}";
                try {
                    sendChat(text);
                    return "{\"ok\":true}";
                } catch (Exception exc) {
                    return "{\"ok\":false,\"error\":\"" + escape(String.valueOf(exc)) + "\"}";
                }
            }
            default: return "{\"ok\":false,\"error\":\"unknown cmd\"}";
        }
    }

    private static Object mc() throws Exception {
        Class<?> cls = Class.forName(MC_CLASS);
        Field field = cls.getDeclaredField(F_INSTANCE);
        field.setAccessible(true);
        return field.get(null);
    }

    private static Object player() throws Exception {
        Object mc = mc();
        if (mc == null) return null;
        Field field = mc.getClass().getDeclaredField(F_PLAYER);
        field.setAccessible(true);
        return field.get(mc);
    }

    @SuppressWarnings("unchecked")
    private static String state() {
        try {
            Object player = player();
            if (player == null) return "{\"inGame\":false}";
            Object x = invoke(player, M_GETX, 0);
            Object y = invoke(player, M_GETY, 0);
            Object z = invoke(player, M_GETZ, 0);
            Object hp = invoke(player, M_HP, 0);
            Object nameComponent = invoke(player, M_NAME, 0);
            String name = String.valueOf(nameComponent);
            try {
                name = String.valueOf(invoke(nameComponent, M_GETSTRING, 0));
            } catch (Throwable ignored) {
            }
            Object level = level();
            String dim = "";
            if (level != null) {
                try {
                    dim = String.valueOf(invoke(level, M_DIMENSION, 0));
                    int slash = dim.indexOf(" / ");
                    if (slash >= 0) {
                        dim = dim.substring(slash + 3);
                        if (dim.endsWith("]")) dim = dim.substring(0, dim.length() - 1);
                    }
                } catch (Throwable ignored) {
                    dim = String.valueOf(level);
                }
            }
            return "{\"inGame\":true,\"player\":{"
                + "\"name\":\"" + escape(name) + "\","
                + "\"x\":" + num(x) + ",\"y\":" + num(y) + ",\"z\":" + num(z) + ","
                + "\"health\":" + num(hp) + ",\"dimension\":\"" + escape(dim) + "\"}}";
        } catch (Throwable t) {
            return "{\"inGame\":false,\"error\":\"" + escape(String.valueOf(t)) + "\"}";
        }
    }

    private static Object level() {
        try {
            Object mc = mc();
            Field field = mc.getClass().getDeclaredField(F_LEVEL);
            field.setAccessible(true);
            return field.get(mc);
        } catch (Throwable t) {
            return null;
        }
    }

    private static void sendChat(String text) throws Exception {
        Object mc = mc();
        if (mc == null) throw new IllegalStateException("game not ready");
        Object connection = invoke(mc, M_CONNECTION, 0);
        if (connection == null) throw new IllegalStateException("not connected");
        String command = text.startsWith("/") ? text.substring(1) : text;
        invoke(connection, M_CHAT, 1, new Class<?>[]{String.class}, new Object[]{command});
    }

    private static Method findMethod(Class<?> cls, String name, int argc) {
        while (cls != null) {
            for (Method method : cls.getDeclaredMethods()) {
                if (method.getName().equals(name) && method.getParameterCount() == argc) return method;
            }
            for (Class<?> iface : cls.getInterfaces()) {
                Method found = findMethod(iface, name, argc);
                if (found != null) return found;
            }
            cls = cls.getSuperclass();
        }
        return null;
    }

    private static Object invoke(Object target, String name, int argc, Class<?>[] types, Object[] args) throws Exception {
        Method method = findMethod(target.getClass(), name, argc);
        if (method == null) throw new NoSuchMethodException(name);
        method.setAccessible(true);
        return method.invoke(target, args);
    }

    private static Object invoke(Object target, String name, int argc) throws Exception {
        return invoke(target, name, argc, new Class<?>[0], new Object[0]);
    }

    private static String num(Object value) {
        if (value instanceof Number) return String.valueOf(((Number) value).doubleValue());
        return "0";
    }

    private static String escape(String value) {
        return value.replace("\\", "\\\\").replace("\"", "\\\"").replace("\n", "\\n").replace("\r", "");
    }

    private static String field(String raw, String key) {
        String pattern = "\"" + key + "\"\\s*:\\s*\"((?:[^\"\\\\]|\\\\.)*)\"";
        java.util.regex.Matcher m = java.util.regex.Pattern.compile(pattern).matcher(raw);
        return m.find() ? m.group(1).replace("\\\"", "\"").replace("\\\\", "\\") : null;
    }
}
'''


def fetch(url: str, timeout: int = 180) -> bytes:
    request = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.read()
    except ssl.SSLError:
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        with urllib.request.urlopen(request, timeout=timeout, context=context) as response:
            return response.read()


def mappings_path() -> Path:
    CACHE.mkdir(parents=True, exist_ok=True)
    target = CACHE / f"{VERSION}-client.txt"
    if target.is_file() and target.stat().st_size > 1_000_000:
        return target
    manifest = json.loads(fetch(MANIFEST))
    entry = next(v for v in manifest["versions"] if v["id"] == VERSION)
    meta = json.loads(fetch(entry["url"]))
    url = meta["downloads"]["client_mappings"]["url"]
    print("downloading mappings:", url)
    target.write_bytes(fetch(url))
    return target


def parse(text: str):
    classes: dict[str, str] = {}
    fields: dict[str, dict[str, str]] = {}
    methods: dict[str, dict[str, str]] = {}
    current = None
    for line in text.splitlines():
        if not line.startswith("    "):
            if " -> " in line:
                left, _, right = line.partition(" -> ")
                name = left.strip()
                obf = right.strip().rstrip(":")
                classes[name] = obf
                current = name
            continue
        body = line.strip()
        if " -> " not in body or current is None:
            continue
        left, _, right = body.partition(" -> ")
        obf = right.strip()
        left = left.strip()
        if "(" in left:
            m = re.match(r"(\S+)\s+(\S+)\(", left)
            if m:
                methods.setdefault(current, {}).setdefault(m.group(2), obf)
        else:
            parts = left.split()
            if len(parts) == 2:
                fields.setdefault(current, {})[parts[1]] = obf
    return classes, fields, methods


def need(classes, fields, methods, cls: str, field: str | None = None, method: str | None = None) -> str:
    if field:
        value = fields.get(cls, {}).get(field)
        if not value:
            raise SystemExit(f"mapping missing: {cls}.{field}")
        return value
    if method:
        value = methods.get(cls, {}).get(method)
        if not value:
            raise SystemExit(f"mapping missing: {cls}.{method}()")
        return value
    value = classes.get(cls)
    if not value:
        raise SystemExit(f"mapping missing class: {cls}")
    return value


def main() -> int:
    raw = mappings_path().read_text(encoding="utf-8", errors="replace")
    classes, fields, methods = parse(raw)

    tokens = {
        "MC_CLASS": need(classes, fields, methods, "net.minecraft.client.Minecraft"),
        "F_INSTANCE": need(classes, fields, methods, "net.minecraft.client.Minecraft", field="instance"),
        "F_PLAYER": need(classes, fields, methods, "net.minecraft.client.Minecraft", field="player"),
        "F_LEVEL": need(classes, fields, methods, "net.minecraft.client.Minecraft", field="level"),
        "M_GETX": need(classes, fields, methods, "net.minecraft.world.entity.Entity", method="getX"),
        "M_GETY": need(classes, fields, methods, "net.minecraft.world.entity.Entity", method="getY"),
        "M_GETZ": need(classes, fields, methods, "net.minecraft.world.entity.Entity", method="getZ"),
        "M_HP": need(classes, fields, methods, "net.minecraft.world.entity.LivingEntity", method="getHealth"),
        "M_CONNECTION": need(classes, fields, methods, "net.minecraft.client.Minecraft", method="getConnection"),
        "M_NAME": need(classes, fields, methods, "net.minecraft.world.entity.Entity", method="getName"),
        "M_CHAT": need(classes, fields, methods, "net.minecraft.client.multiplayer.ClientPacketListener", method="sendCommand"),
        "M_GETSTRING": need(classes, fields, methods, "net.minecraft.network.chat.Component", method="getString"),
        "M_DIMENSION": need(classes, fields, methods, "net.minecraft.world.level.Level", method="dimension"),
    }
    print("tokens:", json.dumps(tokens, ensure_ascii=False))

    src = JAVA_TEMPLATE
    for key, value in tokens.items():
        src = src.replace(f"__{key}__", value)

    SRC_DIR.mkdir(parents=True, exist_ok=True)
    package_dir = SRC_DIR / "vein" / "agent"
    package_dir.mkdir(parents=True, exist_ok=True)
    java_file = package_dir / "VeinAgent.java"
    java_file.write_text(src, encoding="utf-8")

    classes_dir = SRC_DIR / "classes"
    if classes_dir.exists():
        shutil.rmtree(classes_dir)
    classes_dir.mkdir(parents=True)
    javac = JDK / "javac.exe"
    jar = JDK / "jar.exe"
    result = subprocess.run(
        [str(javac), "-encoding", "UTF-8", "-d", str(classes_dir), str(java_file)],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(result.stdout[-3000:])
        print(result.stderr[-3000:])
        return 1

    AGENT_DIR.mkdir(parents=True, exist_ok=True)
    manifest = SRC_DIR / "MANIFEST.MF"
    manifest.write_text("Manifest-Version: 1.0\nPremain-Class: vein.agent.VeinAgent\n\n", encoding="utf-8")
    target = AGENT_DIR / f"vein-agent-{VERSION}.jar"
    result = subprocess.run(
        [str(jar), "cfm", str(target), str(manifest), "-C", str(classes_dir), "."],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(result.stderr[-2000:])
        return 1
    print(f"built agent: {target} ({target.stat().st_size / 1024:.0f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
