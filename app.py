from flask import Flask, render_template, jsonify, request
import sqlite3
import os
import shutil
import psutil
from datetime import datetime

app = Flask(__name__)
DB_NAME = "database.db"

# 1. Inicializar Base de Datos
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS respaldos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT,
            origen TEXT,
            destino TEXT,
            estado TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# 2. Rutas de la Aplicación
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/sistema', methods=['GET'])
def estado_sistema():
    # Obtiene información del disco principal C: o raíz
    disco = psutil.disk_usage('/')
    return jsonify({
        "total": round(disco.total / (1024**3), 2),
        "usado": round(disco.used / (1024**3), 2),
        "libre": round(disco.free / (1024**3), 2),
        "porcentaje": disco.percent
    })

@app.route('/api/respaldo', methods=['POST'])
def ejecutar_respaldo():
    data = request.json
    origen = data.get('origen')
    destino = data.get('destino')
    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if not os.path.exists(origen):
        return jsonify({"status": "error", "message": "La carpeta de origen no existe."}), 400
        
    try:
        # Simulación o copia real de la carpeta
        nombre_carpeta = os.path.basename(origen)
        destino_final = os.path.join(destino, f"Backup_{nombre_carpeta}")
        
        if os.path.exists(destino_final):
            shutil.rmtree(destino_final) # Reemplaza si ya existe
            
        shutil.copytree(origen, destino_final)
        
        # Guardar historial en la BD
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO respaldos (fecha, origen, destino, estado) VALUES (?, ?, ?, ?)",
                       (fecha_actual, origen, destino, "Exitoso"))
        conn.commit()
        conn.close()
        
        return jsonify({"status": "success", "message": "¡Respaldo completado con éxito!"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/historial', methods=['GET'])
def historial_respaldos():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT fecha, origen, destino, estado FROM respaldos ORDER BY id DESC")
    filas = cursor.fetchall()
    conn.close()
    
    historial = [{"fecha": f[0], "origen": f[1], "destino": f[2], "estado": f[3]} for f in filas]
    return jsonify(historial)

if __name__ == '__main__':
    app.run(debug=True, port=5000)