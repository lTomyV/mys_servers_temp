"""
Script de prueba rápida para verificar extracción de datos optimizada
"""
import os
import sys
sys.path.append('.')

from src.simulation.runner import create_and_run_adaptive_simulation

def test_optimized_simulation():
    """Prueba una simulación optimizada y verifica la extracción."""
    
    print("🚀 Iniciando prueba de simulación optimizada...")
    print("="*50)
    
    # Ejecutar simulación de prueba
    cost, temps = create_and_run_adaptive_simulation(9999)
    
    if cost is not None:
        print(f"✅ Simulación exitosa!")
        print(f"💰 Costo extraído: ${cost:.2f}")
        
        if temps is not None:
            print(f"🌡️  Temperaturas extraídas: {len(temps)} puntos")
            print(f"   Rango: {min(temps):.1f}°C - {max(temps):.1f}°C")
            print(f"   Promedio: {sum(temps)/len(temps):.1f}°C")
            
            # Verificar cumplimiento de objetivo
            temps_over_25 = sum(1 for t in temps if t > 25.0)
            cumplimiento = (len(temps) - temps_over_25) / len(temps) * 100
            print(f"   Cumplimiento objetivo (≤25°C): {cumplimiento:.1f}%")
        else:
            print("⚠️  No se extrajeron temperaturas")
        
        return True
    else:
        print("❌ Fallo en la simulación")
        return False

if __name__ == "__main__":
    success = test_optimized_simulation()
    
    if success:
        print("\n🎉 Prueba exitosa! Proceder con simulación completa.")
    else:
        print("\n❌ Prueba falló. Revisar configuración.")
