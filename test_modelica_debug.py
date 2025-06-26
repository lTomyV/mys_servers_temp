#!/usr/bin/env python3
"""
Script de prueba para diagnosticar problemas con la simulación de Modelica.
"""

import logging
import sys
from pathlib import Path

# Configurar logging detallado
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('debug_modelica.log')
    ]
)

# Agregar la ruta del proyecto al Python path
sys.path.append(str(Path(__file__).parent))

from src.modelica.interface import ModelicaInterface
import numpy as np

def test_modelica_interface():
    """Prueba la interfaz de Modelica con logging detallado."""
    print("🔧 DIAGNÓSTICO DE MODELICA")
    print("=" * 50)
    
    # Buscar el archivo del modelo
    model_path = Path("src/modelica/temperatura_servidor.mo")
    if not model_path.exists():
        print(f"❌ Archivo de modelo no encontrado: {model_path}")
        return
    
    try:
        # Crear interfaz
        interface = ModelicaInterface(str(model_path))
        
        print(f"OpenModelica path: {interface.omc_path}")
        print(f"OpenModelica disponible: {interface.modelica_available}")
        
        if not interface.modelica_available:
            print("❌ OpenModelica no está disponible, usando modelo simplificado")
            return
        
        # Crear datos de prueba simples
        time_vector = np.linspace(0, 3600, 61)  # 1 hora, cada minuto
        exterior_temp = 25.0 + 10.0 * np.sin(time_vector / 3600 * np.pi)  # Variación sinusoidal
        
        print(f"Tiempo: {len(time_vector)} puntos desde {time_vector[0]} hasta {time_vector[-1]}s")
        print(f"Temperatura exterior: {np.min(exterior_temp):.1f} - {np.max(exterior_temp):.1f}°C")
        
        # Ejecutar simulación
        print("\n🚀 Ejecutando simulación de Modelica...")
        results = interface.simulate_server_temperature(
            exterior_temp=exterior_temp,
            time_vector=time_vector,
            cooling_power=1000.0,
            initial_temp=20.0
        )
        
        print("✅ Simulación completada")
        print(f"Resultados: {list(results.keys())}")
        
        if 'T_case' in results:
            T_case = results['T_case']
            print(f"Temperatura de carcasa: {np.min(T_case):.1f} - {np.max(T_case):.1f}°C")
        
    except Exception as e:
        print(f"❌ Error en la prueba: {e}")
        logging.exception("Error detallado:")

if __name__ == "__main__":
    test_modelica_interface()
