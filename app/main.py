import os
import json
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS # No es necesario, la API Gateway de Fargate (HTTP API) maneja el CORS
from pydantic import ValidationError
from datetime import datetime
import uuid
from models.grades import GradeModel, UpdateGradeModel, GradeCreateModel

# justo después de crear tu app
app = Flask(__name__)
CORS(app) # No es necesario con la plantilla de Fargate que usa HTTP API y CorsConfiguration

# --- 1️⃣ Configuración de conexión a la base de datos ---
# ¡Esto ya está correcto! Lee las variables de entorno de CloudFormation.
db_username = os.environ.get("DB_USERNAME", "admin")
db_password = os.environ.get("DB_PASSWORD", "admin123")
db_host = os.environ.get("DB_HOST", "localhost")
db_port = os.environ.get("DB_PORT", "5432")
db_name = os.environ.get("DB_NAME", "appdb")

# Construir URI de conexión a PostgreSQL
DB_URI = f"postgresql+psycopg2://{db_username}:{db_password}@{db_host}:{db_port}/{db_name}"

if os.environ.get("USE_SQLITE", "false").lower() == "true":
    DB_URI = "sqlite:///test.db"

app.config["SQLALCHEMY_DATABASE_URI"] = DB_URI
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# --- 2️⃣ Inicialización de SQLAlchemy ---
db = SQLAlchemy(app)
db_initialized = False

# --- 3️⃣ Modelo de base de datos (MODIFICADO) ---
# He cambiado los nombres de las columnas para que coincidan con tu frontend
# (Alumno -> AlumnoNombre, Clase -> ClaseNombre, id -> noteId)
class GradeDB(db.Model):
    __tablename__ = "notas" # Cambiado de 'grades' a 'notas'

    # Clave primaria cambiada a 'noteId' para coincidir con las rutas
    noteId = db.Column(db.Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    ClaseNombre = db.Column(db.String(100), nullable=False) # Cambiado de 'Clase'
    AlumnoNombre = db.Column(db.String(100), nullable=False) # Cambiado de 'Alumno'
    Nota = db.Column(db.Integer, nullable=False) # Esto ya estaba bien
    
    # Estos campos están bien
    Fecha = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<GradeDB {self.AlumnoNombre} - {self.ClaseNombre}>"

# --- 4️⃣ Manejador de errores de Pydantic ---
@app.errorhandler(ValidationError)
def handle_validation_error(e):
    return jsonify({"errors": e.errors()}), 400

# --- 5️⃣ Endpoints (MODIFICADOS) ---

# Esta ruta '/health' es vital para el 'HealthCheckPath' de tu TargetGroup en el YAML
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"message": "Correcto"}), 200

# Ruta cambiada de '/grades' a '/notas'
@app.route('/notas', methods=['GET', 'POST'])
def handle_notas(): # Nombre de función cambiado
    if request.method == 'POST':
        data = request.get_json()
        try:
            # Asumimos que tu 'GradeCreateModel' ya usa 'AlumnoNombre' y 'ClaseNombre'
            validated_data = GradeCreateModel.model_validate(data)
        except ValidationError as e:
            return jsonify({"errors": e.errors()}), 400

        data_dict = validated_data.model_dump()
        if 'Fecha' in data_dict and data_dict['Fecha']:
            data_dict['Fecha'] = datetime.fromisoformat(data_dict['Fecha'])

        # Esto ahora funciona porque el modelo GradeDB coincide con los nombres
        new_grade_db = GradeDB(**data_dict) 
        try:
            db.session.add(new_grade_db)
            db.session.commit()
            # Asumimos que 'GradeModel' también usa los nombres correctos
            response_model = GradeModel.model_validate(new_grade_db) 
            return jsonify(response_model.model_dump()), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": "Error al guardar en la base de datos", "details": str(e)}), 500
    else:
        # GET (Obtener todos)
        all_grades_db = db.session.execute(db.select(GradeDB)).scalars().all()
        response_list = [GradeModel.model_validate(grade).model_dump() for grade in all_grades_db]
        return jsonify(response_list), 200

# Ruta cambiada de '/grades/<uuid:grade_id>' a '/notas/<uuid:noteId>'
@app.route('/notas/<uuid:noteId>', methods=['GET', 'PUT', 'DELETE'])
def handle_note_by_id(noteId): # Argumento cambiado a 'noteId'
    
    # Lógica de búsqueda cambiada para usar 'noteId'
    grade_db = db.session.get(GradeDB, noteId) 
    if not grade_db:
        return jsonify({"error": f"Elemento con ID {noteId} no encontrado."}), 404

    if request.method == 'GET':
        response_model = GradeModel.model_validate(grade_db)
        return jsonify(response_model.model_dump()), 200

    elif request.method == 'PUT':
        data = request.get_json()
        try:
            # Asumimos que 'UpdateGradeModel' usa los nombres correctos
            update_data = UpdateGradeModel.model_validate(data) 
        except ValidationError as e:
            return jsonify({"errors": e.errors()}), 400

        update_dict = update_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            if key == 'Fecha' and value is not None:
                value = datetime.fromisoformat(value)
            setattr(grade_db, key, value)

        try:
            db.session.commit()
            response_model = GradeModel.model_validate(grade_db)
            return jsonify(response_model.model_dump()), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": "Error al actualizar la base de datos", "details": str(e)}), 500

    elif request.method == 'DELETE':
        try:
            db.session.delete(grade_db)
            db.session.commit()
            return jsonify({"mensaje": f"Elemento con ID {noteId} eliminado."}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": "Error al eliminar de la base de datos", "details": str(e)}), 500

# --- 6️⃣ Inicialización de la base de datos ---
from sqlalchemy.exc import OperationalError

@app.before_request
def create_tables_once():
    """
    Se ejecuta ANTES de cada petición.
    Usa una bandera global para intentar crear las tablas solo una vez.
    """
    global db_initialized
    if not db_initialized:
        try:
            with app.app_context():
                db.create_all() # Crea la tabla 'notas' si no existe
            
            db_initialized = True 
            print("--- Tablas de BD creadas/verificadas ---", flush=True)
        
        except OperationalError as e:
            print(f"--- Falla al crear tablas (se reintentará en la prox. req): {e} ---", flush=True)
        
        except Exception as e:
            print(f"--- Error inesperado al crear tablas: {e} ---", flush=True)


# --- 7️⃣ Ejecutar la app ---
if __name__ == '__main__':
    # El puerto 5000 coincide con el 'ContainerPort' de tu YAML
    app.run(host='0.0.0.0', port=5000)