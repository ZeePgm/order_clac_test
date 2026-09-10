import os
import sys

import pytest

# 把项目根目录加入 sys.path，保证在任意目录下运行都能 import order_calc
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from order_calc import (
    Item,
    Order,
    calc_full_reduction,
    calc_member_discount,
    calc_shipping,
    calc_subtotal,
)


# ===========================================================================
# 一、等价类划分（ORD-UT-001 ~ 004、007、009、010）
# ===========================================================================
class TestSubtotalEquivalence:
    """小计计算的等价类划分用例。"""

    def test_ord_ut_001_empty_items_subtotal_is_zero(self):
        """ORD-UT-001 空订单小计为 0（有效等价类）。"""
        assert calc_subtotal([]) == 0.0

    def test_ord_ut_002_single_item(self):
        """ORD-UT-002 单个商品小计 = 单价 × 数量。"""
        assert calc_subtotal([Item("钢笔", 3.5, 2)]) == 7.0

    def test_ord_ut_003_multiple_items(self):
        """ORD-UT-003 多个商品小计累加。"""
        items = [Item("钢笔", 3.5, 2), Item("笔记本", 10.0, 1)]
        assert calc_subtotal(items) == 17.0

    def test_ord_ut_004_zero_price_item(self):
        """ORD-UT-004 单价为 0 的赠品小计为 0（边界下点 price = 0）。"""
        assert calc_subtotal([Item("赠品", 0.0, 3)]) == 0.0

    def test_ord_ut_007_non_integer_quantity_raises(self):
        """ORD-UT-007 数量为小数应抛 ValueError（无效等价类）。"""
        with pytest.raises(ValueError):
            Item("钢笔", 3.0, 1.5)

    def test_ord_ut_009_large_quantity(self):
        """ORD-UT-009 大数量累加结果正确。"""
        assert calc_subtotal([Item("A", 0.01, 100000)]) == 1000.0

    def test_ord_ut_010_non_numeric_price_raises_value_error(self):
        """ORD-UT-010 单价为非数值时应抛 ValueError（与文档约定一致）。

        需求约定：单价非法时应给出明确的参数校验异常 ValueError。
        """
        with pytest.raises(ValueError):
            Item("钢笔", "abc", 1)

# ===========================================================================
# 二、边界值分析（ORD-UT-005、006、008、011 ~ 026）
# ===========================================================================
class TestSubtotalBoundary:
    """小计相关边界值用例。"""

    def test_ord_ut_005_negative_price_raises(self):
        """ORD-UT-005 单价 -0.01（下点外）应抛 ValueError。"""
        with pytest.raises(ValueError):
            Item("钢笔", -0.01, 1)

    def test_ord_ut_006_zero_quantity_raises(self):
        """ORD-UT-006 数量 0（下点外）应抛 ValueError。"""
        with pytest.raises(ValueError):
            Item("钢笔", 3.0, 0)

    def test_ord_ut_008_quantity_one(self):
        """ORD-UT-008 数量 1（下点）合法。"""
        assert calc_subtotal([Item("钢笔", 9.9, 1)]) == 9.9

    def test_ord_ut_031_bool_price_rejected(self):
        """ORD-UT-031 布尔值不应被当作合法单价（True 等价于 1.0 属于类型混用）。

        需求约定：单价必须为数值类型；布尔值虽然可隐式转成 0/1，
        但属于类型误用，应被参数校验拒绝。
        """
        with pytest.raises(ValueError):
            Item("钢笔", True, 1)

    def test_ord_ut_032_nan_price_rejected(self):
        """ORD-UT-032 非有限数值（NaN）单价应被拒绝，不能污染小计。

        需求约定：单价为合法金额（有限非负数）；NaN 参与累加会使整个
        订单小计变为 NaN，导致后续所有金额计算失效。
        """
        with pytest.raises(ValueError):
            Item("钢笔", float("nan"), 1)


class TestFullReductionBoundary:
    """满减的边界值用例。"""

    def test_ord_ut_011_below_threshold(self):
        """ORD-UT-011 小计 99.99（门槛下点外）不减免。"""
        assert calc_full_reduction(99.99, 100.0, 20.0) == 0.0

    def test_ord_ut_012_exact_threshold(self):
        """ORD-UT-012 小计 100.0（上点）减免 20。"""
        assert calc_full_reduction(100.0, 100.0, 20.0) == 20.0

    def test_ord_ut_013_above_threshold(self):
        """ORD-UT-013 小计 100.01（上点外）减免 20。"""
        assert calc_full_reduction(100.01, 100.0, 20.0) == 20.0

    def test_ord_ut_014_reduction_capped_by_subtotal(self):
        """ORD-UT-014 减免金额不超过小计本身。"""
        assert calc_full_reduction(10.0, 5.0, 50.0) == 10.0

    def test_ord_ut_015_zero_threshold(self):
        """ORD-UT-015 门槛 0、小计 0 时减免封顶为 0。"""
        assert calc_full_reduction(0.0, 0.0, 5.0) == 0.0

    def test_ord_ut_016_negative_threshold_raises(self):
        """ORD-UT-016 门槛为负数应抛 ValueError。"""
        with pytest.raises(ValueError):
            calc_full_reduction(100.0, -0.01, 20.0)

    def test_ord_ut_017_negative_reduction_raises(self):
        """ORD-UT-017 减免金额为负数应抛 ValueError。"""
        with pytest.raises(ValueError):
            calc_full_reduction(100.0, 50.0, -1.0)


class TestMemberDiscountBoundary:
    """会员折扣的边界值用例。"""

    def test_ord_ut_018_rate_one_no_discount(self):
        """ORD-UT-018 折扣率 1（上点）折扣额为 0。"""
        assert calc_member_discount(100.0, 1.0) == 0.0

    def test_ord_ut_019_rate_zero_full_discount(self):
        """ORD-UT-019 折扣率 0（下点）折扣额等于原金额。"""
        assert calc_member_discount(100.0, 0.0) == 100.0

    def test_ord_ut_020_normal_rate(self):
        """ORD-UT-020 常规 9 折折扣额为 10。"""
        assert calc_member_discount(100.0, 0.9) == 10.0

    def test_ord_ut_021_rate_above_one_raises(self):
        """ORD-UT-021 折扣率 1.01（上点外）应抛 ValueError。"""
        with pytest.raises(ValueError):
            calc_member_discount(100.0, 1.01)

    def test_ord_ut_022_negative_rate_raises(self):
        """ORD-UT-022 折扣率 -0.01（下点外）应抛 ValueError。"""
        with pytest.raises(ValueError):
            calc_member_discount(100.0, -0.01)

    def test_ord_ut_023_negative_amount_raises(self):
        """ORD-UT-023 参与折扣金额为负数应抛 ValueError。"""
        with pytest.raises(ValueError):
            calc_member_discount(-1.0, 0.9)


class TestShippingBoundary:
    """运费的边界值用例。"""

    def test_ord_ut_024_free_at_threshold(self):
        """ORD-UT-024 小计 200.0（上点）免运费。"""
        assert calc_shipping(200.0, 200.0, 10.0) == 0.0

    def test_ord_ut_025_below_threshold_charged(self):
        """ORD-UT-025 小计 199.99（下点外）收运费 10。"""
        assert calc_shipping(199.99, 200.0, 10.0) == 10.0

    def test_ord_ut_026_negative_base_fee_raises(self):
        """ORD-UT-026 基础运费为负数应抛 ValueError。"""
        with pytest.raises(ValueError):
            calc_shipping(100.0, 200.0, -0.01)


# ===========================================================================
# 三、场景法（ORD-UT-027 ~ 030）
# ===========================================================================
class TestOrderScenario:
    """订单全流程场景法用例。"""

    def test_ord_ut_027_full_checkout_flow(self):
        """ORD-UT-027 加购→满减→折扣→运费→结算全流程。"""
        order = Order()
        order.add_item("钢笔", 50.0, 2)   # 小计 100
        order.add_item("橡皮", 2.5, 4)    # 小计 10，合计 110
        order.set_full_reduction(100.0, 20.0)
        order.set_member_rate(0.9)
        order.set_shipping(150.0, 8.0)

        result = order.checkout()

        assert result["subtotal"] == 110.0
        assert result["reduction"] == 20.0
        assert result["discount"] == 9.0
        assert result["shipping"] == 8.0
        assert result["total"] == 89.0

    def test_ord_ut_028_empty_order_checkout(self):
        """ORD-UT-028 空订单结算各项均为 0。"""
        result = Order().checkout()
        assert result == {
            "subtotal": 0.0,
            "reduction": 0.0,
            "discount": 0.0,
            "shipping": 0.0,
            "total": 0.0,
        }

    def test_ord_ut_029_reduction_before_discount(self):
        """ORD-UT-029 优惠叠加顺序：先满减，再对剩余金额打折。"""
        order = Order()
        order.add_item("A", 100.0, 1)
        order.set_full_reduction(100.0, 30.0)
        order.set_member_rate(0.8)

        result = order.checkout()

        # 折扣基数 = 100 - 30 = 70，折扣额 = 70 × 0.2 = 14
        assert result["discount"] == 14.0
        assert result["total"] == 56.0

    def test_ord_ut_030_remove_duplicate_named_item(self):
        """ORD-UT-030 移除同名商品只减少一件。

        场景：购物车中有两个同名商品（不同单价），移除后应只减少一件，
        剩余商品应恰好为 [橡皮, 钢笔]。
        """
        order = Order()
        order.add_item("钢笔", 10.0, 1)
        order.add_item("橡皮", 5.0, 1)
        order.add_item("钢笔", 20.0, 1)

        order.remove_item("钢笔")

        names = [item.name for item in order._items]
        assert len(order._items) == 2, f"移除同名商品后剩余件数错误：{names}"
        assert names == ["橡皮", "钢笔"], f"移除同名商品后剩余商品错误：{names}"

    def test_ord_ut_033_invalid_member_rate_rejected_on_set(self):
        """ORD-UT-033 非法折扣率应在设置时即被拒绝。

        场景：调用 set_member_rate(1.5) 应立刻抛出 ValueError，
        而不是等到 checkout() 时才在计算折扣的过程中暴露异常。
        """
        order = Order()
        order.add_item("A", 100.0, 1)

        with pytest.raises(ValueError):
            order.set_member_rate(1.5)

    def test_ord_ut_034_negative_reduction_rejected_on_set(self):
        """ORD-UT-034 负满减金额应在设置时即被拒绝。"""
        order = Order()
        order.add_item("A", 100.0, 1)

        with pytest.raises(ValueError):
            order.set_full_reduction(50.0, -10.0)

    def test_ord_ut_035_negative_shipping_fee_rejected_on_set(self):
        """ORD-UT-035 负运费应在设置时即被拒绝。"""
        order = Order()
        order.add_item("A", 100.0, 1)

        with pytest.raises(ValueError):
            order.set_shipping(200.0, -5.0)
