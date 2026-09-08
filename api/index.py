
import mimetypes
import os
import psycopg2
from flask import Flask, render_template
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
        return render_template('eliminar_usuario.html', mensaje=None)

    cedula = request.form['cedula']

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "CALL eliminar_usuario(%s, %s)",
        (cedula, None)
    )
    resultado = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()

    mensaje = resultado[0]

    return render_template('eliminar_usuario.html', mensaje=mensaje)




if __name__ == '__main__':
    app.run(debug=True)