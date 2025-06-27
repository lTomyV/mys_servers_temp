"""
Script para probar extracción de datos con simulación corta.
"""
import os
import sys
import subprocess
import shutil

# Agregar el directorio raíz al path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def test_short_simulation():
    """Ejecuta una simulación de 1 hora para probar la extracción de datos."""
    
    # Crear directorio temporal
    temp_dir = "temp/test_extraction"
    os.makedirs(temp_dir, exist_ok=True)
    
    # Guardar directorio actual
    original_dir = os.getcwd()
    
    try:
        # Cambiar al directorio temporal
        os.chdir(temp_dir)
        
        # Copiar archivo .mo
        shutil.copy2(os.path.join(original_dir, "AnalisisServidores.mo"), ".")
        
        # Crear script para 1 hora (3600 segundos)
        mos_script_content = """
        loadFile("AnalisisServidores.mo");
        setCommandLineOptions("-d=newInst");
        simulate(
            AnalisisServidores.Modelos.SimulacionAdaptativa,
            startTime=0,
            stopTime=3600,
            numberOfIntervals=72,
            method="dassl",
            tolerance=1e-6,
            fileNamePrefix="test_extraction"
        );
        quit();
        """
        
        # Escribir script
        with open("test_extract.mos", "w") as f:
            f.write(mos_script_content)
        
        # Ejecutar OpenModelica
        omc_path = r"C:\Program Files\OpenModelica1.25.1-64bit\bin\omc.exe"
        print("🚀 Ejecutando simulación de 1 hora para probar extracción...")
        
        process = subprocess.run([omc_path, "test_extract.mos"], 
                                capture_output=True, 
                                text=True, 
                                timeout=120)  # 2 minutos timeout
        
        if process.returncode != 0:
            print(f"❌ Error en simulación: {process.stderr}")
            return False
        
        # Probar extracción de datos
        mat_file = "test_extraction_res.mat"
        if os.path.exists(mat_file):
            print(f"✅ Archivo generado: {mat_file}")
            
            # Importar funciones de extracción
            sys.path.append(original_dir)
            from src.simulation.runner import extract_final_energy_from_results, extract_temperatures_from_results
            
            # Probar extracción de energía
            energia = extract_final_energy_from_results(mat_file)
            if energia is not None:
                print(f"✅ Energía extraída: {energia:.2f} Wh")
            else:
                print("❌ No se pudo extraer energía")
            
            # Probar extracción de temperaturas
            temps = extract_temperatures_from_results(mat_file)
            if temps is not None:
                print(f"✅ Temperaturas extraídas: {len(temps)} puntos, rango {temps.min():.1f}-{temps.max():.1f}°C")
            else:
                print("❌ No se pudo extraer temperaturas")
            
            return energia is not None and temps is not None
        else:
            print(f"❌ No se encontró archivo de resultados")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    finally:
        # Volver al directorio original
        os.chdir(original_dir)

if __name__ == "__main__":
    success = test_short_simulation()
    if success:
        print("\n✅ Extracción de datos funciona correctamente")
    else:
        print("\n❌ Problemas con la extracción de datos")
