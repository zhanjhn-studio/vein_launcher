"""从源码提取文档需要的事实（供 gen_internal_doc.py / gen_dev_doc.py 渲染）

文档里写死的数字（RPC 方法数、导航项、测试数、版本号、插件能力…）会随代码漂移，
本模块只做「提取」，不做渲染、不做判定——渲染与判定归文档生成器。

用法：
    python tools/doc_facts.py            # 打印 Facts（JSON），锚点解析失败时退出码 1

设计：
- stdlib only（ast / re / subprocess / json），不 import 项目里的任何模块，
  所以离线、无 Qt、无网络也能跑；
- 每个提取器独立 try/except，失败写进 ``Facts.errors`` 而不是整体崩溃；
- ``check()`` 目前是占位实现，ERROR/WARN 规则由文档侧后续提供。
"""

from __future__ import annotations

import ast
import json
import re
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BRIDGE = ROOT / "vein_launcher" / "presentation" / "bridge.py"
APP_TSX = ROOT / "vein_launcher" / "presentation" / "webui" / "src" / "App.tsx"
CONTEXT = ROOT / "vein_launcher" / "presentation" / "context.py"
PLUGIN_SERVICE = ROOT / "vein_launcher" / "application" / "services" / "plugin_service.py"
FRONTEND_SRC = ROOT / "vein_launcher" / "presentation" / "webui" / "src"

_NAV_RE = re.compile(r"key:\s*'([a-z]+)'")
_VERSION_RE = re.compile(r"^VERSION\s*=\s*['\"]([^'\"]+)['\"]", re.MULTILINE)
_REGISTER_RE = re.compile(r'reg\.register\(\s*"([^"]+)"\s*,\s*"([^"]+)"\s*,')
_RAN_RE = re.compile(r"Ran\s+(\d+)\s+tests?")

# collect() 会被文档生成器多次调用；测试要跑 1s 多，缓存一次即可
_CACHE: "Facts | None" = None


@dataclass
class Facts:
    """一份代码事实快照；errors 非空表示锚点解析失败（不是文档内容错误）"""

    rpc_methods: list[str] = field(default_factory=list)
    rpc_groups: dict[str, int] = field(default_factory=dict)
    nav_items: list[str] = field(default_factory=list)
    test_count: int = 0
    version: str = ""
    plugin_capabilities: list[tuple[str, str]] = field(default_factory=list)
    frontend_loc: int = 0
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _read(path: Path) -> str:
    if not path.is_file():
        raise FileNotFoundError(f"缺少源文件：{path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


# ----------------------------------------------------------------------
# 提取器：每个只负责填 Facts 的一个字段
# ----------------------------------------------------------------------
def _extract_rpc(facts: Facts) -> None:
    """bridge.py 里 self._handlers 字典字面量的常量键（AnnAssign / Assign 都认）"""
    tree = ast.parse(_read(BRIDGE), filename=str(BRIDGE))
    methods: list[str] = []
    found = False
    for node in ast.walk(tree):
        targets = []
        if isinstance(node, ast.Assign):
            targets, value = node.targets, node.value
        elif isinstance(node, ast.AnnAssign):
            targets, value = [node.target], node.value
        else:
            continue
        if not isinstance(value, ast.Dict):
            continue
        if not any(isinstance(t, ast.Attribute) and t.attr == "_handlers" for t in targets):
            continue
        found = True
        for key in value.keys:
            if isinstance(key, ast.Constant) and isinstance(key.value, str):
                methods.append(key.value)
            else:
                facts.warnings.append("bridge._handlers 含非字面量键，已跳过")
    if not found:
        raise ValueError("未找到 self._handlers 字典字面量（锚点失效）")

    unique = list(dict.fromkeys(methods))  # 源码里重复键运行时只保留最后一个
    if len(unique) != len(methods):
        facts.warnings.append(f"bridge._handlers 含 {len(methods) - len(unique)} 个重复键")
    facts.rpc_methods = unique
    groups: dict[str, int] = {}
    for name in unique:
        group = name.split(".", 1)[0]
        groups[group] = groups.get(group, 0) + 1
    facts.rpc_groups = dict(sorted(groups.items()))


def _extract_nav(facts: Facts) -> None:
    """App.tsx 里 const NAV = [...] 的 key"""
    text = _read(APP_TSX)
    block = re.search(r"const\s+NAV\b[^=]*=\s*\[(.*?)\n\s*\];", text, re.S)
    if block is None:
        raise ValueError("未找到 const NAV = [...] 块（锚点失效）")
    items = _NAV_RE.findall(block.group(1))
    if not items:
        raise ValueError("NAV 块里没有匹配 key: 'xxx' 的项")
    facts.nav_items = items


def _extract_version(facts: Facts) -> None:
    match = _VERSION_RE.search(_read(CONTEXT))
    if match is None:
        raise ValueError("context.py 里没有 VERSION = \"...\"（锚点失效）")
    facts.version = match.group(1)


def _extract_plugin_capabilities(facts: Facts) -> None:
    """plugin_service.py 里 reg.register("能力", "权限", handler) 的 (能力, 权限)"""
    pairs = [(name, perm) for name, perm in _REGISTER_RE.findall(_read(PLUGIN_SERVICE))]
    if not pairs:
        raise ValueError("plugin_service.py 里没有 reg.register(...)（锚点失效）")
    facts.plugin_capabilities = pairs


def _extract_frontend_loc(facts: Facts) -> None:
    files = [p for p in FRONTEND_SRC.rglob("*") if p.suffix in (".ts", ".tsx") and p.is_file()]
    if not files:
        raise ValueError(f"{FRONTEND_SRC.relative_to(ROOT)} 下没有 .ts/.tsx")
    total = 0
    for path in files:
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            total += sum(1 for _ in handle)
    facts.frontend_loc = total


def _extract_test_count(facts: Facts) -> None:
    proc = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=300,
    )
    match = _RAN_RE.search(proc.stderr or "")
    if match is None:
        raise ValueError(f"unittest 输出里没有 'Ran N tests'（exit={proc.returncode}）")
    facts.test_count = int(match.group(1))
    if proc.returncode != 0:
        facts.warnings.append(
            f"unittest 未通过（exit={proc.returncode}），数量按输出记录：{facts.test_count}"
        )


_EXTRACTORS = (
    ("rpc_methods", _extract_rpc),
    ("nav_items", _extract_nav),
    ("version", _extract_version),
    ("plugin_capabilities", _extract_plugin_capabilities),
    ("frontend_loc", _extract_frontend_loc),
    ("test_count", _extract_test_count),
)


# ----------------------------------------------------------------------
# 对外接口
# ----------------------------------------------------------------------
def collect(*, use_cache: bool = True) -> Facts:
    """汇总一份事实快照；单个锚点失败只记 errors，不抛出"""
    global _CACHE
    if use_cache and _CACHE is not None:
        return _CACHE

    facts = Facts()
    for label, extractor in _EXTRACTORS:
        try:
            extractor(facts)
        except Exception as exc:  # noqa: BLE001 - 汇总给文档侧，别让生成器整体崩掉
            facts.errors.append(f"{label}: {type(exc).__name__}: {exc}")
    if use_cache:
        _CACHE = facts
    return facts


def check() -> tuple[list[str], list[str]]:
    """ERROR/WARN 规则占位：返回 (errors, warnings)，规则由文档侧后续提供"""
    return ([], [])


def main() -> int:
    facts = collect()
    payload = asdict(facts)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    if facts.errors:
        print("锚点解析失败：" + "；".join(facts.errors), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
