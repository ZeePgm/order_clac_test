"""订单金额计算模块的 pytest 测试脚本。

说明：
- 本文件仅包含少量「示例用例」，用于验证测试工程可一键运行、展示用例风格。
- ⚠️ 模块一要求：最终 ≥30 条测试用例须由小组成员人工设计（等价类/边界值/场景法
  中至少 2 种方法），请勿用 AI 直接生成正式交付用例。
- 运行方式：在项目根目录执行  `pytest`  或  `.venv\\Scripts\\python.exe -m pytest`。
"""

import pytest

from order_calc import (
    Item,
    Order,
    calc_full_reduction,
    calc_member_discount,
    calc_shipping,
    calc_subtotal,
    calc_total,
)


# ---------------------------------------------------------------------------
# 等价类示例：小计计算
# ---------------------------------------------------------------------------
class TestCalcSubtotal:
    def test_empty_items_subtotal_is_zero(self):
        """空订单小计为 0（有效等价类）。"""
        assert calc_subtotal([]) == 0.0

    def test_single_item(self):
        """单个商品：单价 × 数量。"""
        assert calc_subtotal([Item("钢笔", 3.5, 2)]) == 7.0

    def test_multiple_items(self):
        """多个商品累加。"""
        items = [Item("钢笔", 3.5, 2), Item("笔记本", 10.0, 1)]
        assert calc_subtotal(items) == 17.0

    def test_invalid_negative_price_raises(self):
        """单价为负数应抛出异常（无效等价类）。"""
        with pytest.raises(ValueError):
            Item("钢笔", -1.0, 1)

    def test_invalid_zero_quantity_raises(self):
        """数量为 0 应抛出异常（无效等价类）。"""
        with pytest.raises(ValueError):
            Item("钢笔", 3.0, 0)


# ---------------------------------------------------------------------------
# 边界值示例：满减
# ---------------------------------------------------------------------------
class TestCalcFullReduction:
    def test_below_threshold_no_reduction(self):
        """小计小于门槛（threshold - 1）不减免。"""
        assert calc_full_reduction(99.0, 100.0, 20.0) == 0.0

    def test_exact_threshold_reduction(self):
        """小计恰好等于门槛（上点）减免。"""
        assert calc_full_reduction(100.0, 100.0, 20.0) == 20.0

    def test_above_threshold_reduction(self):
        """小计大于门槛减免。"""
        assert calc_full_reduction(100.01, 100.0, 20.0) == 20.0

    def test_reduction_capped_by_subtotal(self):
        """减免金额不超过小计本身。"""
        assert calc_full_reduction(10.0, 5.0, 50.0) == 10.0

    def test_negative_threshold_raises(self):
        """门槛为负数抛出异常。"""
        with pytest.raises(ValueError):
            calc_full_reduction(100.0, -1.0, 20.0)


# ---------------------------------------------------------------------------
# 边界值示例：会员折扣
# ---------------------------------------------------------------------------
class TestCalcMemberDiscount:
    def test_full_rate_no_discount(self):
        """折扣率 1（不打折）折扣金额为 0。"""
        assert calc_member_discount(100.0, 1.0) == 0.0

    def test_zero_rate_full_discount(self):
        """折扣率 0（全额减免）折扣金额等于原金额。"""
        assert calc_member_discount(100.0, 0.0) == 100.0

    def test_normal_rate(self):
        """常规 9 折。"""
        assert calc_member_discount(100.0, 0.9) == 10.0

    def test_rate_out_of_range_raises(self):
        """折扣率超出 [0,1] 抛出异常。"""
        with pytest.raises(ValueError):
            calc_member_discount(100.0, 1.1)
        with pytest.raises(ValueError):
            calc_member_discount(100.0, -0.1)


# ---------------------------------------------------------------------------
# 边界值示例：运费
# ---------------------------------------------------------------------------
class TestCalcShipping:
    def test_free_shipping_at_threshold(self):
        """小计恰达免运费门槛免运费。"""
        assert calc_shipping(200.0, 200.0, 10.0) == 0.0

    def test_below_threshold_charged(self):
        """小计低于门槛收取运费。"""
        assert calc_shipping(199.99, 200.0, 10.0) == 10.0

    def test_negative_fee_raises(self):
        """运费为负数抛出异常。"""
        with pytest.raises(ValueError):
            calc_shipping(100.0, 200.0, -1.0)


# ---------------------------------------------------------------------------
# 场景法示例：订单全流程结算
# ---------------------------------------------------------------------------
class TestOrderCheckout:
    def test_full_flow_with_discount_and_shipping(self):
        """场景：加购 → 满减 → 会员折扣 → 结算。"""
        order = Order()
        order.add_item("钢笔", 50.0, 2)  # 小计 100
        order.add_item("橡皮", 2.5, 4)   # 小计 10，合计 110
        order.set_full_reduction(100.0, 20.0)   # 满 100 减 20
        order.set_member_rate(0.9)              # 9 折
        order.set_shipping(150.0, 8.0)          # 满 150 免运费，否则 8 元
        result = order.checkout()
        assert result["subtotal"] == 110.0
        assert result["reduction"] == 20.0
        # 先满减再折扣：折扣金额 = (110 - 20) × 0.1 = 9.0
        assert result["discount"] == 9.0
        assert result["shipping"] == 8.0
        # 总额 = 110 - 20 - 9 + 8 = 89.0
        assert result["total"] == 89.0
