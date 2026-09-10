
import mimetypes
import os
import psycopg2
from flask import Flask, jsonify, render_template
from flask import request, redirect, url_for
from dotenv import load_dotenv 
load_dotenv()
mimetypes.add_type('text/css' , '.css')
app = Flask(__name__, template_folder='../templates', static_folder='../static')


def get_connection():
    """
    Abre una conexión nueva a Postgres usando la variable de entorno
    que Vercel/Neon generan automáticamente.
    """
    database_url = os.environ.get('DATABASE_URL')
    conn = psycopg2.connect(database_url)
    return conn


@app.route('/')
def home():
    return render_template('index.html')

@app.route('/usuarios/crear', methods=['GET', 'POST'])
def crear_usuario():
    if request.method == 'GET':
        return render_template('crear_usuario.html')

    # POST: el formulario fue enviado
    cedula = request.form['cedula']
    nombre = request.form['nombre']
    email = request.form['email']
    edad = request.form['edad']

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM crear_usuario(%s, %s, %s, %s)",
        (cedula, nombre, email, edad)
    )
    resultado = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()

    mensaje = resultado[1]  # la columna resultado_mensaje

    return render_template('crear_usuario.html', mensaje=mensaje)


@app.route('/usuarios')
def listar_usuarios():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM listar_usuarios()")
    usuarios = cur.fetchall()
    cur.close()
    conn.close()

    return render_template('listar_usuarios.html', usuarios=usuarios)

@app.route('/usuarios/buscar', methods=['GET', 'POST'])
def buscar_usuario():
    if request.method == 'GET':
        return render_template('buscar_usuario.html', usuario=None, buscado=False)

    cedula = request.form['cedula']

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM obtener_usuario_por_id(%s)", (cedula,))
    usuario = cur.fetchone()
    cur.close()
    conn.close()

    return render_template('buscar_usuario.html', usuario=usuario, buscado=True)

@app.route('/usuarios/actualizar', methods=['GET', 'POST'])
def actualizar_usuario():
    if request.method == 'GET':
        return render_template('actualizar_usuario.html', mensaje=None)

    cedula = request.form['cedula']
    nombre = request.form['nombre']
    email = request.form['email']
    edad = request.form['edad']

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "CALL actualizar_usuario(%s, %s, %s, %s, %s)",
        (cedula, nombre, email, edad, None)
    )
    resultado = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()

    mensaje = resultado[0]  # el parámetro INOUT p_mensaje que vuelve

    return render_template('actualizar_usuario.html', mensaje=mensaje)


@app.route('/usuarios/eliminar', methods=['GET', 'POST'])
def eliminar_usuario():
    if request.method == 'GET':
        return render_template('eliminar_usuario.html', mensaje=None, usuario=None)

    accion = request.form.get('accion')
    cedula = request.form['cedula']

    conn = get_connection()
    cur = conn.cursor()

    if accion == 'buscar':
        # 1. Buscar la info del usuario ANTES de eliminar
        try:
            cur.execute("SELECT * FROM usuarios WHERE cedula = %s", (cedula,))
            fila = cur.fetchone()

            if not fila:
                return render_template('eliminar_usuario.html', mensaje="No se encontró ningún usuario con esa cédula.", usuario=None, cedula=cedula)

            # Convertir la fila en un diccionario {columna: valor} ANTES de cerrar el cursor
            columnas = [desc[0] for desc in cur.description]
            usuario = dict(zip(columnas, fila))

            return render_template('eliminar_usuario.html', mensaje=None, usuario=usuario, cedula=cedula)

        except Exception as e:
            conn.rollback()
            return render_template('eliminar_usuario.html', mensaje=f"Ocurrió un error al buscar el usuario: {e}", usuario=None, cedula=cedula)

        finally:
            cur.close()
            conn.close()

    elif accion == 'confirmar':
        # 2. Ejecutar la eliminación real
        try:
            cur.execute("CALL eliminar_usuario(%s, %s)", (cedula, None))
            resultado = cur.fetchone()
            conn.commit()
            mensaje = resultado[0]
        except Exception as e:
            conn.rollback()
            mensaje = f"Ocurrió un error al eliminar el usuario: {e}"
        finally:
            cur.close()
            conn.close()

        return render_template('eliminar_usuario.html', mensaje=mensaje, usuario=None)

    cur.close()
    conn.close()
    return render_template('eliminar_usuario.html', mensaje="Acción no válida.", usuario=None)

@app.route('/api/usuario/<cedula>')
def api_usuario(cedula):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT nombre, email, edad FROM usuarios WHERE cedula = %s",
        (cedula,)
    )
    usuario = cur.fetchone()
    cur.close()
    conn.close()

    if usuario is None:
        return jsonify({'error': 'no encontrado'}), 404

    return jsonify({
        'nombre': usuario[0],
        'email': usuario[1],
        'edad': usuario[2]
    })




if __name__ == '__main__':
    app.run(debug=True)