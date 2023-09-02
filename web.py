from flask import Flask, redirect, request, render_template, session
import requests
import json

# Inicialización de la aplicación Flask
app = Flask(__name__)


# Parámetros para la autenticación
CLIENT_ID = 'e6b797b3-57dd-4fc2-a7b9-a5325b704684'
REDIRECT_URI = 'http://localhost:5000/callback'
AUTH_URL = 'https://login.microsoftonline.com/04fd3bf2-9dd4-40cc-912b-9c4aed792ce9/oauth2/v2.0/authorize'
TOKEN_URL = 'https://login.microsoftonline.com/04fd3bf2-9dd4-40cc-912b-9c4aed792ce9/oauth2/v2.0/token'
SCOPE = 'api://f827577e-75f5-4639-b668-640bbb2e5d9d/data.read'
client_secret = None


# Parámetros para el reporte
params = {}
tipo_reporte_param = None

# Función para validar parámetros
def validar_parametro(texto):
    return None if texto in [None, "", " "] else texto


# Ruta principal
@app.route('/')
def index():
    return render_template('index.html')


# Ruta para iniciar sesión y redirigir para autenticación
@app.route('/login', methods=['POST'])
def login():
    global client_secret, params, tipo_reporte_param
    client_secret = validar_parametro(request.form['client_secret'])
    params = {
        'gtin': validar_parametro(request.form['gtin_param']),
        'fecha': validar_parametro(request.form['fecha_param']),
        'cod_gpi': validar_parametro(request.form['cod_gpi_param'])
    }
    tipo_reporte_param = validar_parametro(request.form['reporte_tipo'])
    authorization_url = f"{AUTH_URL}?response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&scope={SCOPE}"
    response = redirect(authorization_url)
    return response


# Ruta de devolución de llamada para la autenticación
@app.route('/callback')
def callback():
    # Obtenemos los parámetros enviados del login
    global client_secret, params, tipo_reporte_param

    # El code que obtenemos de la autenticación
    code = request.args.get('code')

    # Validamos que el client secret no sea nulo
    if not client_secret:
        return "Error: No se ha enviado el client secret"
    
    # Body del request para generar el token de acceso
    data = {
        'grant_type': 'authorization_code',
        'client_id': CLIENT_ID,
        'client_secret': client_secret,
        'code': code,
        'redirect_uri': REDIRECT_URI,
        'scope': SCOPE
    }

    # Headers del request para generar el token de acceso
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    # Realizamos la solicitud del token de acceso
    response = requests.post(TOKEN_URL, data=data, headers=headers)

    # Validamos que la solicitud haya sido exitosa
    if response.status_code != 200:
        print("Error en la solicitud del token:", response.text)
        return f"Error: {response.text}"

    # Obtenemos el token de acceso
    token_response = response.json()
    access_token = token_response['access_token']

    # Definimos la cabecera para la solicitud del reporte usando el token de acceso
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    # Definimos la URL del reporte
    if tipo_reporte_param == "12A":
        url_reporte = 'https://alterra-reportes-api.azurewebsites.net/reporte12a/'

        # En caso los parámetros sean nulos, se envía el reporte 12A Total
        if params['gtin'] == None and params['fecha'] == None and params['cod_gpi'] == None:
            return render_template('reporte12a_total.html', token_obtenido=access_token)
    
    elif tipo_reporte_param == "12E":
        url_reporte = 'https://alterra-reportes-api.azurewebsites.net/reporte12e/'

    # Realizamos la solicitud del reporte
    response = requests.post(url_reporte, headers=headers, json=params, timeout=600)
    print("URL", url_reporte, "Headers", headers, "Data", params)
    
    # Obtenemos la respuesta y la mostramos en la página
    respuesta_texto = response.text
    print("Respuesta obtenida:", respuesta_texto)
    respuesta_json = json.loads(respuesta_texto)
    return render_template('reportes.html', response=respuesta_json)


if __name__ == '__main__':
    app.run(debug=True)
