"""
Script de instalación y configuración del entorno de simulación integrada.
"""

import subprocess
import sys
import os
from pathlib import Path


def install_requirements():
    """Instala los paquetes de Python requeridos."""
    print("Instalando dependencias de Python...")
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✓ Dependencias de Python instaladas correctamente")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Error instalando dependencias: {e}")
        return False


def check_openmodelica():
    """Verifica si OpenModelica está instalado."""
    print("Verificando OpenModelica...")
    
    # Ubicaciones típicas de OpenModelica en Windows
    possible_paths = [
        "omc",  # Si está en PATH
        r"C:\Program Files\OpenModelica1.25.1-64bit\bin\omc.exe",
        r"C:\Program Files\OpenModelica\bin\omc.exe",
        r"C:\Program Files (x86)\OpenModelica\bin\omc.exe",
        r"C:\OpenModelica\bin\omc.exe",
    ]
    
    # También verificar variable de entorno
    om_home = os.environ.get('OPENMODELICAHOME')
    if om_home:
        omc_path = os.path.join(om_home, 'bin', 'omc.exe')
        possible_paths.insert(1, omc_path)
    
    for path in possible_paths:
        try:
            if path == "omc":
                # Probar si está en PATH
                result = subprocess.run([path, '--version'], 
                                      capture_output=True, text=True, timeout=10)
            else:
                # Verificar si el archivo existe y es ejecutable
                if os.path.isfile(path):
                    result = subprocess.run([path, '--version'], 
                                          capture_output=True, text=True, timeout=10)
                else:
                    continue
            
            if result.returncode == 0:
                print(f"✓ OpenModelica encontrado en: {path}")
                print(f"  Versión: {result.stdout.strip()}")
                return True
                
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            continue
    
    print("✗ OpenModelica no encontrado en ubicaciones típicas")
    print("  Ubicaciones verificadas:")
    for path in possible_paths[:5]:  # Mostrar las primeras 5
        print(f"    - {path}")
    print("  Nota: La simulación funcionará con modelo físico simplificado")
    return False


def create_directories():
    """Crea los directorios necesarios."""
    print("Creando estructura de directorios...")
    
    directories = [
        "graphs",
        "logs",
        "results",
        "temp"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✓ Directorio {directory}/ creado")


def setup_environment():
    """Configura el entorno de desarrollo."""
    print("="*60)
    print("CONFIGURACIÓN DEL ENTORNO DE SIMULACIÓN INTEGRADA")
    print("="*60)
    
    # Verificar Python
    python_version = sys.version_info
    print(f"Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    if python_version < (3, 8):
        print("✗ Se requiere Python 3.8 o superior")
        return False
    
    # Crear directorios
    create_directories()
    
    # Instalar dependencias
    success = install_requirements()
    if not success:
        return False
    
    # Verificar OpenModelica
    openmodelica_available = check_openmodelica()
    
    print("\n" + "="*60)
    print("CONFIGURACIÓN COMPLETADA")
    print("="*60)
    
    if openmodelica_available:
        print("✓ Entorno completo configurado")
        print("  - Simulación con Modelica disponible")
        print("  - Modelo físico completo activo")
    else:
        print("⚠ Entorno parcialmente configurado")
        print("  - Simulación con modelo simplificado")
        print("  - Para Modelica completo, instalar OpenModelica")
    
    print("\nPara ejecutar la simulación:")
    print("  python main_integrated.py")
    
    return True


def test_installation():
    """Prueba la instalación ejecutando una simulación básica."""
    print("\n" + "="*60)
    print("PRUEBA DE INSTALACIÓN")
    print("="*60)
    
    try:
        # Importar módulos principales
        from src.simulation.integrated_runner import IntegratedSimulationRunner
        from src.weather.generator import generate_weather_profile
        
        print("✓ Importaciones exitosas")
        
        # Configuración de prueba
        config = {
            'cooling_power_multiplier': 1.0,
            'target_temperature': 25.0,
            'save_detailed_results': False,
        }
        
        # Crear runner
        runner = IntegratedSimulationRunner(config)
        print("✓ Runner integrado creado")
        
        # Ejecutar simulación de prueba
        print("Ejecutando simulación de prueba (1 día)...")
        test_result = runner.run_single_day_simulation()
        
        print(f"✓ Simulación exitosa:")
        print(f"  - Temperatura máxima carcasa: {test_result['max_case_temp']:.1f}°C")
        print(f"  - Energía total: {test_result['total_energy']:.2f} kWh")
        print(f"  - Costo: {test_result['cost_eur']:.2f} €")
        
        return True
        
    except Exception as e:
        print(f"✗ Error en prueba: {e}")
        return False


if __name__ == "__main__":
    if setup_environment():
        test_installation()
    else:
        print("✗ Error en la configuración del entorno")
        sys.exit(1)
