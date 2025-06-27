"""
Test rápido para verificar que los costos sean realistas
con los nuevos parámetros.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.simulation.runner_fisico import ejecutar_simulacion_fisica
from config.settings import COST_PER_KWH, SIMULATION_DAYS

def test_costos_realistas():
    """Ejecuta una simulación corta para verificar costos."""
    print("🧪 Test de Costos Realistas")
    print("=" * 50)
    
    print(f"📊 Parámetros actualizados:")
    print(f"  • Carga térmica servidor: 15 kW")
    print(f"  • Potencia refrigeración: 35 kW") 
    print(f"  • Precio energía: ${COST_PER_KWH}/kWh")
    print(f"  • COP variable: Sí (función T_exterior)")
    
    print(f"\n🚀 Ejecutando simulación de 3 días...")
    
    try:
        # Ejecutar simulación corta (3 días = 72 horas)
        costo_total, temps, datos_detalle = ejecutar_simulacion_fisica(1, duracion_horas=72)
        
        if costo_total is not None:
            # Escalar a mensual
            costo_diario = costo_total / 3
            costo_mensual = costo_diario * 31
            
            print(f"\n💰 Resultados de Costos:")
            print(f"  • Costo 3 días: ${costo_total:.2f}")
            print(f"  • Costo diario: ${costo_diario:.2f}")
            print(f"  • Costo mensual estimado: ${costo_mensual:.2f}")
            
            # Análisis de uso de refrigeración
            if datos_detalle and 'P_refrigeracion' in datos_detalle:
                potencias = datos_detalle['P_refrigeracion']
                potencia_prom = sum(potencias) / len(potencias) if potencias else 0
                porcentaje_uso = (potencia_prom / 35000) * 100  # vs 35kW máximo
                
                print(f"\n⚡ Análisis de Consumo:")
                print(f"  • Potencia promedio: {potencia_prom/1000:.1f} kW ({porcentaje_uso:.1f}% de capacidad)")
                print(f"  • Consumo eléctrico estimado: {potencia_prom/3200:.1f} kW (asumiendo COP=3.2)")
                
                # Verificar que los costos estén en rango razonable
                if 800 <= costo_mensual <= 3000:
                    print(f"\n✅ Los costos están en rango razonable para una sala de servidores")
                elif costo_mensual < 800:
                    print(f"\n⚠️  Los costos parecen bajos. Revisar parámetros.")
                else:
                    print(f"\n⚠️  Los costos parecen altos. Verificar configuración.")
            
        else:
            print("❌ Error en la simulación")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_costos_realistas()
