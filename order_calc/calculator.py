"""订单金额计算模块（被测对象）。

本模块是软件测试实践作业的「被测代码」，实现电商订单金额计算的核心业务逻辑，
包含商品小计、满减、会员折扣、运费等计算规则。

所有金额计算统一使用浮点数并 round 到 2 位小数（分）。

业务规则约定：
1. 商品单价 price >= 0，数量 quantity 为 >= 1 的整数；
2. 小计 = Σ(单价 × 数量)；
3. 满减：订单小计满 threshold 元减 reduction 元，优惠不超过小计本身；
4. 会员折扣：折扣率 rate 属于 [0, 1]，折扣金额 = 金额 × (1 - rate)；
5. 优惠叠加顺序：先满减，再对剩余金额应用会员折扣（可配置）；
6. 运费：小计（未优惠前）达到 free_threshold 元免运费，否则收取 base_fee 元；
7. 应付总额 = 小计 - 满减 - 折扣 + 运费，最低为 0。
"""

from __future__ import annotations

from typing import List, Optional


class Item:
    """订单中的单个商品项。

    Attributes:
        name: 商品名称。
        price: 商品单价，必须 >= 0。
        quantity: 购买数量，必须为 >= 1 的整数。
    """

    def __init__(self, name: str, price: float, quantity: int) -> None:
        if not isinstance(quantity, int) or isinstance(quantity, bool):
            raise ValueError("数量必须为整数")
        if quantity < 1:
            raise ValueError("数量必须大于等于 1")
        if price < 0:
            raise ValueError("单价不能为负数")
        self.name = name
        self.price = round(float(price), 2)
        self.quantity = quantity

    @property
    def amount(self) -> float:
        """该商品项的小计金额（单价 × 数量）。"""
        return round(self.price * self.quantity, 2)

    def __repr__(self) -> str:  # pragma: no cover
        return f"Item({self.name!r}, {self.price}, {self.quantity})"


def calc_subtotal(items: List[Item]) -> float:
    """计算订单小计：Σ(单价 × 数量)。

    Args:
        items: 商品项列表，可为空列表（空列表小计为 0）。

    Returns:
        小计金额，保留 2 位小数。
    """
    return round(sum(item.amount for item in items), 2)


def calc_full_reduction(subtotal: float, threshold: float, reduction: float) -> float:
    """计算满减优惠金额。

    规则：当 subtotal >= threshold 时减免 reduction，否则不减免；
    减免金额不超过 subtotal 本身。

    Args:
        subtotal: 订单小计。
        threshold: 满减门槛金额，必须 >= 0。
        reduction: 满减减免金额，必须 >= 0。

    Returns:
        实际减免金额。

    Raises:
        ValueError: threshold 或 reduction 为负数时抛出。
    """
    if threshold < 0:
        raise ValueError("满减门槛不能为负数")
    if reduction < 0:
        raise ValueError("满减金额不能为负数")
    if subtotal < threshold:
        return 0.0
    return round(min(reduction, subtotal), 2)


def calc_member_discount(amount: float, rate: float) -> float:
    """计算会员折扣金额。

    规则：折扣金额 = amount × (1 - rate)，rate 为折扣率（0.9 表示 9 折）。
    当 rate 为 1 时折扣金额为 0；rate 为 0 时折扣金额等于 amount。

    Args:
        amount: 参与折扣的金额，必须 >= 0。
        rate: 折扣率，必须在 [0, 1] 闭区间内。

    Returns:
        折扣金额。

    Raises:
        ValueError: rate 不在 [0, 1] 范围内时抛出。
    """
    if rate < 0 or rate > 1:
        raise ValueError("折扣率必须在 0 到 1 之间")
    if amount < 0:
        raise ValueError("金额不能为负数")
    return round(amount * (1 - rate), 2)


def calc_shipping(subtotal: float, free_threshold: float, base_fee: float) -> float:
    """计算运费。

    规则：subtotal >= free_threshold 时免运费（0 元），否则收取 base_fee 元。

    Args:
        subtotal: 订单小计。
        free_threshold: 免运费门槛金额，必须 >= 0。
        base_fee: 基础运费，必须 >= 0。

    Returns:
        运费金额。

    Raises:
        ValueError: free_threshold 或 base_fee 为负数时抛出。
    """
    if free_threshold < 0:
        raise ValueError("免运费门槛不能为负数")
    if base_fee < 0:
        raise ValueError("基础运费不能为负数")
    if subtotal >= free_threshold:
        return 0.0
    return round(base_fee, 2)


def calc_total(
    subtotal: float,
    reduction: float,
    discount: float,
    shipping: float,
) -> float:
    """计算应付总额。

    规则：总额 = 小计 - 满减 - 折扣 + 运费，最低为 0。

    Args:
        subtotal: 订单小计。
        reduction: 满减金额。
        discount: 会员折扣金额。
        shipping: 运费。

    Returns:
        应付总额，保留 2 位小数，不小于 0。
    """
    total = subtotal - reduction - discount + shipping
    return round(max(total, 0.0), 2)


class Order:
    """订单类，用于场景法测试（多步骤组合操作）。

    提供加购、移除商品、设置优惠与结算等操作。
    """

    def __init__(self) -> None:
        self._items: List[Item] = []
        self._full_reduction_threshold: float = 0.0
        self._full_reduction_amount: float = 0.0
        self._member_rate: Optional[float] = None
        self._free_shipping_threshold: float = 0.0
        self._base_fee: float = 0.0
        self._discount_after_reduction: bool = True

    def add_item(self, name: str, price: float, quantity: int) -> None:
        """添加商品项。"""
        self._items.append(Item(name, price, quantity))

    def remove_item(self, name: str) -> None:
        """按名称移除一件商品（若有多个同名项，仅移除第一个）。"""
        for item in self._items:
            if item.name == name:
                self._items.remove(item)
                return

    @property
    def subtotal(self) -> float:
        return calc_subtotal(self._items)

    def set_full_reduction(self, threshold: float, reduction: float) -> None:
        self._full_reduction_threshold = threshold
        self._full_reduction_amount = reduction

    def set_member_rate(self, rate: float) -> None:
        self._member_rate = rate

    def set_shipping(self, free_threshold: float, base_fee: float) -> None:
        self._free_shipping_threshold = free_threshold
        self._base_fee = base_fee

    @property
    def reduction(self) -> float:
        return calc_full_reduction(
            self.subtotal,
            self._full_reduction_threshold,
            self._full_reduction_amount,
        )

    @property
    def discount(self) -> float:
        if self._member_rate is None:
            return 0.0
        base = self.subtotal
        if self._discount_after_reduction:
            base = round(self.subtotal - self.reduction, 2)
        return calc_member_discount(base, self._member_rate)

    @property
    def shipping(self) -> float:
        return calc_shipping(
            self.subtotal,
            self._free_shipping_threshold,
            self._base_fee,
        )

    @property
    def total(self) -> float:
        return calc_total(self.subtotal, self.reduction, self.discount, self.shipping)

    def checkout(self) -> dict:
        """结算，返回金额明细。"""
        return {
            "subtotal": self.subtotal,
            "reduction": self.reduction,
            "discount": self.discount,
            "shipping": self.shipping,
            "total": self.total,
        }
