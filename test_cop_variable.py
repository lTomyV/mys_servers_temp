"""
Script de prueba para verificar el funcionamiento del COP variable
basado en la temperatura exterior.
"""

import numpy as np
import matplotlib.pyplot as plt
import sys
import os

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.equipos_hvac import MODELOS_REFRIGERACION
from config.settings import COST_PER_KWH

def test_cop_curves():
    """Prueba y grafica las curvas de COP para todos los modelos."""
    print("🔬 Probando curvas de COP variable...")
    
    # Rango de temperaturas exteriores para evaluar
    T_exterior = np.linspace(25, 45, 100)  # 25°C a 45°C
    
    plt.figure(figsize=(12, 8))
    
    colors = ['blue', 'green', 'red']
    
    for i, (modelo, info) in enumerate(MODELOS_REFRIGERACION.items()):
        cop_values = [info['cop_curve'](T) for T in T_exterior]
        
        plt.subplot(2, 2, i+1)
        plt.plot(T_exterior, cop_values, color=colors[i], linewidth=2, label=f'COP real')
        plt.axhline(y=info['cop_nominal'], color=colors[i], linestyle='--', alpha=0.7, 
                   label=f'COP nominal: {info["cop_nominal"]}')
        plt.axvline(x=35, color='gray', linestyle=':', alpha=0.5, label='35°C (referencia)')
        
        plt.title(f'{info["nombre"]}\nPotencia: {info["potencia_nominal"]/1000:.0f} kW')
        plt.xlabel('Temperatura Exterior (°C)')
        plt.ylabel('COP')
        plt.grid(True, alpha=0.3)
        plt.legend()
        
        # Mostrar algunos valores específicos
        cop_30 = info['cop_curve'](30)
        cop_35 = info['cop_curve'](35)
        cop_40 = info['cop_curve'](40)
        
        print(f"\n📊 {info['nombre']}:")
        print(f"  • COP a 30°C: {cop_30:.2f}")
        print(f"  • COP a 35°C: {cop_35:.2f} (nominal: {info['cop_nominal']})")
        print(f"  • COP a 40°C: {cop_40:.2f}")
        print(f"  • Degradación: {(cop_35-cop_40)/5:.3f} COP/°C")
    
    # Gráfico de comparación
    plt.subplot(2, 2, 4)
    for modelo, info in MODELOS_REFRIGERACION.items():
        cop_values = [info['cop_curve'](T) for T in T_exterior]
        plt.plot(T_exterior, cop_values, linewidth=2, label=info['nombre'])
    
    plt.title('Comparación de Modelos')
    plt.xlabel('Temperatura Exterior (°C)')
    plt.ylabel('COP')
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.axvline(x=35, color='gray', linestyle=':', alpha=0.5, label='35°C')
    
    # Resaltar el rango típico de nuestras simulaciones (30-42°C)
    plt.axvspan(30, 42, alpha=0.2, color='yellow', label='Rango simulación')
    
    plt.tight_layout()
    plt.savefig('graphs/test_cop_curves.png', dpi=300, bbox_inches='tight')
    print(f"\n📊 Gráfico guardado: graphs/test_cop_curves.png")
    
    return True

def test_energy_consumption():
    """Calcula el consumo energético teórico para diferentes temperaturas."""
    print(f"\n⚡ Análisis de Consumo Energético:")
    
    # Suponer potencia de refrigeración constante de 50kW (escenario típico)
    P_refrig = 50000  # W
    horas = 1  # 1 hora de operación
    
    print(f"\nEscenario: {P_refrig/1000:.0f} kW de refrigeración durante {horas} hora(s)")
    print(f"Precio energía: ${COST_PER_KWH}/kWh")
    print("-" * 60)
    
    temps = [30, 35, 40, 42]  # Temperaturas exteriores típicas
    
    for temp in temps:
        print(f"\nTemperatura exterior: {temp}°C")
        print("Modelo            COP    Consumo(kW)  Costo/hora($)")
        print("-" * 45)
        
        for modelo, info in MODELOS_REFRIGERACION.items():
            cop = info['cop_curve'](temp)
            consumo_kW = P_refrig / cop / 1000  # kW
            costo_hora = consumo_kW * COST_PER_KWH  # Usar precio actualizado
            
            print(f"{modelo:<15} {cop:>5.2f}  {consumo_kW:>8.1f}    {costo_hora:>8.2f}")

if __name__ == "__main__":
    print("🧪 Test de Equipos HVAC con COP Variable")
    print("=" * 50)
    
    # Crear directorio de gráficos si no existe
    os.makedirs('graphs', exist_ok=True)
    
    # Probar curvas de COP
    test_cop_curves()
    
    # Análisis de consumo energético
    test_energy_consumption()
    
    print("\n🎉 Test completado!")
    print("Ahora el sistema usa COP variable basado en temperatura exterior real.")
