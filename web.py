from flask import Flask, redirect, request, render_template_string
import requests
import json
from flask import jsonify

app = Flask(__name__)

# Configura tus credenciales aquí
CLIENT_ID = 'e6b797b3-57dd-4fc2-a7b9-a5325b704684'
REDIRECT_URI = 'http://localhost:5000/callback'
AUTH_URL = 'https://login.microsoftonline.com/04fd3bf2-9dd4-40cc-912b-9c4aed792ce9/oauth2/v2.0/authorize'
TOKEN_URL = 'https://login.microsoftonline.com/04fd3bf2-9dd4-40cc-912b-9c4aed792ce9/oauth2/v2.0/token'

client_secret = None
gtin_param = None
fecha_param = None
cod_gpi_param = None
pagina_param = None
tipo_reporte_param = None


def validar_parametro(texto):
    if texto == None or texto == "" or texto == " ":
        return None
    else:
        return texto


@app.route('/')
def index():
    return render_template_string('''
    <title>Reportes Alterra</title>
    <form action="/login" method="post">
        REPORTE: <select name="reporte_tipo">
            <option value="12A">Reporte 12A</option>
            <option value="12E">Reporte 12E</option>
        </select>
        GTIN: <input type="text" name="gtin_param">
        Fecha: <input type="text" name="fecha_param">
        GPI: <input type="text" name="cod_gpi_param">
        Página: <input type="text" name="pagina_param">
        Client Secret: <input type="text" name="client_secret">
        <input type="submit" value="Ingresar">
    </form>
    ''')

@app.route('/login', methods=['POST'])
def login():
    global client_secret 
    client_secret = request.form['client_secret']
    global gtin_param
    gtin_param = validar_parametro(request.form['gtin_param'])
    global fecha_param
    fecha_param = validar_parametro(request.form['fecha_param'])
    global cod_gpi_param
    cod_gpi_param = validar_parametro(request.form['cod_gpi_param'])
    global pagina_param
    pagina_param = validar_parametro(request.form['pagina_param'])
    global tipo_reporte_param
    tipo_reporte_param = validar_parametro(request.form['reporte_tipo'])

    authorization_url = f"{AUTH_URL}?response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&scope=api://f827577e-75f5-4639-b668-640bbb2e5d9d/.default"
    response = redirect(authorization_url)
    return response

@app.route('/callback')
def callback():
    code = request.args.get('code')

    print("Client secret obtenido:", client_secret)
    if client_secret == None or client_secret == "" or client_secret == " ":
        return "Error: No se ha enviado el client secret"
    data = {
        'grant_type': 'authorization_code',
        'client_id': CLIENT_ID,
        'client_secret': client_secret,
        'code': code,
        'redirect_uri': REDIRECT_URI,
        'scope': 'api://f827577e-75f5-4639-b668-640bbb2e5d9d/.default'
    }

    # print("Data enviada:", data)

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    response = requests.post(TOKEN_URL, data=data, headers=headers)
    # print("Cuerpo de la solicitud:", response.request.body) # Imprimir el cuerpo de la solicitud
    # print("Headers de la solicitud:", response.request.headers) # Imprimir los encabezados de la solicitud
    # print("Cuerpo de la respuesta:", response.text) # Imprimir el cuerpo de la respuesta

    if response.status_code != 200:
        print("Error en la solicitud del token:", response.text)
        return f"Error: {response.text}"

    token_response = response.json()
    access_token = token_response['access_token']

    # Ahora puedes usar el token de acceso para hacer una solicitud autorizada
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    print(gtin_param, fecha_param, cod_gpi_param)
    data = {
        "gtin": gtin_param,# "3582185728896",
        "fecha": fecha_param,
        "cod_gpi": cod_gpi_param,
        "pagina": pagina_param
    }
    if tipo_reporte_param == "12A":
        url_reporte = 'https://reportes-ads.azurewebsites.net/reportes/reporte12a'
    elif tipo_reporte_param == "12E":
        url_reporte = 'https://reportes-ads.azurewebsites.net/reportes/reporte12e'
    response = requests.post(url_reporte, headers=headers, json=data, timeout=600)
    respuesta_texto = response.text
    respuesta_json = json.loads(respuesta_texto)
    respuesta_html = render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Reportes Alterra</title>
    </head>
    <body>
        <h2>Respuesta:</h2>
        {% if response['Error'] %}
            <p>{{ response['Error'] }}</p>
        {% else %}
            {% for item in response %}
                <p>{{ item }}</p>
                <hr>
            {% endfor %}
        {% endif %}
    </body>
    </html>
    ''', response=respuesta_json)
    # print(respuesta_json)
    return respuesta_html


if __name__ == '__main__':
    app.run(debug=True)