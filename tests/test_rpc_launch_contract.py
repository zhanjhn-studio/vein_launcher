"""RPC 调用 ↔ 服务层签名的静态契约（纯 AST，不导入 Qt / 不联网）

背景：``presentation/bridge.py`` 曾给 ``LauncherService.launch`` 传了不存在的
``uuid=``，UI 点启动必然 TypeError。这类「调用签名漂移」单元测试抓不到
（单元测试直接调服务层，绕过了 bridge 的实参），所以这里用 AST 静态兜住：

1. 找出 ``bridge.py`` 里所有 ``...launcher.launch(...)`` 调用；
2. 取出 ``launcher_service.py`` 中 ``LauncherService.launch`` 的形参集合；
3. 关键字参数必须是形参的子集，位置参数不得超过形参可容纳的位置参数数量。

静态检查故意不 import ``bridge``/``launcher_service``：导入约等于拉起 PySide6、
pydantic 与网络模块，会让本测试变慢且产生副作用。
"""

from __future__ import annotations

import ast
import unittest
from pathlib import Path
from typing import Dict, List, NamedTuple, Set, Tuple

ROOT = Path(__file__).resolve().parents[1]
BRIDGE = ROOT / "vein_launcher" / "presentation" / "bridge.py"
LAUNCHER = ROOT / "vein_launcher" / "application" / "services" / "launcher_service.py"


class Signature(NamedTuple):
    """一个函数/方法的静态签名摘要"""

    names: Set[str]             # 全部可传的参数名（位置 + 仅关键字），不含 self/cls
    positional_capacity: int    # 可接受的位置参数个数
    has_vararg: bool            # 定义了 *args
    has_kwarg: bool             # 定义了 **kwargs


def _signature(node: ast.FunctionDef | ast.AsyncFunctionDef) -> Signature:
    args = node.args
    positional = [a.arg for a in args.posonlyargs] + [a.arg for a in args.args]
    if positional and positional[0] in ("self", "cls"):
        positional = positional[1:]
    keyword_only = [a.arg for a in args.kwonlyargs]
    return Signature(
        names=set(positional) | set(keyword_only),
        positional_capacity=len(positional),
        has_vararg=args.vararg is not None,
        has_kwarg=args.kwarg is not None,
    )


def _parse(path: Path) -> ast.Module:
    if not path.is_file():
        raise AssertionError(f"契约测试依赖的源文件不存在：{path}")
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _find_class_method(path: Path, class_name: str, method_name: str) -> ast.FunctionDef | ast.AsyncFunctionDef:
    for node in ast.walk(_parse(path)):
        if not isinstance(node, ast.ClassDef) or node.name != class_name:
            continue
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name == method_name:
                return item
    raise AssertionError(f"{path.name} 中找不到 {class_name}.{method_name}（方法被重命名或删除？）")


def _launcher_launch_calls(tree: ast.Module) -> List[ast.Call]:
    """收集 ``<...>.launcher.launch(...)``，如 ``self._ctx.launcher.launch(...)``"""
    calls: List[ast.Call] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not isinstance(func, ast.Attribute) or func.attr != "launch":
            continue
        owner = func.value
        if isinstance(owner, ast.Attribute) and owner.attr == "launcher":
            calls.append(node)
    return calls


def _describe(call: ast.Call) -> str:
    return f"{ast.unparse(call.func)}(...) @ line {call.lineno}"


class LaunchCallSiteTests(unittest.TestCase):
    """bridge 调用服务层 launch 的实参必须匹配 LauncherService.launch 签名"""

    def setUp(self) -> None:
        self.signature = _signature(_find_class_method(LAUNCHER, "LauncherService", "launch"))
        self.calls = _launcher_launch_calls(_parse(BRIDGE))

    def test_call_site_exists(self) -> None:
        """防止测试空转：重构改写调用点后必须回来更新契约测试"""
        self.assertTrue(
            self.calls,
            "bridge.py 里没找到 <...>.launcher.launch(...) 调用；"
            "调用方式变了就同步更新本契约测试，别让它静默失效",
        )

    def test_keyword_names_are_accepted(self) -> None:
        problems = []
        for call in self.calls:
            passed = {kw.arg for kw in call.keywords if kw.arg is not None}
            unknown = sorted(passed - self.signature.names)
            if unknown:
                problems.append(
                    f"{_describe(call)} 传入了 LauncherService.launch 不接受的参数 "
                    f"{unknown}；允许的参数：{sorted(self.signature.names)}"
                )
        self.assertEqual(problems, [], "\n".join(problems))

    def test_positional_args_within_capacity(self) -> None:
        problems = []
        for call in self.calls:
            positional = len([arg for arg in call.args if not isinstance(arg, ast.Starred)])
            if positional > self.signature.positional_capacity and not self.signature.has_vararg:
                problems.append(
                    f"{_describe(call)} 传了 {positional} 个位置参数，"
                    f"但 LauncherService.launch 只接受 {self.signature.positional_capacity} 个"
                )
        self.assertEqual(problems, [], "\n".join(problems))

    def test_no_star_unpacking_at_call_site(self) -> None:
        """``*args`` / ``**kwargs`` 展开无法静态校验，出现即要求改成显式实参"""
        problems = []
        for call in self.calls:
            starred = any(isinstance(arg, ast.Starred) for arg in call.args)
            unpacked = any(kw.arg is None for kw in call.keywords)
            if starred or unpacked:
                problems.append(
                    f"{_describe(call)} 使用了 *args/**kwargs 展开，静态契约无法校验；"
                    "请改为显式参数，或扩展本测试"
                )
        self.assertEqual(problems, [], "\n".join(problems))


if __name__ == "__main__":
    unittest.main()
