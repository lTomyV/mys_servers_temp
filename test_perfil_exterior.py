"""
Script para verificar las temperaturas exteriores en simulaciones largas.
"""
import numpy as np
import matplotlib.pyplot as plt
import sys
import os

# Agregar el directorio raíz al path
sys.path.append('.')

from src.simulation.runner_fisico import crear_perfil_temperatura_exterior
from config.settings import TMIN_MEDIAN, TMAX_MEDIAN, TMIN_SIGMA, TMAX_SIGMA

def test_perfil_31_dias():
    """Prueba el perfil de temperatura exterior para 31 días."""
    print("🧪 Probando perfil de 31 días...")
    
    # Crear perfil de 31 días
    duracion_horas = 31 * 24
    T_exterior = crear_perfil_temperatura_exterior(duracion_horas)
    
    print(f"Puntos generados: {len(T_exterior)} (esperado: {duracion_horas * 2})")
    print(f"Rango de temperaturas: {np.min(T_exterior):.1f}°C - {np.max(T_exterior):.1f}°C")
    print(f"Temperatura promedio: {np.mean(T_exterior):.1f}°C")
    
    # Crear tiempo en días para el gráfico
    tiempo_dias = np.arange(len(T_exterior)) / (2 * 24)  # 2 puntos por hora, 24 horas por día
    
    # Graficar todo el período
    plt.figure(figsize=(15, 8))
    
    plt.subplot(2, 1, 1)
    plt.plot(tiempo_dias, T_exterior, 'b-', linewidth=0.8, alpha=0.7)
    plt.xlabel('Tiempo (días)')
    plt.ylabel('Temperatura (°C)')
    plt.title('Perfil de Temperatura Exterior - 31 Días Completos')
    plt.grid(True, alpha=0.3)
    plt.axhline(y=TMIN_MEDIAN, color='blue', linestyle='--', alpha=0.5, label=f'T_min mediana: {TMIN_MEDIAN}°C')
    plt.axhline(y=TMAX_MEDIAN, color='red', linestyle='--', alpha=0.5, label=f'T_max mediana: {TMAX_MEDIAN}°C')
    plt.legend()
    
    # Zoom en los primeros 3 días
    plt.subplot(2, 1, 2)
    puntos_3_dias = 3 * 24 * 2  # 3 días × 24 horas × 2 puntos/hora
    tiempo_3_dias = tiempo_dias[:puntos_3_dias]
    temp_3_dias = T_exterior[:puntos_3_dias]
    
    plt.plot(tiempo_3_dias, temp_3_dias, 'b-', linewidth=2)
    plt.xlabel('Tiempo (días)')
    plt.ylabel('Temperatura (°C)')
    plt.title('Detalle: Primeros 3 Días')
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('graphs/test_perfil_31_dias.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"✅ Gráfico guardado: graphs/test_perfil_31_dias.png")
    
    # Estadísticas por día para verificar variabilidad
    puntos_por_dia = 48  # 48 puntos por día (cada 30 min)
    dias_completos = len(T_exterior) // puntos_por_dia
    puntos_completos = dias_completos * puntos_por_dia
    
    temperaturas_diarias = T_exterior[:puntos_completos].reshape(-1, puntos_por_dia)
    temps_min_diarias = np.min(temperaturas_diarias, axis=1)
    temps_max_diarias = np.max(temperaturas_diarias, axis=1)
    
    print(f"\nEstadísticas de {dias_completos} días completos:")
    print(f"T_min diarias - Media: {np.mean(temps_min_diarias):.1f}°C, Desv: {np.std(temps_min_diarias):.2f}°C")
    print(f"T_max diarias - Media: {np.mean(temps_max_diarias):.1f}°C, Desv: {np.std(temps_max_diarias):.2f}°C")
    print(f"Rango T_min: {np.min(temps_min_diarias):.1f}°C - {np.max(temps_min_diarias):.1f}°C")
    print(f"Rango T_max: {np.min(temps_max_diarias):.1f}°C - {np.max(temps_max_diarias):.1f}°C")
    
    # Verificar que hay variabilidad real entre días
    variabilidad_min = np.max(temps_min_diarias) - np.min(temps_min_diarias)
    variabilidad_max = np.max(temps_max_diarias) - np.min(temps_max_diarias)
    
    if variabilidad_min > 3:  # Al menos 3°C de variación en mínimas
        print("✅ Variabilidad adecuada en temperaturas mínimas")
    else:
        print(f"❌ Poca variabilidad en mínimas: {variabilidad_min:.1f}°C")
    
    if variabilidad_max > 5:  # Al menos 5°C de variación en máximas
        print("✅ Variabilidad adecuada en temperaturas máximas")
    else:
        print(f"❌ Poca variabilidad en máximas: {variabilidad_max:.1f}°C")

def test_multiples_simulaciones():
    """Prueba múltiples simulaciones cortas para verificar aleatoriedad."""
    print(f"\n🧪 Probando 10 simulaciones de 1 día...")
    
    temps_promedio = []
    temps_min = []
    temps_max = []
    
    for i in range(10):
        T_exterior = crear_perfil_temperatura_exterior(24)  # 1 día
        temps_promedio.append(np.mean(T_exterior))
        temps_min.append(np.min(T_exterior))
        temps_max.append(np.max(T_exterior))
    
    print(f"Temperatura promedio por simulación:")
    for i, temp in enumerate(temps_promedio):
        print(f"  Sim {i+1}: {temp:.1f}°C (min: {temps_min[i]:.1f}°C, max: {temps_max[i]:.1f}°C)")
    
    variabilidad_promedio = np.std(temps_promedio)
    variabilidad_mins = np.std(temps_min)
    variabilidad_maxs = np.std(temps_max)
    
    print(f"\nVariabilidad entre simulaciones:")
    print(f"  Promedio: σ={variabilidad_promedio:.2f}°C")
    print(f"  Mínimas: σ={variabilidad_mins:.2f}°C")
    print(f"  Máximas: σ={variabilidad_maxs:.2f}°C")
    
    if variabilidad_promedio > 1:
        print("✅ Buena variabilidad entre simulaciones")
    else:
        print("❌ Poca variabilidad entre simulaciones")

if __name__ == "__main__":
    os.makedirs('graphs', exist_ok=True)
    test_perfil_31_dias()
    test_multiples_simulaciones()
    print(f"\n🎉 Pruebas completadas.")
