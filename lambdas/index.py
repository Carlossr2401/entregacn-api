import json, os, uuid, boto3
from botocore.exceptions import ClientError # (Mejor importar errores)

# --- Configuración Única (Compartida) ---
table_name = os.environ.get('TABLE_NAME')
if not table_name:
    raise ValueError("Error: La variable de entorno TABLE_NAME no está configurada.")
table = boto3.resource('dynamodb').Table(table_name)

# --- Función de Ayuda Única (Compartida) ---
def build_response(status_code, body):
    return {
        'statusCode': status_code,
        'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
        'body': json.dumps(body, default=str)
    }

# -----------------------------------------------
# ------ HANDLER 1: Crear Nota (POST /notas)
# -----------------------------------------------
def create_note_handler(event, context):
    try:
        body = json.loads(event.get('body', '{}'))
        if 'AlumnoNombre' not in body or 'ClaseNombre' not in body or 'Nota' not in body:
            return build_response(400, {'error': 'Faltan campos requeridos: AlumnoNombre, ClaseNombre, Nota'})
        
        item = {
            'NoteID': str(uuid.uuid4()),
            'AlumnoNombre': body['AlumnoNombre'],
            'ClaseNombre': body['ClaseNombre'],
            'Nota': body['Nota']
        }
        table.put_item(Item=item)
        return build_response(201, item)
    
    except json.JSONDecodeError:
        return build_response(400, {'error': 'El cuerpo (body) de la solicitud no es un JSON válido.'})
    except Exception as e:
        print(f"Error en create_note_handler: {e}")
        return build_response(500, {'error': 'Error interno al crear la nota'})

# -----------------------------------------------
# ------ HANDLER 2: Obtener Todas (GET /notas)
# -----------------------------------------------
def get_all_notes_handler(event, context):
    try:
        response = table.scan()
        items = response.get('Items', [])
        
        while 'LastEvaluatedKey' in response:
            response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            items.extend(response.get('Items', []))
        
        return build_response(200, items)
    
    except Exception as e:
        print(f"Error en get_all_notes_handler: {e}")
        return build_response(500, {'error': 'Error interno al obtener las notas'})

# -----------------------------------------------
# ------ HANDLER 3: Obtener por ID (GET /notas/{id})
# -----------------------------------------------
def get_note_by_id_handler(event, context):
    try:
        note_id = event.get('pathParameters', {}).get('noteId')
        if not note_id:
            return build_response(400, {'error': 'Falta el noteId'})
        
        response = table.get_item(Key={'NoteID': note_id})
        if 'Item' in response:
            return build_response(200, response['Item'])
        else:
            return build_response(404, {'error': 'Nota no encontrada'})
    
    except Exception as e:
        print(f"Error en get_note_by_id_handler: {e}")
        return build_response(500, {'error': 'Error interno al obtener la nota'})

# -----------------------------------------------
# ------ HANDLER 4: Actualizar Nota (PUT /notas/{id})
# -----------------------------------------------
def update_note_handler(event, context):
    try:
        note_id = event.get('pathParameters', {}).get('noteId')
        if not note_id:
            return build_response(400, {'error': 'Falta el noteId'})
        
        body = json.loads(event.get('body', '{}'))
        if 'Nota' not in body:
            return build_response(400, {'error': 'Falta el campo "Nota" en el body'})
        
        response = table.update_item(
            Key={'NoteID': note_id},
            UpdateExpression="SET Nota = :n",
            ExpressionAttributeValues={':n': body['Nota']},
            ReturnValues="UPDATED_NEW"
        )
        return build_response(200, response.get('Attributes', {}))
    
    except json.JSONDecodeError:
        return build_response(400, {'error': 'El cuerpo (body) de la solicitud no es un JSON válido.'})
    except Exception as e:
        print(f"Error en update_note_handler: {e}")
        return build_response(500, {'error': 'Error interno al actualizar la nota'})

# -----------------------------------------------
# ------ HANDLER 5: Borrar Nota (DELETE /notas/{id})
# -----------------------------------------------
def delete_note_handler(event, context):
    try:
        note_id = event.get('pathParameters', {}).get('noteId')
        if not note_id:
            return build_response(400, {'error': 'Falta el noteId'})
        
        table.delete_item(Key={'NoteID': note_id})
        return build_response(200, {'mensaje': 'Nota eliminada exitosamente'})
    
    except Exception as e:
        print(f"Error en delete_note_handler: {e}")
        return build_response(500, {'error': 'Error interno al eliminar la nota'})