# -*- coding: utf-8 -*-
"""缺陷修复验证：临时补丁工具（apply / revert）。
用法：
    python 缺陷修复验证/patch_calculator.py apply     # 打临时补丁
    python -m pytest 模块一自动化测试脚本 -v           # 跑模块一用例 -> 应全部通过
    python 缺陷修复验证/patch_calculator.py revert    # 还原主干代码（必做）
"""
import os
import shutil
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TARGET = os.path.join(ROOT, "order_calc", "calculator.py")
BACKUP_DIR = os.path.join(os.path.dirname(__file__), "_backup")
BACKUP = os.path.join(BACKUP_DIR, "calculator.py.orig")

# ---- 修复内容DEF-001 ~ DEF-005 ----

OLD_ITEM = '''    def __init__(self, name: str, price: float, quantity: int) -> None:
        if not isinstance(quantity, int) or isinstance(quantity, bool):
            raise ValueError("数量必须为整数")
        if quantity < 1:
            raise ValueError("数量必须大于等于 1")
        if price < 0:
            raise ValueError("单价不能为负数")
        self.name = name
        self.price = round(float(price), 2)
        self.quantity = quantity'''

NEW_ITEM = '''    def __init__(self, name: str, price: float, quantity: int) -> None:
        if not isinstance(quantity, int) or isinstance(quantity, bool):
            raise ValueError("数量必须为整数")
        if quantity < 1:
            raise ValueError("数量必须大于等于 1")
        # DEF-001/DEF-002：单价必须为数值类型，且不能是布尔类型
        if isinstance(price, bool) or not isinstance(price, (int, float)):
            raise ValueError("单价必须为数值")
        price = float(price)
        # DEF-003：单价必须为有限数值（拒绝 NaN / Inf）
        if price != price or price in (float("inf"), float("-inf")):
            raise ValueError("单价必须为有限数值")
        if price < 0:
            raise ValueError("单价不能为负数")
        self.name = name
        self.price = round(price, 2)
        self.quantity = quantity'''

OLD_SETTERS = '''    def set_full_reduction(self, threshold: float, reduction: float) -> None:
        self._full_reduction_threshold = threshold
        self._full_reduction_amount = reduction

    def set_member_rate(self, rate: float) -> None:
        self._member_rate = rate

    def set_shipping(self, free_threshold: float, base_fee: float) -> None:
        self._free_shipping_threshold = free_threshold
        self._base_fee = base_fee'''

NEW_SETTERS = '''    def set_full_reduction(self, threshold: float, reduction: float) -> None:
        # DEF-005：设置时即校验，避免非法参数带到结算阶段才暴露
        if not isinstance(threshold, (int, float)) or isinstance(threshold, bool):
            raise ValueError("满减门槛必须为数值")
        if not isinstance(reduction, (int, float)) or isinstance(reduction, bool):
            raise ValueError("满减金额必须为数值")
        if threshold < 0:
            raise ValueError("满减门槛不能为负数")
        if reduction < 0:
            raise ValueError("满减金额不能为负数")
        self._full_reduction_threshold = float(threshold)
        self._full_reduction_amount = float(reduction)

    def set_member_rate(self, rate: float) -> None:
        # DEF-004：折扣率必须在 [0, 1] 内，设置时即拒绝
        if not isinstance(rate, (int, float)) or isinstance(rate, bool):
            raise ValueError("折扣率必须为数值")
        if rate < 0 or rate > 1:
            raise ValueError("折扣率必须在 0 到 1 之间")
        self._member_rate = float(rate)

    def set_shipping(self, free_threshold: float, base_fee: float) -> None:
        # DEF-005：设置时即校验
        if not isinstance(free_threshold, (int, float)) or isinstance(free_threshold, bool):
            raise ValueError("免运费门槛必须为数值")
        if not isinstance(base_fee, (int, float)) or isinstance(base_fee, bool):
            raise ValueError("基础运费必须为数值")
        if free_threshold < 0:
            raise ValueError("免运费门槛不能为负数")
        if base_fee < 0:
            raise ValueError("基础运费不能为负数")
        self._free_shipping_threshold = float(free_threshold)
        self._base_fee = float(base_fee)'''


def build_patched(src: str) -> str:
    if OLD_ITEM not in src:
        raise SystemExit("错误：Item.__init__ 代码片段未匹配，主干代码可能已被改动。")
    if OLD_SETTERS not in src:
        raise SystemExit("错误：Order setter 代码片段未匹配，主干代码可能已被改动。")
    return src.replace(OLD_ITEM, NEW_ITEM, 1).replace(OLD_SETTERS, NEW_SETTERS, 1)


def do_apply() -> None:
    if os.path.exists(BACKUP):
        print("提示：备份已存在，说明补丁可能处于已应用状态。如需重新应用请先 revert。")
        return
    os.makedirs(BACKUP_DIR, exist_ok=True)
    shutil.copy2(TARGET, BACKUP)

    with open(TARGET, encoding="utf-8") as f:
        src = f.read()
    patched = build_patched(src)
    with open(TARGET, "w", encoding="utf-8") as f:
        f.write(patched)

    print(f"已备份原始代码 -> {BACKUP}")
    print(f"已应用临时补丁 -> {TARGET}")
    print("下一步：运行 pytest 验证，验证完成后执行 revert 还原。")


def do_revert() -> None:
    if not os.path.exists(BACKUP):
        print("提示：未找到备份，主干代码未被本工具修改过，无需还原。")
        return
    shutil.copy2(BACKUP, TARGET)
    os.remove(BACKUP)
    try:
        os.rmdir(BACKUP_DIR)
    except OSError:
        pass
    print(f"已从备份还原主干代码 -> {TARGET}")
    print("主干代码已恢复原始状态。")


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ("apply", "revert"):
        print(__doc__)
        raise SystemExit(1)
    if sys.argv[1] == "apply":
        do_apply()
    else:
        do_revert()
