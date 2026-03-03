from mcp.server.fastmcp import FastMCP
import os
import glob
from datetime import datetime

mcp = FastMCP("Documents")

DOCS_FOLDER = "./documents"

@mcp.tool()
def list_txt_files() -> str:
    """
    Lista todos los archivos .txt disponibles en la carpeta documents/.
    """
    if not os.path.exists(DOCS_FOLDER):
        return f"Carpeta {DOCS_FOLDER} no existe. Créala primero."
    
    txt_files = glob.glob(os.path.join(DOCS_FOLDER, "*.txt"))
    if not txt_files:
        return f"No hay archivos .txt en {DOCS_FOLDER}"
    
    files_list = []
    for file_path in txt_files:
        filename = os.path.basename(file_path)
        size = os.path.getsize(file_path)
        files_list.append(f"- {filename} ({size} bytes)")
    
    return f"Archivos disponibles en {DOCS_FOLDER}:\n" + "\n".join(files_list)


@mcp.tool()
def read_full_txt(filename: str) -> str:
    """
    Lee el CONTENIDO COMPLETO de un archivo .txt (útil para análisis detallado).
    """
    file_path = os.path.join(DOCS_FOLDER, filename)
    
    if not os.path.exists(file_path):
        return f"❌ '{filename}' no existe en {DOCS_FOLDER}"
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            full_content = f.read()
        
        if len(full_content) > 2000:
            return f"📄 '{filename}' leído ({len(full_content)} chars):\n\n{full_content[:1900]}...\n\n[Archivo muy largo - truncado]"
        else:
            return f"📄 CONTENIDO COMPLETO '{filename}':\n\n{full_content}"
            
    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == "__main__":
    print(f"🚀 Servidor TXT resumidor iniciado. Carpeta: {DOCS_FOLDER}")
    mcp.run(transport="stdio")
