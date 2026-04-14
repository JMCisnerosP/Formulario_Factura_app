from flask import Flask, render_template, request
import os
import csv
from datetime import datetime
from werkzeug.utils import secure_filename
from flask_mail import Mail, Message

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Crear la carpeta de subida si no existe
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Configuración de correo (usa variables de entorno en Render o local)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')  # ejemplo: admonbribiesca@gmail.com
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')  # tu App Password de Gmail
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_USERNAME')

mail = Mail(app)

@app.route('/')
def formulario():
    return render_template('formulario.html')

@app.route('/enviar', methods=['POST'])
def enviar():
     print("➡️ Entrando a la ruta /enviar")
    forma_pago, metodo_pago = request.form['forma_pago'].split('|')
    
    datos = {
        'nombre': request.form['nombre'],
        'rfc': request.form['rfc'],
        'correo': request.form['correo'],
        'codigo_postal': request.form['codigo_postal'],
        'telefono': request.form['telefono'],
        'regimen_fiscal': request.form['regimen_fiscal'],
        'ticket': request.form['ticket'],
        'uso_cfdi': request.form['uso_cfdi'],
        'monto': request.form['monto'],
        'forma_pago': forma_pago,
        'metodo_pago': metodo_pago
    }
 print("✅ Datos recibidos:", datos)
    archivo = request.files['constancia']
    ruta_archivo = None  # inicializamos para evitar NameError

    if archivo and archivo.filename != '':
        filename = secure_filename(archivo.filename)
        ruta_archivo = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        archivo.save(ruta_archivo)
        datos['archivo'] = filename
        print("📂 Archivo guardado en:", ruta_archivo)
    else:
        datos['archivo'] = ''
        print("⚠️ No se subió archivo")

    # Guardar en CSV
    csv_file = os.path.join(app.config['UPLOAD_FOLDER'], 'solicitudes_factura.csv')
    headers = [
        'Nombre', 'RFC', 'Correo Electrónico', 'Código Postal', 'Teléfono',
        'Régimen Fiscal', 'Número de Ticket', 'Uso CFDI', 'Monto',
        'Forma de Pago', 'Método de Pago', 'Fecha de Solicitud', 'Archivo Subido'
    ]
    
    if not os.path.exists(csv_file):
        with open(csv_file, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(headers)
        print("📝 CSV creado con headers")

    with open(csv_file, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([
            datos['nombre'],
            datos['rfc'],
            datos['correo'],
            datos['codigo_postal'],
            datos['telefono'],
            datos['regimen_fiscal'],
            datos['ticket'],
            datos['uso_cfdi'],
            datos['monto'],
            datos['forma_pago'],
            datos['metodo_pago'],
            datetime.now().strftime('%Y-%m-%d'),
            datos['archivo']
        ])
    print("📝 Datos agregados al CSV")

    # Enviar correo con los datos
    print("📧 Preparando correo...")
    msg = Message(
    "Nueva Solicitud de Factura",
    sender=app.config['MAIL_USERNAME'],
    recipients=["admonbribiesca@gmail.com"]
    )
    msg.body = f"""
    Se recibió una nueva solicitud de factura:

    Nombre: {datos['nombre']}
    RFC: {datos['rfc']}
    Correo: {datos['correo']}
    Código Postal: {datos['codigo_postal']}
    Teléfono: {datos['telefono']}
    Régimen Fiscal: {datos['regimen_fiscal']}
    Ticket: {datos['ticket']}
    Uso CFDI: {datos['uso_cfdi']}
    Monto: {datos['monto']}
    Forma de Pago: {datos['forma_pago']}
    Método de Pago: {datos['metodo_pago']}
    Archivo: {datos['archivo']}
    """

    # Adjuntar archivo si existe
    if ruta_archivo:
        print("📎 Adjuntando archivo al correo")
        with open(ruta_archivo, 'rb') as f:
            msg.attach(
                datos['archivo'],
                "application/octet-stream",  # o "application/pdf" si siempre es PDF
                f.read()
            )

    print("🚀 Enviando correo...")
    mail.send(msg)
    print("✅ Correo enviado")

    return render_template('confirmacion.html', datos=datos, monto=datos['monto'])


