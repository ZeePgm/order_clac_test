# -*- coding: utf-8 -*-
"""模块二：AI 生成的自动化测试脚本（方案2「AI 测」）。




"""
import os
import sys

import pytest

# 把项目根目录加入 sys.path，保证在任意目录下运行都能 import order_calc
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from order_calc import (  # noqa: E402
    Item,
    Order,
    calc_full_reduction,
    calc_member_discount,
    calc_shipping,
    calc_subtotal,
    calc_total,
)


# ===========================================================================
# ORD-AI-001 / 002：精度与极端数值
# ===========================================================================
class TestPrecision:
    def test_ord_ai_001_huge_amount_is_finite(self):
        """ORD-AI-001 超大数量与超大单价组合的金额精度。"""
        item = Item("A", 9999999.99, 999999)
        assert item.amount == round(item.price * item.quantity, 2)
        assert item.amount == item.amount  # 非 NaN
        assert item.amount not in (float("inf"), float("-inf"))

    def test_ord_ai_002_float_accumulation_rounding(self):
        """ORD-AI-002 浮点累加的舍入一致性。"""
        items = [Item("A", 0.1, 3), Item("B", 0.2, 1)]
        assert calc_subtotal(items) == 0.5


# ===========================================================================
# ORD-AI-003 ~ 005：满减边界与浮点临界
# ===========================================================================
class TestFullReductionAI:
    def test_ord_ai_003_zero_reduction(self):
        """ORD-AI-003 减免额为 0 的退化场景。"""
        assert calc_full_reduction(200.0, 200.0, 0.0) == 0.0

    def test_ord_ai_004_float_threshold(self):
        """ORD-AI-004 门槛为浮点数时的临界判定。"""
        assert calc_full_reduction(99.999, 100.0, 5.0) == 0.0

    def test_ord_ai_005_reduction_equals_subtotal(self):
        """ORD-AI-005 减免额恰等于小计（封顶边界）。"""
        assert calc_full_reduction(30.0, 10.0, 30.0) == 30.0


# ===========================================================================
# ORD-AI-006 ~ 007：折扣精度与对称性
# ===========================================================================
class TestMemberDiscountAI:
    def test_ord_ai_006_non_integer_rate_rounding(self):
        """ORD-AI-006 折扣率 0.95 的分位舍入。"""
        assert calc_member_discount(99.99, 0.95) == 5.0

    def test_ord_ai_007_half_rate_symmetry(self):
        """ORD-AI-007 折扣率 0.5 的对称性。"""
        assert calc_member_discount(88.88, 0.5) == 44.44


# ===========================================================================
# ORD-AI-008 ~ 009：运费退化与组合
# ===========================================================================
class TestShippingAI:
    def test_ord_ai_008_zero_free_threshold(self):
        """ORD-AI-008 免运费门槛为 0 时恒免运费。"""
        assert calc_shipping(0.0, 0.0, 12.0) == 0.0

    def test_ord_ai_009_empty_order_with_shipping(self):
        """ORD-AI-009 小计为 0 且需收运费。"""
        assert calc_shipping(0.0, 100.0, 12.0) == 12.0


# ===========================================================================
# ORD-AI-010 ~ 011：总额兜底与单因素组合
# ===========================================================================
class TestTotalAI:
    def test_ord_ai_010_total_floor_zero(self):
        """ORD-AI-010 优惠总额超过小计后总额不低于 0。"""
        assert calc_total(10.0, 100.0, 50.0, 0.0) == 0.0

    def test_ord_ai_011_only_shipping(self):
        """ORD-AI-011 仅含运费的总额计算。"""
        assert calc_total(20.0, 0.0, 0.0, 8.0) == 28.0


# ===========================================================================
# ORD-AI-012 ~ 014：状态性与幂等性
# ===========================================================================
class TestOrderStateAI:
    def test_ord_ai_012_checkout_is_idempotent(self):
        """ORD-AI-012 重复结算结果一致（无副作用）。"""
        order = Order()
        order.add_item("A", 100.0, 1)
        order.set_full_reduction(50.0, 10.0)
        order.set_member_rate(0.9)
        order.set_shipping(150.0, 8.0)

        first = order.checkout()
        second = order.checkout()

        assert first == second

    def test_ord_ai_013_rate_change_updates_result(self):
        """ORD-AI-013 修改折扣率后重新结算结果随之更新。"""
        order = Order()
        order.add_item("A", 100.0, 1)

        order.set_member_rate(0.9)
        first = order.checkout()["discount"]
        order.set_member_rate(0.8)
        second = order.checkout()["discount"]

        assert first == 10.0
        assert second == 20.0

    def test_ord_ai_014_remove_item_updates_subtotal(self):
        """ORD-AI-014 移除商品后小计同步更新。"""
        order = Order()
        order.add_item("钢笔", 100.0, 1)
        order.add_item("橡皮", 50.0, 1)
        assert order.subtotal == 150.0

        order.remove_item("橡皮")

        assert order.subtotal == 100.0


# ===========================================================================
# ORD-AI-015 ~ 018：组合场景
# ===========================================================================
class TestOrderCombinationAI:
    def test_ord_ai_015_threshold_equals_subtotal(self):
        """ORD-AI-015 满减门槛恰等于小计时的结算。"""
        order = Order()
        order.add_item("A", 100.0, 1)
        order.set_full_reduction(100.0, 15.0)
        order.set_member_rate(1.0)

        result = order.checkout()

        assert result["reduction"] == 15.0
        assert result["discount"] == 0.0
        assert result["total"] == 85.0

    def test_ord_ai_016_discount_with_shipping(self):
        """ORD-AI-016 折扣与运费同时生效的总额。"""
        order = Order()
        order.add_item("A", 80.0, 1)
        order.set_member_rate(0.9)
        order.set_shipping(100.0, 6.0)

        result = order.checkout()

        assert result["discount"] == 8.0
        assert result["shipping"] == 6.0
        assert result["total"] == 78.0

    def test_ord_ai_017_no_discount_baseline(self):
        """ORD-AI-017 无任何优惠时总额等于小计加运费。"""
        order = Order()
        order.add_item("A", 30.0, 1)
        order.set_shipping(50.0, 5.0)

        result = order.checkout()

        assert result["reduction"] == 0.0
        assert result["discount"] == 0.0
        assert result["shipping"] == 5.0
        assert result["total"] == 35.0

    def test_ord_ai_018_excessive_discount_floor(self):
        """ORD-AI-018 优惠远大于小计时总额兜底为 0。"""
        order = Order()
        order.add_item("A", 10.0, 1)
        order.set_full_reduction(0.0, 100.0)
        order.set_member_rate(0.0)
        order.set_shipping(0.0, 5.0)

        result = order.checkout()

        assert result["total"] == 0.0


# ===========================================================================
# ORD-AI-019 ~ 020：跨接口一致性（AI 提出的性质校验）
# ===========================================================================
class TestConsistencyAI:
    def test_ord_ai_019_subtotal_consistency(self):
        """ORD-AI-019 calc_subtotal 与 Order.subtotal 结果一致。"""
        order = Order()
        order.add_item("钢笔", 3.5, 2)
        order.add_item("笔记本", 10.0, 1)

        assert order.subtotal == calc_subtotal(
            [Item("钢笔", 3.5, 2), Item("笔记本", 10.0, 1)]
        )

    def test_ord_ai_020_total_consistency(self):
        """ORD-AI-020 calc_total 与 Order.total 在等价配置下一致。"""
        order = Order()
        order.add_item("A", 120.0, 1)
        order.set_full_reduction(100.0, 20.0)
        order.set_member_rate(0.9)
        order.set_shipping(200.0, 8.0)

        result = order.checkout()
        manual = calc_total(
            result["subtotal"], result["reduction"], result["discount"], result["shipping"]
        )

        assert result["total"] == manual
        assert manual == 98.0


# ===========================================================================
# ORD-AI-021 ~ 024：AI 发现缺陷（在未修改的原系统上必然失败，作为缺陷证据）
# ===========================================================================
class TestDefectDiscovery:


    def test_ord_ai_021_invalid_member_rate_rejected(self):
        """ORD-AI-021 非法折扣率应在设置时被拒绝。"""
        order = Order()
        order.add_item("A", 100.0, 1)
        with pytest.raises(ValueError):
            order.set_member_rate(1.5)

    def test_ord_ai_022_negative_reduction_rejected(self):
        """ORD-AI-022 负满减金额应在设置时被拒绝。"""
        order = Order()
        order.add_item("A", 100.0, 1)
        with pytest.raises(ValueError):
            order.set_full_reduction(50.0, -10.0)

    def test_ord_ai_023_nan_price_rejected(self):
        """ORD-AI-023 NaN 单价应被拒绝，不能污染小计。"""
        with pytest.raises(ValueError):
            Item("钢笔", float("nan"), 1)

    def test_ord_ai_024_bool_price_rejected(self):
        """ORD-AI-024 布尔值不应作为合法单价。"""
        with pytest.raises(ValueError):
            Item("钢笔", True, 1)
