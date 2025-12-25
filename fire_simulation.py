import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import os

# ==========================================
# 1. 基础参数设定 (Configuration)
# ==========================================

# 个人信息
CURRENT_AGE = 25        # 更新为用户提供的 25 岁
LIFE_EXPECTANCY = 90    # 预期寿命 (保守估计，规划到90岁)
CURRENT_ASSETS = 200    # 当前储蓄 (万)
ANNUAL_INCOME = 56      # 税后年入 (万)
ANNUAL_EXPENSE = 12     # 当前年支出 (万)

# 经济假设
SIMULATIONS = 10000     # 模拟次数
INFLATION_MEAN = 0.035  # 通胀均值 (3.5%)
INFLATION_STD = 0.008   # 通胀标准差 (让大部分落在2%-5%区间)

# 投资回报 (均匀分布 -10% 到 +15%)
RETURN_MIN = -0.10
RETURN_MAX = 0.15

# 职业生涯风险假设
CAREER_CRISIS_AGE_START = 35
LAYOFF_PROBABILITY = 0.15      # 35岁后每年遭遇裁员/降薪的概率
SALARY_CUT_RATIO = 0.70        # 如果遭遇危机，薪资变为原来的70%
EARLY_GROWTH_RATE = 0.05       # 前5年的工资增长率

# ==========================================
# 2. 核心模拟逻辑 (Core Logic)
# ==========================================

def simulate_lifetime(retire_age):
    """
    模拟单次人生的资产轨迹
    返回: 是否破产 (Boolean), 资产路径 (Array)
    """
    ages = np.arange(CURRENT_AGE, LIFE_EXPECTANCY + 1)
    assets = np.zeros(len(ages))
    assets[0] = CURRENT_ASSETS
    
    current_salary = ANNUAL_INCOME
    current_expense = ANNUAL_EXPENSE
    
    is_ruined = False
    has_experienced_crisis = False # 标记是否已经经历过薪资跳水（避免每年都跳水）
    
    for t in range(1, len(ages)):
        age = ages[t]
        
        # --- A. 生成随机变量 ---
        # 1. 通胀 (正态分布)
        inflation = np.random.normal(INFLATION_MEAN, INFLATION_STD)
        inflation = np.clip(inflation, 0.0, 0.10) # 极端边界保护
        
        # 2. 投资回报 (均匀分布)
        investment_return = np.random.uniform(RETURN_MIN, RETURN_MAX)
        
        # --- B. 更新收支 ---
        # 更新支出 (随通胀增长)
        current_expense *= (1 + inflation)
        
        # 更新收入 (仅在退休前)
        if age <= retire_age:
            if age < CAREER_CRISIS_AGE_START:
                # 35岁前稳定增长
                current_salary *= (1 + EARLY_GROWTH_RATE)
            else:
                # 35岁后：职业危机判定
                if not has_experienced_crisis:
                    # 掷骰子决定是否遭遇危机
                    if np.random.random() < LAYOFF_PROBABILITY:
                        current_salary *= SALARY_CUT_RATIO
                        has_experienced_crisis = True # 假设经历一次大降薪后，就在那个水位稳定了
                    else:
                        current_salary *= (1 + 0.02) # 没裁员，但只有抗通胀的微涨
                else:
                    current_salary *= (1 + 0.02) # 已经降薪过了，后续按通胀微调
            
            yearly_cashflow = current_salary - current_expense
        else:
            # 退休后无工资收入，只有支出
            yearly_cashflow = -current_expense
            
        # --- C. 资产结算 ---
        # 逻辑：年初资产 * (1+收益率) + 本年净结余
        # 注意：这里假设结余是在年末产生，不享受当年投资收益；
        # 或者假设生活费是年初预留。为了保守起见，先算投资损益，再加减现金流。
        prev_assets = assets[t-1]
        new_assets = prev_assets * (1 + investment_return) + yearly_cashflow
        
        assets[t] = new_assets
        
        if new_assets < 0:
            is_ruined = True
            # 破产后资产归零，不再变负（模拟现实没钱了）
            assets[t:] = 0 
            break
            
    return is_ruined, assets

# ==========================================
# 3. 批量运行与分析 (Analysis)
# ==========================================

def analyze_assets_at_ages(target_ages=[40, 45, 50]):
    """
    固定在60岁退休(作为基准)，看中间过程的资产分布
    """
    print(f"\n--- 资产积累推演 (基于10000次模拟) ---")
    print(f"假设一直工作不退休，观察资产潜力：")
    
    # 我们运行一组很晚退休的模拟，纯粹为了看资产在40/45/50岁的分布
    results = []
    for _ in range(SIMULATIONS):
        _, path = simulate_lifetime(retire_age=60)
        results.append(path)
    
    results = np.array(results)
    
    for age in target_ages:
        idx = age - CURRENT_AGE
        assets_at_age = results[:, idx]
        p10 = np.percentile(assets_at_age, 10)
        p50 = np.percentile(assets_at_age, 50)
        p90 = np.percentile(assets_at_age, 90)
        print(f"【{age}岁时】")
        print(f"  悲观情况 (P10): {p10:.2f} 万")
        print(f"  中性情况 (P50): {p50:.2f} 万")
        print(f"  乐观情况 (P90): {p90:.2f} 万")

def find_optimal_fire_age():
    """
    寻找破产率 < 5% 的最早退休年龄
    """
    print(f"\n--- 寻找最佳 FIRE 年龄 (破产率 < 5%) ---")
    
    possible_retire_ages = range(35, 61) # 测试 35岁 到 60岁
    safe_age = None
    
    ruin_rates = []
    
    for r_age in possible_retire_ages:
        ruin_count = 0
        for _ in range(SIMULATIONS):
            is_ruined, _ = simulate_lifetime(retire_age=r_age)
            if is_ruined:
                ruin_count += 1
        
        rate = (ruin_count / SIMULATIONS) * 100
        ruin_rates.append(rate)
        
        print(f"退休年龄: {r_age}岁 -> 破产概率: {rate:.2f}%")
        
        if safe_age is None and rate < 5.0:
            safe_age = r_age
            
    return safe_age, possible_retire_ages, ruin_rates

# ==========================================
# 4. 主程序执行与绘图
# ==========================================

if __name__ == "__main__":
    # 1. 资产分布推演
    analyze_assets_at_ages()
    
    # 2. 寻找退休年龄
    safe_age, ages, rates = find_optimal_fire_age()
    
    if safe_age:
        print(f"\n>>> 结论: 建议在 【{safe_age}岁】 退休，此时资金耗尽概率低于5%。")
    else:
        print("\n>>> 结论: 在60岁前退休均无法满足<5%破产率的要求，建议降低预期或增加储蓄。")

    # 3. 绘图
    plt.figure(figsize=(12, 6))
    
    # 绘制破产率曲线
    plt.plot(ages, rates, marker='o', linestyle='-', color='#2c3e50', linewidth=2, label='Ruined Probability')
    
    # 标记安全线
    plt.axhline(y=5, color='#e74c3c', linestyle='--', label='5% Safety Threshold')
    
    # 标记推荐年龄
    if safe_age:
        try:
             # Find index safely
            idx = list(ages).index(safe_age)
            safe_rate = rates[idx]
            plt.scatter([safe_age], [safe_rate], color='#27ae60', s=150, zorder=5, label=f'Recommended Age: {safe_age}')
            plt.annotate(f'{safe_age} Years\n{safe_rate:.2f}% Risk', 
                        (safe_age, safe_rate), 
                        xytext=(10, 20), textcoords='offset points',
                        arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=.2'))
        except ValueError:
            pass

    plt.title(f'FIRE Monte Carlo Simulation (N={SIMULATIONS})', fontsize=14)
    plt.xlabel('Retirement Age', fontsize=12)
    plt.ylabel('Probability of Ruin (%)', fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.legend()
    
    # 保存结果
    plt.tight_layout()
    output_png = 'fire_simulation_result.png'
    plt.savefig(output_png)
    print(f"\n已生成分析图表: {output_png}")
    # plt.show() # Commented out to avoid blocking in headless env if needed, but saving is key.
