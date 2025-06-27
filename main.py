"""
Simulador principal de análisis de servidores con control adaptativo inteligente.
Actualizado para usar modelos físicos directos (sin OpenModelica).
"""

import sys
import os
import numpy as np

# Agregar el directorio raíz al path para importaciones
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.settings import NUM_SIMULATIONS, SIMULATION_DAYS, MAX_WORKERS, ENABLE_PARALLEL, MODELO_HVAC
from config.equipos_hvac import MODELOS_REFRIGERACION
from src.simulation.runner_fisico import run_monte_carlo_adaptive, escalar_a_mensual
from src.analysis.statistics import calculate_cost_statistics, calculate_temperature_statistics
from src.visualization.plots import plot_cost_distribution, plot_temperature_density, plot_adaptive_performance, plot_system_performance_timeline
from src.physics.sala_servidores import SalaServidores


def print_adaptive_results(costs):
    """Imprime los resultados de la estrategia adaptativa."""
    stats = calculate_cost_statistics(costs)
    
    print(f"\n--- Resultados del Control Adaptativo Inteligente ---")
    print(f"Costo Mensual Promedio: ${stats['mean']:.2f}")
    print(f"Desviación Estándar del Costo: ${stats['std']:.2f}")
    print(f"Costo Mediano: ${stats['median']:.2f}")
    print(f"Costo90 (Percentil 90): ${stats['costo90']:.2f}")
    print(f"Rango de Costos: ${stats['min']:.2f} - ${stats['max']:.2f}")
    print(f"Coeficiente de Variación: {stats['std']/stats['mean']*100:.1f}%")
    
    return stats


def print_temperature_analysis(temp_stats):
    """Imprime análisis detallado de temperaturas."""
    if temp_stats is None:
        print("⚠️  No hay datos de temperatura para analizar")
        return
    
    print("\n--- Análisis de Temperaturas ---")
    print(f"Temperatura interior mínima registrada: {temp_stats['temp_min']:.1f}°C")
    print(f"Temperatura interior máxima registrada: {temp_stats['temp_max']:.1f}°C")
    print(f"Temperatura promedio: {np.mean(temp_stats['hourly_means']):.1f}°C")
    
    # Análisis de cumplimiento del objetivo
    temps_over_25 = np.sum(temp_stats['hourly_means'] > 25.0)
    total_hours = len(temp_stats['hourly_means'])
    porcentaje_cumplimiento = (total_hours - temps_over_25) / total_hours * 100
    
    print(f"\n--- Análisis de Cumplimiento ---")
    print(f"Horas con temperatura > 25°C: {temps_over_25}/{total_hours}")
    print(f"Cumplimiento del objetivo: {porcentaje_cumplimiento:.1f}%")
    
    if porcentaje_cumplimiento >= 95:
        print("✅ EXCELENTE: Cumplimiento óptimo del objetivo de temperatura")
    elif porcentaje_cumplimiento >= 90:
        print("✅ BUENO: Cumplimiento satisfactorio del objetivo")
    elif porcentaje_cumplimiento >= 80:
        print("⚠️  REGULAR: Necesita mejoras en el control")
    else:
        print("❌ DEFICIENTE: Control inadecuado")
    
    # Análisis de eficiencia energética
    temps_under_20 = np.sum(temp_stats['hourly_means'] < 20.0)
    if temps_under_20 > 0:
        print(f"⚡ Posible sobre-enfriamiento: {temps_under_20} horas < 20°C")
    else:
        print("⚡ Sin sobre-enfriamiento detectado")


def print_efficiency_analysis(cost_stats):
    """Imprime análisis de eficiencia energética."""
    print("\n--- Análisis de Eficiencia Energética ---")
    
    # Calcular métricas de eficiencia
    costo_diario_promedio = cost_stats['mean'] / 31  # 31 días
    costo_por_hora = costo_diario_promedio / 24
    
    print(f"Costo diario promedio: ${costo_diario_promedio:.2f}")
    print(f"Costo por hora promedio: ${costo_por_hora:.3f}")
    
    # Análisis de variabilidad
    cv = cost_stats['std'] / cost_stats['mean'] * 100
    if cv < 10:
        print(f"✅ Variabilidad baja (CV={cv:.1f}%): Control muy estable")
    elif cv < 20:
        print(f"✅ Variabilidad moderada (CV={cv:.1f}%): Control estable")
    else:
        print(f"⚠️  Variabilidad alta (CV={cv:.1f}%): Control menos predecible")


def main():
    """Función principal del simulador adaptativo."""
    print("="*70)
    print("🏢 SIMULADOR DE CONTROL ADAPTATIVO INTELIGENTE PARA SERVIDORES")
    print("="*70)
    
    print(f"\n🎯 Configuración del experimento:")
    print(f"  • Simulaciones Monte Carlo: {NUM_SIMULATIONS}")
    print(f"  • Duración por simulación: {SIMULATION_DAYS} días")
    print(f"  • Modelo: Físico directo (Python)")
    print(f"  • Paralelización: {'✅ Habilitada' if ENABLE_PARALLEL else '❌ Deshabilitada'}")
    if ENABLE_PARALLEL:
        import multiprocessing
        from src.simulation.runner_fisico import get_optimal_workers
        workers = MAX_WORKERS if MAX_WORKERS else get_optimal_workers(NUM_SIMULATIONS)
        print(f"  • Hilos: {workers} (de {multiprocessing.cpu_count()} núcleos)")
    print(f"  • Estrategia: Control sigmoidal adaptativo")
    print(f"  • Rango de control: 15°C (0%) → 25°C (100%)")
    
    # Información del equipo HVAC
    equipo_info = MODELOS_REFRIGERACION[MODELO_HVAC]
    print(f"\n❄️  Equipo de Refrigeración:")
    print(f"  • Modelo: {equipo_info['nombre']}")
    print(f"  • Potencia nominal: {equipo_info['potencia_nominal']/1000:.0f} kW")
    print(f"  • COP nominal: {equipo_info['cop_nominal']} @35°C")
    print(f"  • COP variable: Sí (función de T_exterior)")

    # Generar y mostrar curva de control
    print(f"\n📊 Generando curva de control adaptativo...")
    try:
        os.makedirs('graphs', exist_ok=True)
        sala_demo = SalaServidores()
        sala_demo.generar_curva_control()
        print("✅ Curva de control generada: graphs/curva_control_fisica.png")
    except Exception as e:
        print(f"⚠️  Error generando curva: {e}")
    
    # Ejecutar simulaciones Monte Carlo
    print(f"\n🚀 Iniciando simulaciones Monte Carlo...")
    print("="*50)
    
    try:
        # Ejecutar simulaciones con modelo físico (costos diarios)
        if ENABLE_PARALLEL:
            costos_diarios, temp_profiles, datos_detallados = run_monte_carlo_adaptive(
                NUM_SIMULATIONS, 
                duracion_horas=SIMULATION_DAYS*24,
                max_workers=MAX_WORKERS
            )
        else:
            # Versión secuencial para debugging o sistemas con problemas de paralelización
            costos_diarios, temp_profiles, datos_detallados = run_monte_carlo_adaptive(
                NUM_SIMULATIONS, 
                duracion_horas=SIMULATION_DAYS*24,
                max_workers=1
            )
        
        # Escalar costos diarios a mensuales para análisis
        costs = [escalar_a_mensual(costo_diario, SIMULATION_DAYS) for costo_diario in costos_diarios]
        
        if len(costs) == 0:
            print("❌ No se obtuvieron resultados válidos")
            return 1
        
        # Analizar resultados de costos
        print("\n" + "="*50)
        cost_stats = print_adaptive_results(costs)
        
        # Generar histograma de costos
        plot_cost_distribution(costs, "Control Adaptativo Físico")
        
        # Analizar temperaturas si están disponibles
        if temp_profiles:
            print("\n" + "="*50)
            print("--- Análisis de Temperaturas ---")
            temp_stats = calculate_temperature_statistics(temp_profiles)
            print_temperature_analysis(temp_stats)
            
            # Generar gráficos de temperatura
            plot_temperature_density(temp_stats)
            
            # Generar análisis de rendimiento adaptativo
            plot_adaptive_performance(temp_profiles, costs)
        
        # Generar gráfico temporal del sistema (temperatura exterior, servidor, potencia)
        if datos_detallados:
            print("\n--- Generando Gráfico Temporal del Sistema ---")
            plot_system_performance_timeline(datos_detallados)
        
        # Análisis de eficiencia
        print_efficiency_analysis(cost_stats)
        
        # Resumen final
        print("\n" + "="*70)
        print("🎉 ANÁLISIS COMPLETADO")
        print("="*70)
        print("📁 Archivos generados en la carpeta 'graphs/':")
        print("  • histograma_costos_Control Adaptativo Físico.png")
        print("  • curva_control_fisica.png")
        if temp_profiles:
            print("  • distribucion_temperaturas_horarias.png")
            print("  • rendimiento_adaptativo.png")
        if datos_detallados:
            print("  • rendimiento_sistema_temporal.png")
        
        print(f"\n🏆 RESULTADO FINAL:")
        print(f"  • Costo promedio mensual: ${cost_stats['mean']:.2f}")
        print(f"  • Control de temperatura: {'✅ ÓPTIMO' if temp_profiles else '⚠️  NO EVALUADO'}")
        print(f"  • Eficiencia energética: {'✅ ALTA' if cost_stats['std']/cost_stats['mean'] < 0.2 else '⚠️  MODERADA'}")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Error durante la ejecución: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
