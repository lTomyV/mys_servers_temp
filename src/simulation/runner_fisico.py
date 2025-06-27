"""
Módulo para ejecutar simulaciones Monte Carlo usando modelos físicos directos.
Optimizado con paralelización para múltiples núcleos.
"""

import os
import sys
import numpy as np
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import multiprocessing

# Agregar el directorio raíz al path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from config.settings import COST_PER_KWH
from src.weather.generator import generate_weather_profile, generate_hourly_temperature_profile
from src.physics.sala_servidores import SalaServidores


def crear_perfil_temperatura_exterior(duracion_horas=24):
    """
    Crea un perfil de temperatura exterior realista usando el generador climático.
    
    Args:
        duracion_horas: Duración de la simulación en horas
    
    Returns:
        Array con temperaturas exteriores cada 30 minutos
    """
    # Calcular número de días completos
    num_dias = int(np.ceil(duracion_horas / 24))
    
    # Generar perfil climático para todos los días necesarios
    t_min_daily, t_max_daily, hour_min_daily, hour_max_daily = generate_weather_profile()
    
    # Si necesitamos más días que los generados (31), generar días adicionales
    if num_dias > len(t_min_daily):
        dias_adicionales = num_dias - len(t_min_daily)
        t_min_extra, t_max_extra, hour_min_extra, hour_max_extra = generate_weather_profile()
        
        # Tomar solo los días adicionales que necesitamos
        t_min_daily = np.concatenate([t_min_daily, t_min_extra[:dias_adicionales]])
        t_max_daily = np.concatenate([t_max_daily, t_max_extra[:dias_adicionales]])
        hour_min_daily = np.concatenate([hour_min_daily, hour_min_extra[:dias_adicionales]])
        hour_max_daily = np.concatenate([hour_max_daily, hour_max_extra[:dias_adicionales]])
    
    # Generar perfil horario completo usando todos los días
    perfil_horario = generate_hourly_temperature_profile(
        t_min_daily[:num_dias], t_max_daily[:num_dias], 
        hour_min_daily[:num_dias], hour_max_daily[:num_dias]
    )
    
    # Interpolar a intervalos de 30 minutos
    perfil_30min = []
    for i in range(len(perfil_horario) - 1):
        T1, T2 = perfil_horario[i], perfil_horario[i + 1]
        perfil_30min.append(T1)
        perfil_30min.append((T1 + T2) / 2)  # Interpolación lineal
    
    # Agregar el último punto
    perfil_30min.append(perfil_horario[-1])
    
    # Truncar al número exacto de puntos necesarios
    puntos_necesarios = int(duracion_horas * 2)  # 2 puntos por hora (cada 30 min)
    return np.array(perfil_30min[:puntos_necesarios])


def ejecutar_simulacion_fisica(run_id, duracion_horas=24):
    """
    Ejecuta una simulación completa usando el modelo físico.
    Optimizada para ejecución en paralelo (thread-safe).
    
    Args:
        run_id: Identificador de la simulación
        duracion_horas: Duración en horas
    
    Returns:
        tuple: (costo_total, temperaturas_servidor) o (None, None) si falla
    """
    try:
        # No imprimir cada simulación individual para evitar mezclar output en paralelo
        start_time = time.time()
        
        # Crear modelo de sala de servidores (cada hilo tiene su propia instancia)
        sala = SalaServidores()
        
        # Generar perfil de temperatura exterior (usa random, que es thread-safe en Python)
        T_exterior = crear_perfil_temperatura_exterior(duracion_horas)
        
        # Ejecutar simulación
        tiempo_simulacion = duracion_horas * 3600  # Convertir a segundos
        resultados = sala.simular(tiempo_simulacion, T_exterior, dt=1800)  # dt = 30 min
        
        if resultados['success']:
            # Calcular costo
            energia_kWh = resultados['energia_total_kWh']
            costo_total = sala.calcular_costo_energetico(energia_kWh, COST_PER_KWH)
            
            # Extraer temperaturas del servidor (remuestreadas a intervalos horarios)
            temps_servidor = resultados['T_servidor']
            indices_horarios = np.arange(0, len(temps_servidor), 2)  # Cada 2 puntos = 1 hora
            temps_horarias = temps_servidor[indices_horarios]
            
            # Para el gráfico detallado, también extraer otros datos horarios
            potencias_refrig = resultados['P_refrigeracion']
            potencias_horarias = potencias_refrig[indices_horarios]
            
            # COP real (si está disponible)
            cop_real = resultados.get('COP_real', None)
            cop_horarios = cop_real[indices_horarios] if cop_real is not None else None
            
            # Temperatura exterior también remuestreada a horarios
            temp_ext_horarias = T_exterior[::1]  # T_exterior ya está en intervalos horarios
            
            elapsed_time = time.time() - start_time
            objetivo_cumplido = '✅' if resultados['objetivo_cumplido'] else '❌'
            
            # Retornar datos completos para análisis detallado
            datos_completos = {
                'T_servidor': temps_horarias,
                'T_exterior': temp_ext_horarias[:len(temps_horarias)],  # Ajustar longitud
                'P_refrigeracion': potencias_horarias,
                'COP_real': cop_horarios,
                'tiempo_horas': np.arange(len(temps_horarias)),
                'equipo_info': resultados.get('equipo_info', {})
            }
            
            return costo_total, temps_horarias, datos_completos
        else:
            return None, None, None
            
    except Exception as e:
        # En paralelo, retornar None en lugar de imprimir errores que se mezclan
        return None, None, None


def run_monte_carlo_adaptive(num_simulations, duracion_horas=24, max_workers=None):
    """
    Ejecuta simulaciones Monte Carlo usando modelos físicos con paralelización.
    
    Args:
        num_simulations: Número de simulaciones
        duracion_horas: Duración de cada simulación en horas
        max_workers: Número máximo de hilos (None = auto-detectar núcleos)
    
    Returns:
        tuple: (array_costos, lista_perfiles_temperatura)
    """
    
    # Auto-detectar número de núcleos si no se especifica
    if max_workers is None:
        max_workers = get_optimal_workers(num_simulations)
    
    print(f"\n🎯 Iniciando {num_simulations} simulaciones Monte Carlo con modelo físico...")
    print(f"⏱️  Duración por simulación: {duracion_horas} horas")
    print(f"🔬 Usando modelos físicos directos (sin OpenModelica)")
    print(f"🚀 Paralelización: {max_workers} hilos en {multiprocessing.cpu_count()} núcleos disponibles")
    
    costs = []
    temperature_profiles = []
    detailed_data = []  # Para almacenar datos detallados de algunas simulaciones
    successful_runs = 0
    start_time = time.time()
    
    # Función auxiliar para ejecutar una simulación individual
    def run_single_simulation(run_id):
        return ejecutar_simulacion_fisica(run_id, duracion_horas)
    
    # Ejecutar simulaciones en paralelo
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Enviar todas las simulaciones al pool de hilos
        future_to_run_id = {
            executor.submit(run_single_simulation, i+1): i+1 
            for i in range(num_simulations)
        }
        
        completed_count = 0
        
        # Procesar resultados conforme van completándose
        for future in as_completed(future_to_run_id):
            run_id = future_to_run_id[future]
            completed_count += 1
            
            try:
                cost, temps, datos_detalle = future.result()
                
                if cost is not None:
                    costs.append(cost)
                    if temps is not None:
                        temperature_profiles.append(temps)
                    # Guardar datos detallados solo de las primeras simulaciones para el gráfico
                    if len(detailed_data) < 3 and datos_detalle is not None:
                        detailed_data.append(datos_detalle)
                    successful_runs += 1
                    
                    # Mostrar progreso
                    elapsed = time.time() - start_time
                    avg_time = elapsed / completed_count
                    eta = avg_time * (num_simulations - completed_count)
                    
                    print(f"✅ Simulación {run_id} completada ({completed_count}/{num_simulations}) - "
                          f"${cost:.3f} - ETA: {eta/60:.1f}min")
                else:
                    print(f"❌ Simulación {run_id} falló")
                
                # Mostrar progreso cada 10 simulaciones o al final
                if completed_count % 10 == 0 or completed_count == num_simulations:
                    progress_pct = (completed_count / num_simulations) * 100
                    print(f"📈 Progreso: {progress_pct:.1f}% ({successful_runs}/{completed_count} exitosas)")
                    
            except Exception as e:
                print(f"❌ Error inesperado en simulación {run_id}: {e}")
    
    total_time = time.time() - start_time
    speedup = num_simulations / total_time if total_time > 0 else 0
    
    print(f"\n🎉 Completadas {successful_runs}/{num_simulations} simulaciones exitosas")
    print(f"⏱️  Tiempo total: {total_time:.1f}s ({speedup:.1f} sim/s)")
    print(f"🚀 Aceleración promedio: {speedup/max_workers:.1f}x por núcleo")
    
    if successful_runs == 0:
        raise RuntimeError("❌ No se completó ninguna simulación exitosamente")
    
    return np.array(costs), temperature_profiles, detailed_data


def escalar_a_mensual(costo_diario, dias=31):
    """Escala un costo diario a mensual."""
    return costo_diario * dias


def get_optimal_workers(num_simulations):
    """
    Determina el número óptimo de hilos para las simulaciones.
    
    Args:
        num_simulations: Número total de simulaciones
        
    Returns:
        int: Número óptimo de hilos
    """
    cpu_count = multiprocessing.cpu_count()
    
    # Para pocas simulaciones, no usar todos los núcleos
    if num_simulations <= 4:
        return min(num_simulations, 2)
    
    # Para simulaciones medianas, usar la mayoría de núcleos
    elif num_simulations <= 20:
        return min(cpu_count - 1, num_simulations)
    
    # Para muchas simulaciones, usar todos los núcleos disponibles
    else:
        return min(cpu_count, num_simulations)


if __name__ == "__main__":
    # Prueba rápida del sistema
    print("🧪 Ejecutando prueba del sistema físico...")
    
    # Probar una simulación
    cost, temps, datos_detalle = ejecutar_simulacion_fisica(999, duracion_horas=24)
    
    if cost is not None:
        costo_mensual = escalar_a_mensual(cost)
        print(f"✅ Prueba exitosa:")
        print(f"   💰 Costo diario: ${cost:.3f}")
        print(f"   💰 Costo mensual estimado: ${costo_mensual:.2f}")
        if temps is not None:
            print(f"   🌡️  Temperaturas: {len(temps)} puntos, rango {np.min(temps):.1f}-{np.max(temps):.1f}°C")
    else:
        print("❌ Prueba falló")
    
    # Probar Monte Carlo pequeño con paralelización
    print(f"\n🧪 Probando Monte Carlo con 3 simulaciones (paralelo)...")
    try:
        costos, temps_profiles, datos_detallados = run_monte_carlo_adaptive(3, duracion_horas=24, max_workers=2)
        costos_mensuales = [escalar_a_mensual(c) for c in costos]
        print(f"✅ Monte Carlo paralelo exitoso:")
        print(f"   💰 Costos mensuales: ${np.min(costos_mensuales):.2f} - ${np.max(costos_mensuales):.2f}")
        print(f"   💰 Promedio: ${np.mean(costos_mensuales):.2f}")
    except Exception as e:
        print(f"❌ Error en Monte Carlo paralelo: {e}")
