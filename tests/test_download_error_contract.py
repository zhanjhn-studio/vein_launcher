"""下载异常构造签名的静态契约（纯 AST，不联网、不导入 aiohttp）

背景：``downloader.py`` 曾写 ``raise DownloadError(..., status=response.status)``，
而 ``DownloadError.__init__`` 只有 ``message / url / retry_count``——异常路径一跑就
TypeError，把「下载失败」变成「下载功能崩掉」。修正方案是新增子类
``HTTPStatusDownloadError`` 承载 ``status``。

本测试用 AST 静态检查（不触发导入、无副作用）：

1. 解析 ``common/exceptions.py``，得到 ``DownloadError`` 家族（含 ``SHA1MismatchError``
   与任何传递子类）的 ``__init__`` 签名；
2. 扫描 ``infrastructure/download/*.py`` 中对家族类的每次构造调用，关键字参数必须是
   该构造器签名允许的子集，位置参数不得超过可容纳数量，不允许 ``*``/``**`` 展开；
3. 额外检查家族子类里的 ``super().__init__(...)`` 是否匹配父类签名。

签名从源码推导而非写死，例外只有一条：``status`` 不允许回到 ``DownloadError``
本身——它属于 ``HTTPStatusDownloadError``，这是本 Bug 的回归锚点。
"""

from __future__ import annotations

import ast
import unittest
from pathlib import Path
from typing import Dict, List, NamedTuple, Optional, Set, Tuple

ROOT = Path(__file__).resolve().parents[1]
EXCEPTIONS = ROOT / "vein_launcher" / "common" / "exceptions.py"
DOWNLOAD_DIR = ROOT / "vein_launcher" / "infrastructure" / "download"

EXCEPTIONS_MODULE = "vein_launcher.common.exceptions"
FAMILY_ROOT = "DownloadError"


class Signature(NamedTuple):
    """一个 ``__init__`` 的静态签名摘要（不含 self）"""

    names: Set[str]
    positional_capacity: int
    has_vararg: bool
    has_kwarg: bool


def _parse(path: Path) -> ast.Module:
    if not path.is_file():
        raise AssertionError(f"契约测试依赖的源文件不存在：{path}")
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _signature(node: ast.FunctionDef | ast.AsyncFunctionDef) -> Signature:
    args = node.args
    positional = [a.arg for a in args.posonlyargs] + [a.arg for a in args.args]
    if positional and positional[0] in ("self", "cls"):
        positional = positional[1:]
    return Signature(
        names=set(positional) | {a.arg for a in args.kwonlyargs},
        positional_capacity=len(positional),
        has_vararg=args.vararg is not None,
        has_kwarg=args.kwarg is not None,
    )


def _init_signature(cls: ast.ClassDef) -> Optional[Signature]:
    for item in cls.body:
        if isinstance(item, ast.FunctionDef) and item.name == "__init__":
            return _signature(item)
    return None


def _base_name(cls: ast.ClassDef) -> Optional[str]:
    """基类名；``DownloadError`` / ``exceptions.DownloadError`` 都归一成末段名"""
    if not cls.bases:
        return None
    base = cls.bases[0]
    if isinstance(base, ast.Name):
        return base.id
    if isinstance(base, ast.Attribute):
        return base.attr
    return None


def _defined_classes(tree: ast.Module) -> Dict[str, ast.ClassDef]:
    return {n.name: n for n in tree.body if isinstance(n, ast.ClassDef)}


def exception_family() -> Dict[str, Signature]:
    """``exceptions.py`` 中 DownloadError 及其（传递）子类的 ``__init__`` 签名"""
    classes = _defined_classes(_parse(EXCEPTIONS))
    if FAMILY_ROOT not in classes:
        raise AssertionError(f"{EXCEPTIONS} 中找不到 {FAMILY_ROOT}（被重命名了？）")

    family = {FAMILY_ROOT}
    changed = True
    while changed:
        changed = False
        for name, cls in classes.items():
            base = _base_name(cls)
            if name not in family and base in family:
                family.add(name)
                changed = True

    signatures: Dict[str, Signature] = {}
    for name in sorted(family):
        sig = _init_signature(classes[name])
        if sig is None:
            raise AssertionError(f"{name} 未显式定义 __init__，无法静态校验构造签名")
        signatures[name] = sig
    return signatures


def _local_visible(path: Path, family: Dict[str, Signature]) -> Dict[str, Tuple[str, Signature]]:
    """模块内可见的家族类：别名 -> (规范名, 签名)。含本模块定义的子类。"""
    tree = _parse(path)
    visible: Dict[str, Tuple[str, Signature]] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.ImportFrom) or node.module != EXCEPTIONS_MODULE:
            continue
        for alias in node.names:
            if alias.name in family:
                visible[alias.asname or alias.name] = (alias.name, family[alias.name])

    for cls in (n for n in tree.body if isinstance(n, ast.ClassDef)):
        base = _base_name(cls)
        if base is None or base not in visible:
            continue
        canonical, _parent_sig = visible[base]
        sig = _init_signature(cls) or visible[base][1]
        visible[cls.name] = (f"{canonical}->{cls.name}", sig)
    return visible


def _call_sites(path: Path, visible: Dict[str, Tuple[str, Signature]]):
    """模块内对家族类的构造调用：[(规范名, 签名, Call)]"""
    sites = []
    for node in ast.walk(_parse(path)):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = func.id if isinstance(func, ast.Name) else (
            func.attr if isinstance(func, ast.Attribute) else None
        )
        if name in visible:
            canonical, sig = visible[name]
            sites.append((canonical, sig, node))
    return sites


def _violations(label: str, sig: Signature, call: ast.Call, where: str) -> List[str]:
    issues: List[str] = []
    if any(isinstance(arg, ast.Starred) for arg in call.args):
        issues.append("*args 展开无法静态校验")
    positional = len([arg for arg in call.args if not isinstance(arg, ast.Starred)])
    if positional > sig.positional_capacity and not sig.has_vararg:
        issues.append(
            f"传了 {positional} 个位置参数，{label}.__init__ 只接受 {sig.positional_capacity} 个"
        )

    passed: Set[str] = set()
    for keyword in call.keywords:
        if keyword.arg is None:
            issues.append("**kwargs 展开无法静态校验")
        else:
            passed.add(keyword.arg)
    unknown = sorted(passed - sig.names)
    if unknown and not sig.has_kwarg:
        issues.append(f"未知关键字 {unknown}；允许 {sorted(sig.names)}")

    return [f"{where}:{call.lineno} {label}(...) {issue}" for issue in issues]


def _super_init_calls(cls: ast.ClassDef):
    """``super().__init__(...)`` 调用点"""
    for node in ast.walk(cls):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not isinstance(func, ast.Attribute) or func.attr != "__init__":
            continue
        receiver = func.value
        if (
            isinstance(receiver, ast.Call)
            and isinstance(receiver.func, ast.Name)
            and receiver.func.id == "super"
        ):
            yield node


class DownloadErrorContractTests(unittest.TestCase):
    """download/ 下所有 DownloadError 家族构造必须匹配其签名"""

    def setUp(self) -> None:
        self.family = exception_family()

    def test_family_root_signature(self) -> None:
        sig = self.family[FAMILY_ROOT]
        self.assertTrue(
            {"message", "url", "retry_count"} <= sig.names,
            f"{FAMILY_ROOT}.__init__ 丢了既有参数：{sorted(sig.names)}",
        )
        self.assertNotIn(
            "status",
            sig.names,
            "status 不应由 DownloadError 承载：HTTP 状态码请用 HTTPStatusDownloadError",
        )

    def test_download_module_calls_match_signatures(self) -> None:
        problems: List[str] = []
        scanned = 0
        for path in sorted(DOWNLOAD_DIR.glob("*.py")):
            visible = _local_visible(path, self.family)
            if not visible:
                continue
            for label, sig, call in _call_sites(path, visible):
                scanned += 1
                problems.extend(_violations(label, sig, call, path.name))
        self.assertGreater(
            scanned,
            0,
            "download/ 下没有扫描到任何 DownloadError 家族调用，契约测试会静默空转",
        )
        self.assertEqual(problems, [], "\n".join(problems))

    def test_subclass_super_init_matches_parent(self) -> None:
        problems: List[str] = []
        checked = 0
        for path in sorted(DOWNLOAD_DIR.glob("*.py")):
            tree = _parse(path)
            visible = _local_visible(path, self.family)
            for cls in (n for n in tree.body if isinstance(n, ast.ClassDef)):
                base = _base_name(cls)
                if base is None or base not in visible:
                    continue
                parent_label, parent_sig = visible[base]
                for call in _super_init_calls(cls):
                    checked += 1
                    problems.extend(
                        _violations(
                            f"super().__init__ (父类 {parent_label})",
                            parent_sig,
                            call,
                            f"{path.name}:{cls.name}",
                        )
                    )
        self.assertGreater(checked, 0, "没有扫描到任何子类 super().__init__(...)，测试会空转")
        self.assertEqual(problems, [], "\n".join(problems))


if __name__ == "__main__":
    unittest.main()
