"""
Módulo para generar gráficos de análisis temporal del sistema de refrigeración.
Muestra la evolución de temperaturas y potencia a lo largo del tiempo.
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List
import logging

def generar_grafico_evolucion_temporal(resultados: Dict, 
                                     titulo: str = "Evolución Temporal del Sistema de Refrigeración",
                                     guardar_en: str = "graphs/evolucion_temporal.png") -> None:
    """
    Genera un gráfico de la evolución temporal mostrando:
    - Temperatura exterior vs tiempo
    - Temperatura de la carcasa vs tiempo  
    - Potencia de refrigeración vs tiempo
    
    Args:
        resultados: Diccionario con datos de la simulación
        titulo: Título del gráfico
        guardar_en: Ruta donde guardar el gráfico
    """
    
    # Extraer datos
    tiempo = resultados['time']
    temp_exterior = resultados['T_exterior']
    temp_carcasa = resultados['T_case']
    potencia = resultados['cooling_power']
    
    # Convertir tiempo de segundos a horas
    tiempo_horas = tiempo / 3600
    
    # Crear figura con subplots
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(14, 10))
    fig.suptitle(titulo, fontsize=16, fontweight='bold')
    
    # Gráfico 1: Temperatura Exterior
    ax1.plot(tiempo_horas, temp_exterior, 'r-', linewidth=2, label='Temperatura Exterior')
    ax1.set_ylabel('Temperatura [°C]', fontsize=12)
    ax1.set_title('Temperatura Exterior a lo Largo del Día')
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    
    # Añadir información de min/max
    temp_min = np.min(temp_exterior)
    temp_max = np.max(temp_exterior)
    hour_min = tiempo_horas[np.argmin(temp_exterior)]
    hour_max = tiempo_horas[np.argmax(temp_exterior)]
    
    ax1.annotate(f'Mín: {temp_min:.1f}°C\n({hour_min:.1f}h)', 
                xy=(hour_min, temp_min), xytext=(hour_min + 2, temp_min + 3),
                arrowprops=dict(arrowstyle='->', color='blue', alpha=0.7),
                bbox=dict(boxstyle="round,pad=0.3", facecolor='lightblue', alpha=0.7))
    
    ax1.annotate(f'Máx: {temp_max:.1f}°C\n({hour_max:.1f}h)', 
                xy=(hour_max, temp_max), xytext=(hour_max - 2, temp_max - 3),
                arrowprops=dict(arrowstyle='->', color='red', alpha=0.7),
                bbox=dict(boxstyle="round,pad=0.3", facecolor='lightcoral', alpha=0.7))
    
    # Gráfico 2: Temperatura de la Carcasa
    ax2.plot(tiempo_horas, temp_carcasa, 'orange', linewidth=3, label='Temperatura Carcasa')
    ax2.axhline(y=25.0, color='red', linestyle='--', linewidth=2, alpha=0.8, label='Límite Crítico (25°C)')
    ax2.axhline(y=24.0, color='orange', linestyle='--', linewidth=1, alpha=0.6, label='Objetivo (24°C)')
    
    ax2.set_ylabel('Temperatura [°C]', fontsize=12)
    ax2.set_title('Temperatura de la Carcasa del Servidor')
    ax2.grid(True, alpha=0.3)
    ax2.legend()
    
    # Resaltar zonas críticas (> 25°C)
    zonas_criticas = temp_carcasa > 25.0
    if np.any(zonas_criticas):
        ax2.fill_between(tiempo_horas, 25, temp_carcasa, 
                        where=zonas_criticas, color='red', alpha=0.2, 
                        label='Zona Crítica')
    
    # Estadísticas de la carcasa
    carcasa_min = np.min(temp_carcasa)
    carcasa_max = np.max(temp_carcasa)
    carcasa_avg = np.mean(temp_carcasa)
    tiempo_sobre_25 = np.sum(zonas_criticas) * (tiempo_horas[1] - tiempo_horas[0])
    
    stats_text = f'Min: {carcasa_min:.1f}°C | Max: {carcasa_max:.1f}°C | Avg: {carcasa_avg:.1f}°C\nTiempo > 25°C: {tiempo_sobre_25:.1f}h'
    ax2.text(0.02, 0.98, stats_text, transform=ax2.transAxes, 
             bbox=dict(boxstyle="round,pad=0.5", facecolor='wheat', alpha=0.8),
             verticalalignment='top', fontsize=10)
    
    # Gráfico 3: Potencia de Refrigeración
    ax3.plot(tiempo_horas, potencia / 1000, 'purple', linewidth=2, label='Potencia de Refrigeración')
    ax3.fill_between(tiempo_horas, 0, potencia / 1000, alpha=0.3, color='purple')
    
    ax3.set_ylabel('Potencia [kW]', fontsize=12)
    ax3.set_xlabel('Tiempo [horas]', fontsize=12)
    ax3.set_title('Potencia de Refrigeración Dinámica')
    ax3.grid(True, alpha=0.3)
    ax3.legend()
    
    # Estadísticas de potencia
    potencia_min = np.min(potencia)
    potencia_max = np.max(potencia)
    potencia_avg = np.mean(potencia)
    energia_total = float(np.trapz(potencia, dx=(tiempo[1] - tiempo[0]))) / 3600 / 1000  # kWh
    
    power_stats = f'Min: {potencia_min:.0f}W | Max: {potencia_max:.0f}W | Avg: {potencia_avg:.0f}W\nEnergía Total: {energia_total:.2f} kWh'
    ax3.text(0.02, 0.98, power_stats, transform=ax3.transAxes,
             bbox=dict(boxstyle="round,pad=0.5", facecolor='lavender', alpha=0.8),
             verticalalignment='top', fontsize=10)
    
    # Configurar ejes X para mostrar horas del día
    for ax in [ax1, ax2, ax3]:
        ax.set_xlim(0, 24)
        ax.set_xticks(range(0, 25, 3))
        ax.set_xticklabels([f'{h:02d}:00' for h in range(0, 25, 3)])
    
    plt.tight_layout()
    
    # Guardar gráfico
    output_path = Path(guardar_en)
    output_path.parent.mkdir(exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    
    print(f"✅ Gráfico de evolución temporal guardado: {output_path}")
    plt.close()


def generar_grafico_correlacion_temp_potencia(resultados: Dict,
                                             guardar_en: str = "graphs/correlacion_temp_potencia.png") -> None:
    """
    Genera un gráfico de correlación entre temperatura exterior y potencia de refrigeración.
    
    Args:
        resultados: Diccionario con datos de la simulación
        guardar_en: Ruta donde guardar el gráfico
    """
    
    temp_exterior = resultados['T_exterior']
    temp_carcasa = resultados['T_case']
    potencia = resultados['cooling_power']
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle('Correlaciones: Temperatura vs Potencia de Refrigeración', fontsize=14, fontweight='bold')
    
    # Gráfico 1: Temperatura Exterior vs Potencia
    scatter1 = ax1.scatter(temp_exterior, potencia / 1000, c=temp_carcasa, 
                          cmap='coolwarm', alpha=0.6, s=20)
    ax1.set_xlabel('Temperatura Exterior [°C]')
    ax1.set_ylabel('Potencia de Refrigeración [kW]')
    ax1.set_title('Temp. Exterior vs Potencia\n(Color = Temp. Carcasa)')
    ax1.grid(True, alpha=0.3)
    
    # Añadir colorbar
    cbar1 = plt.colorbar(scatter1, ax=ax1)
    cbar1.set_label('Temp. Carcasa [°C]')
    
    # Gráfico 2: Temperatura Carcasa vs Potencia
    ax2.scatter(temp_carcasa, potencia / 1000, c=temp_exterior, 
               cmap='plasma', alpha=0.6, s=20)
    ax2.axvline(x=25.0, color='red', linestyle='--', alpha=0.7, label='Límite 25°C')
    ax2.set_xlabel('Temperatura Carcasa [°C]')
    ax2.set_ylabel('Potencia de Refrigeración [kW]')
    ax2.set_title('Temp. Carcasa vs Potencia\n(Color = Temp. Exterior)')
    ax2.grid(True, alpha=0.3)
    ax2.legend()
    
    # Calcular correlaciones
    corr_ext_pot = np.corrcoef(temp_exterior, potencia)[0, 1]
    corr_car_pot = np.corrcoef(temp_carcasa, potencia)[0, 1]
    
    # Añadir texto con correlaciones
    ax1.text(0.05, 0.95, f'Correlación: {corr_ext_pot:.3f}', 
             transform=ax1.transAxes, bbox=dict(boxstyle="round", facecolor='white', alpha=0.8))
    ax2.text(0.05, 0.95, f'Correlación: {corr_car_pot:.3f}', 
             transform=ax2.transAxes, bbox=dict(boxstyle="round", facecolor='white', alpha=0.8))
    
    plt.tight_layout()
    
    # Guardar gráfico
    output_path = Path(guardar_en)
    output_path.parent.mkdir(exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    
    print(f"✅ Gráfico de correlación guardado: {output_path}")
    plt.close()


def generar_resumen_diario(resultados: Dict,
                          guardar_en: str = "graphs/resumen_diario.png") -> None:
    """
    Genera un resumen visual del día completo en un solo gráfico.
    
    Args:
        resultados: Diccionario con datos de la simulación
        guardar_en: Ruta donde guardar el gráfico
    """
    
    tiempo = resultados['time'] / 3600  # Convertir a horas
    temp_exterior = resultados['T_exterior']
    temp_carcasa = resultados['T_case']
    potencia = resultados['cooling_power']
    
    # Crear figura con eje principal y secundario
    fig, ax1 = plt.subplots(figsize=(15, 8))
    fig.suptitle('Resumen Diario: Temperaturas y Potencia de Refrigeración', 
                 fontsize=16, fontweight='bold')
    
    # Eje principal: Temperaturas
    color1 = 'tab:red'
    color2 = 'tab:orange'
    
    line1 = ax1.plot(tiempo, temp_exterior, color=color1, linewidth=2, 
                     label='Temperatura Exterior', marker='o', markersize=3)
    line2 = ax1.plot(tiempo, temp_carcasa, color=color2, linewidth=3, 
                     label='Temperatura Carcasa', marker='s', markersize=2)
    
    ax1.axhline(y=25.0, color='red', linestyle='--', alpha=0.7, label='Límite Crítico (25°C)')
    ax1.set_xlabel('Hora del Día', fontsize=12)
    ax1.set_ylabel('Temperatura [°C]', fontsize=12, color='black')
    ax1.tick_params(axis='y', labelcolor='black')
    ax1.grid(True, alpha=0.3)
    
    # Eje secundario: Potencia
    ax2 = ax1.twinx()
    color3 = 'tab:purple'
    
    line3 = ax2.plot(tiempo, potencia / 1000, color=color3, linewidth=2, 
                     label='Potencia Refrigeración', alpha=0.8)
    ax2.fill_between(tiempo, 0, potencia / 1000, color=color3, alpha=0.2)
    
    ax2.set_ylabel('Potencia de Refrigeración [kW]', fontsize=12, color=color3)
    ax2.tick_params(axis='y', labelcolor=color3)
    
    # Configurar eje X
    ax1.set_xlim(0, 24)
    ax1.set_xticks(range(0, 25, 2))
    ax1.set_xticklabels([f'{h:02d}:00' for h in range(0, 25, 2)], rotation=45)
    
    # Combinar leyendas
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', 
               bbox_to_anchor=(0.02, 0.98))
    
    # Añadir estadísticas resumidas
    stats_text = f"""ESTADÍSTICAS DEL DÍA:
Temperatura Exterior: {np.min(temp_exterior):.1f}°C - {np.max(temp_exterior):.1f}°C
Temperatura Carcasa: {np.min(temp_carcasa):.1f}°C - {np.max(temp_carcasa):.1f}°C
Tiempo > 25°C: {np.sum(temp_carcasa > 25.0) * (tiempo[1] - tiempo[0]):.1f} horas
Potencia: {np.min(potencia):.0f}W - {np.max(potencia):.0f}W
Energía Total: {float(np.trapz(potencia, dx=(tiempo[1] - tiempo[0])))  / 1000:.2f} kWh"""
    
    ax1.text(0.98, 0.02, stats_text, transform=ax1.transAxes,
             bbox=dict(boxstyle="round,pad=0.5", facecolor='lightgray', alpha=0.9),
             verticalalignment='bottom', horizontalalignment='right', fontsize=10)
    
    plt.tight_layout()
    
    # Guardar gráfico
    output_path = Path(guardar_en)
    output_path.parent.mkdir(exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    
    print(f"✅ Gráfico de resumen diario guardado: {output_path}")
    plt.close()
