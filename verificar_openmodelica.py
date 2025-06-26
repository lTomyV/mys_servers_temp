#!/usr/bin/env python3
"""
Script para verificar y configurar OpenModelica en el sistema.
Busca instalaciones de OpenModelica y ayuda con la configuración.
"""

import os
import sys
import subprocess
from pathlib import Path
import platform

def find_openmodelica_installations():
    """Busca todas las instalaciones posibles de OpenModelica."""
    print("🔍 Buscando instalaciones de OpenModelica...")
    
    installations = []
    
    # Ubicaciones típicas según el sistema operativo
    if platform.system() == "Windows":
        possible_paths = [
            r"C:\OpenModelica\bin\omc.exe",
            r"C:\Program Files\OpenModelica\bin\omc.exe",
            r"C:\Program Files (x86)\OpenModelica\bin\omc.exe",
        ]
        
        # Agregar ubicación desde variable de entorno si existe
        om_home = os.environ.get('OPENMODELICAHOME')
        if om_home:
            omc_path = os.path.join(om_home, 'bin', 'omc.exe')
            possible_paths.insert(0, omc_path)  # Prioridad alta
        
        # Buscar versiones específicas
        for drive in ['C:', 'D:', 'E:']:
            for version in ['1.21.0', '1.22.0', '1.23.0', '1.24.0', '1.25.0', '1.25.1']:
                possible_paths.append(f"{drive}\\OpenModelica{version}\\bin\\omc.exe")
                possible_paths.append(f"{drive}\\Program Files\\OpenModelica{version}-64bit\\bin\\omc.exe")
    else:
        possible_paths = [
            "/usr/bin/omc",
            "/usr/local/bin/omc",
            "/opt/openmodelica/bin/omc",
        ]
    
    # Verificar cada path
    for path in possible_paths:
        if os.path.isfile(path):
            try:
                result = subprocess.run([path, '--version'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    version = result.stdout.strip()
                    installations.append({
                        'path': path,
                        'version': version,
                        'working': True
                    })
                    print(f"✅ Encontrado: {path}")
                    print(f"   Versión: {version}")
                else:
                    installations.append({
                        'path': path,
                        'version': 'Error al obtener versión',
                        'working': False
                    })
                    print(f"⚠️  Encontrado pero no funcional: {path}")
            except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
                installations.append({
                    'path': path,
                    'version': f'Error: {e}',
                    'working': False
                })
                print(f"❌ Error al verificar: {path}")
    
    # Verificar si está en PATH
    try:
        result = subprocess.run(['omc', '--version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            version = result.stdout.strip()
            installations.append({
                'path': 'omc (en PATH)',
                'version': version,
                'working': True
            })
            print(f"✅ OpenModelica encontrado en PATH del sistema")
            print(f"   Versión: {version}")
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        print("❌ OpenModelica no está en el PATH del sistema")
    
    return installations

def check_environment_variables():
    """Verifica las variables de entorno relacionadas con OpenModelica."""
    print("\n🔧 Verificando variables de entorno...")
    
    env_vars = [
        'OPENMODELICAHOME',
        'OPENMODELICALIBRARY',
        'PATH'
    ]
    
    for var in env_vars:
        value = os.environ.get(var)
        if var == 'PATH':
            if value:
                # Buscar rutas que contengan OpenModelica
                om_paths = [p for p in value.split(os.pathsep) if 'openmodelica' in p.lower()]
                if om_paths:
                    print(f"✅ {var} contiene rutas de OpenModelica:")
                    for path in om_paths:
                        print(f"   - {path}")
                else:
                    print(f"⚠️  {var} no contiene rutas de OpenModelica")
            else:
                print(f"❌ {var} no está definida")
        else:
            if value:
                print(f"✅ {var} = {value}")
            else:
                print(f"❌ {var} no está definida")

def test_simple_simulation():
    """Prueba una simulación simple para verificar que todo funciona."""
    print("\n🧪 Probando simulación simple...")
    
    # Crear un modelo simple de prueba
    simple_model = """
model TestModel
  Real x(start=0);
equation
  der(x) = 1;
end TestModel;
"""
    
    # Crear archivo temporal
    with open('test_model.mo', 'w') as f:
        f.write(simple_model)
    
    # Script de simulación
    script = """
loadFile("test_model.mo");
simulate(TestModel, startTime=0, stopTime=1, numberOfIntervals=10);
"""
    
    with open('test_script.mos', 'w') as f:
        f.write(script)
    
    try:
        # Intentar ejecutar
        result = subprocess.run(['omc', 'test_script.mos'], 
                              capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ Simulación de prueba completada exitosamente")
            print("   OpenModelica está funcionando correctamente")
        else:
            print("❌ Error en simulación de prueba:")
            print(f"   {result.stderr}")
            
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
        print(f"❌ No se pudo ejecutar la simulación de prueba: {e}")
    
    finally:
        # Limpiar archivos temporales
        for file in ['test_model.mo', 'test_script.mos']:
            if os.path.exists(file):
                os.remove(file)

def provide_installation_instructions():
    """Proporciona instrucciones de instalación para OpenModelica."""
    print("\n📋 Instrucciones de instalación de OpenModelica:")
    
    if platform.system() == "Windows":
        print("""
🪟 Para Windows:
1. Descargar OpenModelica desde: https://openmodelica.org/download/
2. Ejecutar el instalador como administrador
3. Asegurarse de marcar "Add to PATH" durante la instalación
4. Reiniciar el sistema después de la instalación

🔧 Configuración manual del PATH (si es necesario):
1. Buscar "Variables de entorno" en el menú de inicio
2. Editar las variables de entorno del sistema
3. Agregar la ruta de instalación de OpenModelica al PATH
   (ejemplo: C:\\OpenModelica\\bin)
4. Reiniciar el sistema
""")
    else:
        print("""
🐧 Para Linux/Ubuntu:
sudo apt update
sudo apt install openmodelica

🍎 Para macOS:
brew install openmodelica

📦 O descargar desde: https://openmodelica.org/download/
""")

def main():
    """Función principal del script de verificación."""
    print("🚀 Verificador de OpenModelica")
    print("=" * 50)
    
    # Buscar instalaciones
    installations = find_openmodelica_installations()
    
    # Verificar variables de entorno
    check_environment_variables()
    
    # Resumen
    print("\n📊 Resumen:")
    working_installations = [inst for inst in installations if inst['working']]
    
    if working_installations:
        print(f"✅ {len(working_installations)} instalación(es) funcional(es) encontrada(s)")
        for inst in working_installations:
            print(f"   - {inst['path']}")
        
        # Probar simulación si hay al menos una instalación funcional
        if any('PATH' in inst['path'] for inst in working_installations):
            test_simple_simulation()
    else:
        print("❌ No se encontraron instalaciones funcionales de OpenModelica")
        provide_installation_instructions()
    
    print("\n🎯 Recomendaciones:")
    if not working_installations:
        print("- Instalar OpenModelica desde https://openmodelica.org/download/")
        print("- Asegurarse de agregar OpenModelica al PATH del sistema")
    elif not any('PATH' in inst['path'] for inst in working_installations):
        print("- Agregar OpenModelica al PATH del sistema para facilitar el acceso")
    else:
        print("- OpenModelica está correctamente instalado y configurado")
        print("- El sistema de simulación debería funcionar correctamente")

if __name__ == "__main__":
    main()
