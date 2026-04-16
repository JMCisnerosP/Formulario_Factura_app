from flask import Flask, render_template, request, redirect, url_for, session
import os
import csv
from datetime import datetime
from werkzeug.utils import secure_filename
from flask_mail import Mail, Message

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "clave-segura")  # Necesario para sesiones

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Configuración de SendGrid (SMTP)
app.config['MAIL_SERVER'] = 'smtp.sendgrid.net'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'apikey'  # literal, no tu correo
app.config['MAIL_PASSWORD'] = os.environ.get('SENDGRID_API_KEY')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('SENDGRID_SENDER')

mail = Mail(app)

@app.route('/')
def formulario():
    return render_template('formulario.html')

@app.route('/enviar', methods=['POST'])
def enviar():
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
        'metodo_pago': metodo_pago,
        'archivo': ''
    }

    archivo = request.files.get('constancia')
    ruta_archivo = None
    if archivo and archivo.filename.strip() != '':
        filename = secure_filename(archivo.filename)
        ruta_archivo = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        archivo.save(ruta_archivo)
        datos['archivo'] = filename

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

    with open(csv_file, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([
            datos['nombre'], datos['rfc'], datos['correo'], datos['codigo_postal'],
            datos['telefono'], datos['regimen_fiscal'], datos['ticket'],
            datos['uso_cfdi'], datos['monto'], datos['forma_pago'],
            datos['metodo_pago'], datetime.now().strftime('%Y-%m-%d'),
            datos['archivo']
        ])

    # Enviar correo con SendGrid
    try:
        msg = Message(
            "Nueva Solicitud de Factura",
            sender=app.config['MAIL_DEFAULT_SENDER'],
            recipients=[app.config['MAIL_DEFAULT_SENDER']]
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
        if ruta_archivo:
            with open(ruta_archivo, 'rb') as f:
                msg.attach(datos['archivo'], "application/pdf", f.read())
        mail.send(msg)
    except Exception as e:
        print("❌ Error al enviar correo con SendGrid:", str(e))
        return f"Error al enviar correo con SendGrid: {str(e)}"

    # Guardar estado en sesión y redirigir
    session['form_enviado'] = True
    session['datos'] = datos
    return redirect(url_for('confirmacion'))

@app.route('/confirmacion')
def confirmacion():
    if not session.get('form_enviado'):
        return redirect(url_for('formulario'))
    return render_template('confirmacion.html', datos=session.get('datos'))

@app.route('/nuevo', endpoint='nuevo_formulario')
def nuevo():
    session.clear()
    return redirect(url_for('formulario'))
