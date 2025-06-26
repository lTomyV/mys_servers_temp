#!/usr/bin/env python3
"""
Script de prueba simple para verificar que OpenModelica funciona.
"""

import subprocess
import os
from pathlib import Path

def test_simple_modelica():
    """Prueba OpenModelica con un modelo muy simple."""
    print("🧪 PRUEBA SIMPLE DE OPENMODELICA")
    print("=" * 50)
    
    # Path de OpenModelica
    omc_path = r"C:\Program Files\OpenModelica1.25.1-64bit\bin\omc.exe"
    
    if not os.path.isfile(omc_path):
        print(f"❌ No se encontró OpenModelica en: {omc_path}")
        return False
    
    # Crear modelo simple
    simple_model = """
model TestSimple
  Real x(start=1.0);
equation
  der(x) = -x;
end TestSimple;
"""
    
    # Escribir modelo a archivo
    with open('test_simple.mo', 'w') as f:
        f.write(simple_model)
    
    # Crear script de simulación
    script = """
loadFile("test_simple.mo");
simulate(TestSimple, startTime=0, stopTime=2, numberOfIntervals=20, outputFormat="csv");
"""
    
    with open('test_simple.mos', 'w') as f:
        f.write(script)
    
    try:
        print("Ejecutando simulación simple...")
        result = subprocess.run(
            [omc_path, 'test_simple.mos'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        print(f"Código de retorno: {result.returncode}")
        print(f"Salida estándar:")
        print(result.stdout)
        
        if result.stderr:
            print(f"Errores:")
            print(result.stderr)
        
        # Verificar si se crearon archivos de resultados
        result_files = []
        for pattern in ['*_res.csv', '*_res.mat', 'TestSimple_*']:
            result_files.extend(Path('.').glob(pattern))
        
        if result_files:
            print(f"✅ Archivos de resultados encontrados:")
            for f in result_files:
                print(f"   - {f}")
                if f.suffix == '.csv':
                    try:
                        with open(f, 'r') as file:
                            lines = file.readlines()
                            print(f"     Archivo CSV con {len(lines)} líneas")
                            if len(lines) > 0:
                                print(f"     Primera línea: {lines[0].strip()}")
                    except Exception as e:
                        print(f"     Error leyendo CSV: {e}")
        else:
            print("❌ No se encontraron archivos de resultados")
            # Listar todos los archivos para debug
            all_files = list(Path('.').glob('*'))
            print("Archivos en directorio:")
            for f in all_files:
                if f.is_file():
                    print(f"   - {f.name}")
    
    except subprocess.TimeoutExpired:
        print("❌ Timeout en la simulación")
        return False
    except Exception as e:
        print(f"❌ Error ejecutando simulación: {e}")
        return False
    
    finally:
        # Limpiar archivos temporales
        cleanup_files = ['test_simple.mo', 'test_simple.mos']
        for f in cleanup_files:
            if os.path.exists(f):
                os.remove(f)
    
    return result.returncode == 0

if __name__ == "__main__":
    success = test_simple_modelica()
    if success:
        print("✅ Prueba simple exitosa")
    else:
        print("❌ Prueba simple falló")
