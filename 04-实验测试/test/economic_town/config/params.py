"""全局仿真参数配置"""

# ── 规模 ─────────────────────────────────────────────
NUM_FACTORIES = 3
NUM_WORKERS = 30
NUM_RETAILERS = 1

# ── 银行初始参数 ──────────────────────────────────────
BANK_INITIAL_CAPITAL = 30000.0  # 自有资本（需能支撑3家工厂大额贷款）
BANK_DEPOSIT_RATE = 0.02        # 月存款利率
BANK_LOAN_RATE = 0.05           # 月贷款利率
BANK_RESERVE_RATIO = 0.20       # 最低准备金率（存款的20%必须留存）
BANK_MAX_LOAN_PER_FACTORY = 5000.0  # 单厂最大贷款额

# ── 工厂初始参数 ──────────────────────────────────────
# 三个工厂的差异化配置 [厂A, 厂B, 厂C]
FACTORY_CONFIGS = [
    {"name": "厂A", "tech_factor": 1.2, "capital_alpha": 0.4, "labor_beta": 0.4, "initial_capital": 2000.0},
    {"name": "厂B", "tech_factor": 1.0, "capital_alpha": 0.5, "labor_beta": 0.3, "initial_capital": 2500.0},
    {"name": "厂C", "tech_factor": 0.8, "capital_alpha": 0.3, "labor_beta": 0.5, "initial_capital": 3000.0},
]
FACTORY_BASE_PRICE = 10.0       # 商品基准出售价格

# ── 外部市场参数 ──────────────────────────────────────
EXTERNAL_BASE_DEMAND = 500.0    # 各工厂基准需求量（差异化，各自独立）
EXTERNAL_PRICE_ELASTICITY = 1.5 # 价格弹性 ε
EXTERNAL_DEMAND_VOLATILITY = 0.1 # 需求随机冲击标准差（月度）

# ── 工人初始参数范围 ──────────────────────────────────
WORKER_SKILL_RANGE = (0.5, 1.5)
WORKER_SAVINGS_RATE_RANGE = (0.1, 0.4)
WORKER_RESERVATION_WAGE_RANGE = (50.0, 120.0)  # 最低可接受工资（合理范围）
WORKER_LOCAL_SPEND_RATIO_RANGE = (0.4, 0.8)    # 本地消费比例
WORKER_INITIAL_SAVINGS = 200.0  # 初始存款

# ── 零售商参数 ────────────────────────────────────────
RETAILER_MARKUP_RATE = 0.10     # 零售商加价率（利润）

# ── 仿真控制 ──────────────────────────────────────────
RANDOM_SEED = 42
SIMULATION_MONTHS = 60          # 默认跑60个月（5年）

# ── LLM 分析触发阈值 ──────────────────────────────────
LLM_TRIGGER_UNEMPLOYMENT_RATE = 0.30   # 失业率超过30%触发分析
LLM_TRIGGER_BAD_DEBT_RATE = 0.20      # 坏账率超过20%触发分析
LLM_ANNUAL_REPORT_INTERVAL = 12        # 每12个月做一次年度报告
OLLAMA_MODEL = "qwen2.5:0.5b"
OLLAMA_BASE_URL = "http://localhost:11434"

# ── 终止条件 ──────────────────────────────────────────
TERMINATION_BANK_CAPITAL_MIN = -5000.0          # 银行资本金低于此值视为破产
TERMINATION_CHRONIC_UNEMPLOYMENT_RATE = 0.60    # 慢性高失业率阈值
TERMINATION_CHRONIC_UNEMPLOYMENT_MONTHS = 6     # 连续 N 个月高失业率触发终止
TERMINATION_MAX_MONTHS = 240                    # 最长运行月数（20年）
