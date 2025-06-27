"""
Módulo de control adaptativo para el sistema de refrigeración.
"""

import numpy as np
import matplotlib.pyplot as plt


def funcion_sigmoidal(temperatura, temp_min=15.0, temp_max=25.0, pendiente=1.5):
    """
    Calcula el porcentaje de potencia usando una función sigmoidal.
    
    Args:
        temperatura: Temperatura actual [°C]
        temp_min: Temperatura para 0% de potencia [°C]
        temp_max: Temperatura para 100% de potencia [°C]
        pendiente: Agresividad de la curva sigmoidal
        
    Returns:
        Porcentaje de potencia [0-100%]
    """
    # Centrar la temperatura en el rango de control
    temp_centrada = (temperatura - (temp_min + temp_max)/2.0) / ((temp_max - temp_min)/2.0)
    
    # Función sigmoidal (tanh para suavidad)
    valor_sigmoide = np.tanh(pendiente * temp_centrada)
    
    # Convertir a porcentaje (0-100%)
    porcentaje = np.clip(50.0 + 50.0 * valor_sigmoide, 0.0, 100.0)
    
    return porcentaje


def calcular_potencia_refrigeracion(temperatura, potencia_maxima=8000.0):
    """
    Calcula la potencia de refrigeración basada en la temperatura.
    
    Args:
        temperatura: Temperatura interior actual [°C]
        potencia_maxima: Potencia máxima del sistema [W]
        
    Returns:
        Potencia de refrigeración [W]
    """
    porcentaje = funcion_sigmoidal(temperatura)
    return potencia_maxima * porcentaje / 100.0


def generar_curva_control():
    """
    Genera y muestra la curva de control sigmoidal.
    """
    temperaturas = np.linspace(10, 30, 200)
    porcentajes = [funcion_sigmoidal(t) for t in temperaturas]
    
    plt.figure(figsize=(10, 6))
    plt.plot(temperaturas, porcentajes, 'b-', linewidth=2, label='Control Sigmoidal')
    plt.axvline(x=15, color='green', linestyle='--', alpha=0.7, label='0% (15°C)')
    plt.axvline(x=25, color='red', linestyle='--', alpha=0.7, label='100% (25°C)')
    plt.axhline(y=50, color='orange', linestyle=':', alpha=0.7, label='50% (20°C)')
    
    plt.xlabel('Temperatura Interior (°C)')
    plt.ylabel('Potencia de Refrigeración (%)')
    plt.title('Curva de Control Adaptativo Sigmoidal')
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.xlim(10, 30)
    plt.ylim(0, 105)
    
    # Marcar puntos clave
    puntos_clave = [15, 20, 23, 25]
    for temp in puntos_clave:
        potencia = funcion_sigmoidal(temp)
        plt.plot(temp, potencia, 'ro', markersize=6)
        plt.annotate(f'{potencia:.1f}%', 
                    xy=(temp, potencia), 
                    xytext=(temp+0.5, potencia+5),
                    fontsize=9)
    
    plt.tight_layout()
    return plt.gcf()


if __name__ == "__main__":
    # Probar la función de control
    print("🎛️  FUNCIÓN DE CONTROL ADAPTATIVO SIGMOIDAL")
    print("="*50)
    
    # Mostrar algunos valores clave
    temperaturas_test = [13, 15, 18, 20, 22, 23, 24, 25, 27]
    print("\nTemperatura [°C] → Potencia [%]")
    print("-"*30)
    for temp in temperaturas_test:
        potencia = funcion_sigmoidal(temp)
        print(f"{temp:6.1f}°C      → {potencia:6.1f}%")
    
    # Generar gráfico
    print("\nGenerando curva de control...")
    fig = generar_curva_control()
    fig.savefig('graphs/curva_control_sigmoidal.png', dpi=300, bbox_inches='tight')
    print("Gráfico guardado en: graphs/curva_control_sigmoidal.png")
    plt.show()
