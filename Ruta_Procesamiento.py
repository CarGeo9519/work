import tkinter as tk
from tkinter import filedialog
import pandas as pd
import os

def seleccionar_archivos():
    root = tk.Tk()
    root.withdraw()  # Ocultar la ventana principal
    
    archivos = filedialog.askopenfilenames(
        title="Seleccionar archivos GPKG",
        filetypes=[("GeoPackage Files", "*.gpkg")]
    )
    
    return archivos

def generar_xlsx(archivos):
    salida = os.path.join(os.getcwd(), "archivos_gpkg.xlsx")  # Guardar en el directorio actual
    
    if not archivos:
        print("No se seleccionaron archivos.")
        input("Presiona Enter para salir...")  # Mantener la consola abierta
        return
    
    datos = []
    for archivo in archivos:
        folder_path = os.path.dirname(archivo)  # Obtener solo la carpeta contenedora
        datos.append({"Nombre": os.path.basename(archivo), "Ruta": folder_path})
    
    df = pd.DataFrame(datos)
    
    try:
        with pd.ExcelWriter(salida, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Archivos')
            workbook = writer.book
            worksheet = writer.sheets['Archivos']
            
            # Convertir la columna de carpetas en hipervínculos
            for row_num in range(1, len(df) + 1):
                worksheet.write_url(row_num, 1, f'file:///{df.at[row_num - 1, "Ruta"]}')
            
            writer.close()  # Asegurar el cierre del archivo
        
        print(f"XLSX generado exitosamente en: {salida}")
    except Exception as e:
        print(f"Error al generar el archivo XLSX: {e}")
    
    input("Presiona Enter para salir...")  # Mantener la consola abierta

if __name__ == "__main__":
    archivos_seleccionados = seleccionar_archivos()
    generar_xlsx(archivos_seleccionados)
