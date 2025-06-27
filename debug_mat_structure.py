"""
Script para debuguear la estructura exacta de los archivos .mat de OpenModelica
"""
import os
import numpy as np
from scipy.io import loadmat
import glob

def debug_mat_file(archivo_mat):
    """Analiza completamente la estructura de un archivo .mat de OpenModelica."""
    
    print(f"\n{'='*80}")
    print(f"🔍 ANALIZANDO: {archivo_mat}")
    print(f"{'='*80}")
    
    if not os.path.exists(archivo_mat):
        print(f"❌ Archivo no encontrado: {archivo_mat}")
        return
    
    try:
        # Cargar archivo
        data = loadmat(archivo_mat)
        
        # Mostrar todas las claves
        variables = [k for k in data.keys() if not k.startswith('_')]
        print(f"📊 Variables principales: {variables}")
        
        # Analizar cada variable
        for var in variables:
            contenido = data[var]
            print(f"\n🔸 {var}:")
            print(f"   Tipo: {type(contenido)}")
            if hasattr(contenido, 'shape'):
                print(f"   Forma: {contenido.shape}")
            if hasattr(contenido, 'dtype'):
                print(f"   Dtype: {contenido.dtype}")
        
        # Decodificar nombres si están disponibles
        if 'name' in data:
            print(f"\n🏷️  DECODIFICANDO NOMBRES:")
            nombres_matriz = data['name']
            print(f"   Matriz de nombres: {nombres_matriz.shape}")
            print(f"   Tipo de datos: {nombres_matriz.dtype}")
            
            nombres = []
            for i in range(min(nombres_matriz.shape[0], 50)):  # Solo primeros 50
                try:
                    # Intentar diferentes métodos de decodificación
                    if nombres_matriz.dtype.kind == 'U':  # Unicode string
                        nombre = str(nombres_matriz[i]).strip()
                    else:
                        # Método original para matrices de caracteres
                        nombre = ''.join(chr(int(c)) for c in nombres_matriz[i] if c != 0).strip()
                    
                    if nombre and nombre != 'nan':
                        nombres.append(nombre)
                        print(f"   {i:2d}: {nombre}")
                    else:
                        nombres.append(f"Variable_{i}")
                        print(f"   {i:2d}: [Variable_{i}]")
                except Exception as e:
                    nombres.append(f"Variable_{i}")
                    print(f"   {i:2d}: [Error: {e}]")
        
        # Analizar datos temporales
        if 'data_2' in data:
            datos = data['data_2']
            print(f"\n📈 DATOS TEMPORALES (data_2):")
            print(f"   Forma: {datos.shape}")
            print(f"   Variables: {datos.shape[0]}")
            print(f"   Puntos temporales: {datos.shape[1]}")
            
            if datos.shape[0] > 0:
                print(f"\n   Estadísticas por variable:")
                for i in range(min(datos.shape[0], 20)):  # Solo primeras 20
                    valores = datos[i, :]
                    nombre = nombres[i] if i < len(nombres) else f"Variable_{i}"
                    print(f"   {i:2d}: {nombre[:30]:30s} | Min: {np.min(valores):8.3f} | Max: {np.max(valores):8.3f} | Final: {valores[-1]:8.3f}")
        
        # Buscar variables de interés específicas
        print(f"\n🎯 BUSCANDO VARIABLES DE INTERÉS:")
        variables_buscadas = ['energia', 'temperatura', 'potencia', 'costo', 'carcasa', 'interior', 'exterior']
        
        for var_buscar in variables_buscadas:
            encontradas = []
            if 'name' in data and len(nombres) > 0:
                for i, nombre in enumerate(nombres):
                    if var_buscar.lower() in nombre.lower():
                        encontradas.append((i, nombre))
            
            if encontradas:
                print(f"\n   '{var_buscar}' encontrada en:")
                for idx, nombre in encontradas:
                    if 'data_2' in data and idx < data['data_2'].shape[0]:
                        valores = data['data_2'][idx, :]
                        print(f"     {idx:2d}: {nombre} (Final: {valores[-1]:.3f})")
        
    except Exception as e:
        print(f"❌ Error analizando archivo: {e}")
        import traceback
        traceback.print_exc()

def buscar_archivos_mat():
    """Busca todos los archivos .mat en el directorio temp."""
    archivos = []
    
    # Buscar en temp/
    temp_patterns = [
        "temp/*/*.mat",
        "temp/**/*.mat", 
        "*.mat"
    ]
    
    for pattern in temp_patterns:
        archivos.extend(glob.glob(pattern))
    
    return list(set(archivos))  # Eliminar duplicados

if __name__ == "__main__":
    print("🔍 Buscando archivos .mat para analizar...")
    
    archivos_mat = buscar_archivos_mat()
    
    if not archivos_mat:
        print("❌ No se encontraron archivos .mat")
        print("💡 Ejecuta primero una simulación para generar archivos de resultados")
    else:
        print(f"📁 Encontrados {len(archivos_mat)} archivos .mat:")
        for archivo in archivos_mat:
            print(f"   • {archivo}")
        
        # Analizar cada archivo
        for archivo in archivos_mat:
            debug_mat_file(archivo)
    
    print(f"\n{'='*80}")
    print("✅ Análisis completado")
