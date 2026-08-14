from flask import Flask, request, jsonify, render_template, abort, redirect, send_from_directory
import psutil
import string
import random



app = Flask(__name__)


######################################################################################
# Configura el nombre del servidor para incluir el subdominio
app.config['SERVER_NAME'] = 'cybersec.dl'
######################################################################################


@app.before_request
def limit_access():
    if request.host != 'cybersec.dl' and request.host != '0internal_down.cybersec.dl' and request.host != 'mail.cybersec.dl':
        return redirect("http://cybersec.dl", code=302)

# Datos simulados de la empresa
company_data = {
    "name": "CyberSec Corp",
    "services": [
        "Auditorias de seguridad",
        "Pentesting",
        "Consultoria en ciberseguridad"
    ],
    "address": "New York, EEUU",
    "phone": "+1322302450134200",
    "branches": ["Brazil", "Curacao", "Lithuania", "Luxembourg", "Japan", "Finland"],
    "customers": ["ADIDAS", "COCACOLA", "PEPSICO", "Teltonika", "Toray Industries", "Weg", "CURALINk"],
    "URLs_web": ["cybersec.dl", "bin.cybersec.dl", "mail.cybersec.dl", "dev.cybersec.dl", "cybersec.dl/downloads", "internal-api.cybersec.dl", "0internal_down.cybersec.dl", "internal.cybersec.dl", "cybersec.dl/documents", "cybersec.dl/api/cpu", "cybersec.dl/api/login"]
}

# Credenciales simuladas
users = {
    "admin": "undertaker",
    "user": "user123"
}

# Información sensible
sensitive_info = {
    "admin": "http://cybersec.dl/555555555555509.txt",
    "user": "http://dashboard.cybersec.com"
}

@app.route('/')
def index():
    return render_template('index.html', data=company_data)

@app.route('/api/login', methods=['POST'])
def login():
    username = request.json.get('username')
    password = request.json.get('password')

    if username in users and users[username] == password:
        response = {
            "message": "Login successful",
            "company": {
                "name": company_data["name"],
                "services": ", ".join(company_data["services"]),
                "address": company_data["address"],
                "phone": company_data["phone"],
                "branches": ", ".join(company_data["branches"]),
                "customers": ", ".join(company_data["customers"]),
                "URLs_web": ", ".join(company_data["URLs_web"])
            }
        }
        return jsonify(response)
    else:
        return jsonify({"message": "Invalid credentials"}), 401

##################################################################
# Nueva ruta para el subdominio '0internal_down'
@app.route('/', subdomain='0internal_down')
def bin_index():
    return render_template('bin.html')  # Carga el archivo bin.html


# Nueva ruta para el subdominio 'mail'
@app.route('/', subdomain='mail')
def mail_index():
    return render_template('mail.html')  # Carga el archivo mail.html

# Descargas
@app.route('/download/<path:filename>', subdomain='0internal_down')
def download_file(filename):
    try:
        return send_from_directory('static/archivos', filename)
    except Exception as e:
        return str(e), 404
####################################################################
# api generadora de password seguras

def generar_contrasena_segura():
    caracteres = string.ascii_letters + string.digits + string.punctuation
    contrasena = ''.join(random.choice(caracteres) for i in range(24))
    return contrasena



#/api/generar_contrasena
@app.route('/api/1passwsecu0', methods=['GET'])
def generar_contrasena():
    contrasena = generar_contrasena_segura()
    return jsonify({"password": contrasena})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
