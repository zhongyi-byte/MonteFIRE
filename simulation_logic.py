import numpy as np
import pandas as pd

class FIRESimulator:
    def __init__(self, config):
        self.current_age = config.get('current_age', 25)
        self.life_expectancy = config.get('life_expectancy', 90)
        self.current_assets = config.get('current_assets', 100)
        self.annual_income = config.get('annual_income', 56)
        self.annual_expense = config.get('annual_expense', 12)
        
        self.simulations = config.get('simulations', 1000) # Default reduced for speed in web app
        self.inflation_mean = config.get('inflation_mean', 0.035)
        self.inflation_std = config.get('inflation_std', 0.008)
        
        self.return_min = config.get('return_min', -0.10)
        self.return_max = config.get('return_max', 0.15)
        
        self.career_crisis_age_start = config.get('career_crisis_age_start', 35)
        self.layoff_probability = config.get('layoff_probability', 0.15)
        self.salary_cut_ratio = config.get('salary_cut_ratio', 0.70)
        self.early_growth_rate = config.get('early_growth_rate', 0.05)
        self.post_retirement_income = config.get('post_retirement_income', 0)

    def simulate_lifetime(self, retire_age):
        ages = np.arange(self.current_age, self.life_expectancy + 1)
        # Pre-allocate for all simulations at once for vectorization speedup if possible, 
        # but sticking to loop for logic preservation first.
        # Actually, let's keep the loop structure but clean it up for single run calls or small batch.
        
        assets = np.zeros(len(ages))
        assets[0] = self.current_assets
        
        current_salary = self.annual_income
        current_expense = self.annual_expense
        current_passive_income = self.post_retirement_income
        
        is_ruined = False
        has_experienced_crisis = False
        
        for t in range(1, len(ages)):
            age = ages[t]
            
            # --- Random Variables ---
            inflation = np.random.normal(self.inflation_mean, self.inflation_std)
            inflation = np.clip(inflation, 0.0, 0.10)
            
            investment_return = np.random.uniform(self.return_min, self.return_max)
            
            # --- Update Finances ---
            current_expense *= (1 + inflation)
            
            if age <= retire_age:
                if age < self.career_crisis_age_start:
                    current_salary *= (1 + self.early_growth_rate)
                else:
                    if not has_experienced_crisis:
                        if np.random.random() < self.layoff_probability:
                            current_salary *= self.salary_cut_ratio
                            has_experienced_crisis = True
                        else:
                            current_salary *= 1.02
                    else:
                        current_salary *= 1.02
                
                yearly_cashflow = current_salary - current_expense
            else:
                # After retirement, no salary but we add the passive income
                # Optional: adjust passive income for inflation? 
                # Let's assume it grows with inflation to be consistent with "current value" logic if user inputs current value.
                current_passive_income *= (1 + inflation)
                yearly_cashflow = current_passive_income - current_expense
                
            # --- Assets Update ---
            prev_assets = assets[t-1]
            new_assets = prev_assets * (1 + investment_return) + yearly_cashflow
            
            assets[t] = new_assets
            
            if new_assets < 0:
                is_ruined = True
                assets[t:] = 0
                break
                
        return is_ruined, assets.tolist()

    def run_simulation(self, retire_age_start, retire_age_end):
        results = {}
        
        # 1. Ruin Probability per Retirement Age
        ruin_rates = []
        possible_ages = list(range(retire_age_start, retire_age_end + 1))
        
        optimal_age = None
        min_ruin_rate = 100
        best_age_fallback = possible_ages[-1]
        
        for r_age in possible_ages:
            ruin_count = 0
            for _ in range(self.simulations):
                is_ruined, _ = self.simulate_lifetime(r_age)
                if is_ruined:
                    ruin_count += 1
            rate = (ruin_count / self.simulations) * 100
            ruin_rates.append({'age': r_age, 'rate': rate})
            
            if rate < min_ruin_rate:
                min_ruin_rate = rate
                best_age_fallback = r_age
            
            if optimal_age is None and rate < 5.0:
                optimal_age = r_age
            
        results['ruin_rates'] = ruin_rates

        # 2. Asset Projections Helper
        def get_projection(target_age):
            asset_paths = []
            for _ in range(self.simulations):
                _, path = self.simulate_lifetime(target_age)
                asset_paths.append(path)
            
            asset_paths = np.array(asset_paths)
            return {
                'ages': list(range(self.current_age, self.life_expectancy + 1)),
                'p10': np.percentile(asset_paths, 10, axis=0).tolist(),
                'p50': np.percentile(asset_paths, 50, axis=0).tolist(),
                'p90': np.percentile(asset_paths, 90, axis=0).tolist(),
                'retire_age': target_age
            }

        # 3. Calculate projections for specific ages
        target_retire_age = optimal_age if optimal_age is not None else best_age_fallback
        
        results['projections'] = {
            'recommended': get_projection(target_retire_age),
            'age_30': get_projection(30) if 30 >= self.current_age else None,
            'age_40': get_projection(40) if 40 >= self.current_age else None
        }
        
        return results
