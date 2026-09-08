# 订单金额计算模块 — 软件测试实践

本项目是《软件测试与质量保证实践》课程作业的被测对象与自动化测试工程。

## 项目结构

```
d:\workspace\
├── order_calc/            # 被测模块（订单金额计算核心业务逻辑）
│   ├── __init__.py
│   └── calculator.py      # Item / Order / 各计算函数
├── tests/                 # 自动化测试脚本（pytest）
│   ├── __init__.py
│   └── test_calculator.py
├── requirements.txt       # 依赖清单
├── README.md              # 本文件
└── .gitignore
```

## 环境配置

1. 创建并激活虚拟环境（PowerShell）：
   ```powershell
   python -m venv .venv
   .venv\Scripts\activate
   ```
2. 安装依赖：
   ```powershell
   pip install -r requirements.txt
   ```

## 测试运行方式

在项目根目录一键运行全部用例：

```powershell
pytest
```

或使用虚拟环境解释器：

```powershell
.venv\Scripts\python.exe -m pytest
```

查看详细输出与覆盖率（可选）：

```powershell
pytest -v
```

## 被测对象说明

`order_calc.calculator` 模块实现电商订单金额计算，核心业务规则：

1. 商品单价 `price >= 0`，数量 `quantity >= 1` 的整数；
2. 小计 = Σ(单价 × 数量)；
3. 满减：满 `threshold` 减 `reduction`，优惠不超过小计；
4. 会员折扣：折扣率 `rate ∈ [0, 1]`，折扣金额 = 金额 × (1 - rate)；
5. 优惠叠加顺序：先满减，再对剩余金额折扣；
6. 运费：小计达 `free_threshold` 免运费，否则收 `base_fee`；
7. 应付总额 = 小计 - 满减 - 折扣 + 运费，最低为 0。

## 版本管理

- 每位小组成员使用个人账号独立提交；
- 提交信息清晰描述变更，例如 `feat: 添加满减边界测试`；
- 本仓库托管于 GitHub。
