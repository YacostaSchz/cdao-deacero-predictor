"""
Análisis de KPIs para CDO DeAcero
Fecha: 2025-09-26
"""

class KPIAnalyzer:
    """Analizador de KPIs para la industria siderúrgica"""
    
    def __init__(self):
        self.current_scrap = 0.05  # 5%
        self.target_scrap = 0.03   # 3%
        self.current_otif = 0.85   # 85%
        self.target_otif = 0.95    # 95%
        self.energy_kwh_ton = 450  # kWh/ton
        self.energy_reduction = 0.10  # 10%
        
    def calculate_scrap_savings(self, annual_production_tons=2_000_000, cost_per_ton=100):
        """Calcula el ahorro potencial por reducción de scrap"""
        reduction = self.current_scrap - self.target_scrap
        tons_saved = annual_production_tons * reduction
        savings = tons_saved * cost_per_ton
        return {
            'reduction_percentage': reduction * 100,
            'tons_saved': tons_saved,
            'annual_savings_usd': savings
        }
    
    def calculate_otif_impact(self, penalty_per_year=900_000):
        """Calcula el impacto de mejorar OTIF"""
        improvement = self.target_otif - self.current_otif
        return {
            'improvement_percentage': improvement * 100,
            'penalties_avoided_usd': penalty_per_year
        }
    
    def calculate_energy_savings(self, annual_production_tons=2_000_000, cost_per_kwh=0.08):
        """Calcula el ahorro por eficiencia energética"""
        current_consumption = annual_production_tons * self.energy_kwh_ton
        reduction_kwh = current_consumption * self.energy_reduction
        savings = reduction_kwh * cost_per_kwh
        return {
            'kwh_saved': reduction_kwh,
            'annual_savings_usd': savings
        }
        
if __name__ == "__main__":
    analyzer = KPIAnalyzer()
    print("=== Análisis de KPIs CDO DeAcero ===")
    print(f"Scrap: {analyzer.calculate_scrap_savings()}")
    print(f"OTIF: {analyzer.calculate_otif_impact()}")
    print(f"Energía: {analyzer.calculate_energy_savings()}")
