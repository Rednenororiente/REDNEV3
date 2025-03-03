# -*- coding: utf-8 -*-
"""Untitled6.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1KCobKnhKoFWIp1bRrtY2ZBTA83Qr-XXP
"""

from flask import Flask, request, send_file, jsonify
from obspy import read
import requests
import io
import datetime
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
from flask_cors import CORS
import numpy as np
from obspy.imaging.spectrogram import spectrogram

app = Flask(__name__)
CORS(app)

# Función auxiliar para calcular la diferencia de tiempo
def calculate_time_difference(start, end):
    start_time = datetime.datetime.fromisoformat(start)
    end_time = datetime.datetime.fromisoformat(end)
    return (end_time - start_time).total_seconds() / 60

# Ruta principal para manejar gráficos dinámicamente
@app.route('/generate_graph', methods=['GET'])
def generate_graph():
    try:
        start = request.args.get('start')
        end = request.args.get('end')
        net = request.args.get('net')
        sta = request.args.get('sta')
        loc = request.args.get('loc')
        cha = request.args.get('cha')

        if not all([start, end, net, sta, loc, cha]):
            return jsonify({"error": "Faltan parámetros requeridos"}), 400

        interval_minutes = calculate_time_difference(start, end)
        if interval_minutes <= 30:
            return generate_sismograma(net, sta, loc, cha, start, end)
        else:
            return generate_helicorder(net, sta, loc, cha, start, end)

    except Exception as e:
        return jsonify({"error": f"Ocurrió un error: {str(e)}"}), 500

# Ruta para generar específicamente sismogramas (y espectrogramas)
@app.route('/generate_sismograma', methods=['GET'])
def generate_sismograma_route():
    try:
        start = request.args.get('start')
        end = request.args.get('end')
        net = request.args.get('net')
        sta = request.args.get('sta')
        loc = request.args.get('loc')
        cha = request.args.get('cha')

        if not all([start, end, net, sta, loc, cha]):
            return jsonify({"error": "Faltan parámetros requeridos"}), 400

        return generate_sismograma(net, sta, loc, cha, start, end)

    except Exception as e:
        return jsonify({"error": f"Ocurrió un error: {str(e)}"}), 500

# Ruta para generar específicamente helicorders
@app.route('/generate_helicorder', methods=['GET'])
def generate_helicorder_route():
    try:
        start = request.args.get('start')
        end = request.args.get('end')
        net = request.args.get('net')
        sta = request.args.get('sta')
        loc = request.args.get('loc')
        cha = request.args.get('cha')

        if not all([start, end, net, sta, loc, cha]):
            return jsonify({"error": "Faltan parámetros requeridos"}), 400

        return generate_helicorder(net, sta, loc, cha, start, end)

    except Exception as e:
        return jsonify({"error": f"Ocurrió un error: {str(e)}"}), 500

# Función para generar sismograma y espectrograma 
def generate_sismograma(net, sta, loc, cha, start, end):
    try:
        # Construir la URL para descargar datos
        url = f"http://osso.univalle.edu.co/fdsnws/dataselect/1/query?starttime={start}&endtime={end}&network={net}&station={sta}&location={loc}&channel={cha}&nodata=404"
        
        # Realizar la solicitud al servidor remoto
        response = requests.get(url)
        if response.status_code != 200:
            return jsonify({"error": f"Error al descargar datos: {response.status_code}"}), 500

        # Procesar los datos MiniSEED
        mini_seed_data = io.BytesIO(response.content)
        try:
            st = read(mini_seed_data)
        except Exception as e:
            return jsonify({"error": f"Error procesando MiniSEED: {str(e)}"}), 500

        # Crear gráfico del sismograma
        tr = st[0]
        start_time = tr.stats.starttime.datetime
        times = [start_time + datetime.timedelta(seconds=sec) for sec in tr.times()]
        data = tr.data

        # Crear la figura con espacios 
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
        
        #Ajustar el espacio entre los subgráficos
        plt.subplots_adjust(hspace=0.4)  # Aumenta el espacio 

        # Sismograma (Gráfico superior)
        ax1.plot(times, data, color='black', linewidth=0.8)
        ax1.set_title(f"Universidad Industrial de Santander UIS\nRed Sísmica REDNE\n{start} - {end}")
        ax1.set_ylabel("Amplitud (M/s)")
        ax1.grid(True)
        ax1.text(0.02, 0.98, f"{net}.{sta}.{loc}.{cha}", transform=ax1.transAxes, fontsize=10, verticalalignment='top', bbox=dict(facecolor='white', edgecolor='black'))

        # Espectro (Gráfico inferior)
        # Calculamos el espectrograma
        nfft = 128  # Número de puntos para FFT
        fs = tr.stats.sampling_rate  # Frecuencia de muestreo
        specgram, freqs, times_spec = plt.specgram(data, NFFT=nfft, Fs=fs, noverlap=nfft//2)
        
        # Usamos un mapa de colores secuenciales de ObsPy
        ax2.pcolormesh(times_spec, freqs, 10 * np.log10(specgram), cmap=obspy_sequential, shading='auto')
        ax2.set_xlabel("Tiempo (UTC Colombia)")
        ax2.set_ylabel("Frecuencia (Hz)")
        ax2.set_title("Espectrograma")
        fig.colorbar(ax2.pcolormesh(times_spec, freqs, 10 * np.log10(specgram), cmap=obspy_sequential, shading='auto'), ax=ax2, label='Potencia (dB)')

        # Mejorar presentación
        fig.tight_layout()

        # Guardar el gráfico en memoria
        output_image = io.BytesIO()
        plt.savefig(output_image, format='png', dpi=100, bbox_inches="tight")
        output_image.seek(0)
        plt.close(fig)

        return send_file(output_image, mimetype='image/png')

    except Exception as e:
        return jsonify({"error": f"Ocurrió un error: {str(e)}"}), 500

# Rutas para generar el gráfico
@app.route('/generate_sismograma', methods=['GET'])
def generate_sismograma_route():
    try:
        # Extraer parámetros de la solicitud
        start = request.args.get('start')
        end = request.args.get('end')
        net = request.args.get('net')
        sta = request.args.get('sta')
        loc = request.args.get('loc')
        cha = request.args.get('cha')

        # Validar los parámetros
        if not all([start, end, net, sta, loc, cha]):
            return jsonify({"error": "Faltan parámetros requeridos"}), 400

        # Llamar a la función de generación de sismogramas
        return generate_sismograma(net, sta, loc, cha, start, end)

    except Exception as e:
        return jsonify({"error": f"Ocurrió un error: {str(e)}"}), 500


# Función para generar un helicorder
def generate_helicorder(net, sta, loc, cha, start, end):
    try:
        url = f"http://osso.univalle.edu.co/fdsnws/dataselect/1/query?starttime={start}&endtime={end}&network={net}&station={sta}&location={loc}&channel={cha}&nodata=404"
        response = requests.get(url)
        if response.status_code != 200:
            return jsonify({"error": f"Error al descargar datos: {response.status_code}"}), 500

        mini_seed_data = io.BytesIO(response.content)
        try:
            st = read(mini_seed_data)
        except Exception as e:
            return jsonify({"error": f"Error procesando MiniSEED: {str(e)}"}), 500

        fig = st.plot(
            type="dayplot",
            interval=15,
            right_vertical_labels=True,
            vertical_scaling_range=2000,
            color=['k', 'r', 'b'],
            show_y_UTC_label=True,
            one_tick_per_line=True
        )

        fig.set_size_inches(12, 4)

        output_image = io.BytesIO()
        fig.savefig(output_image, format='png', dpi=120, bbox_inches="tight")
        output_image.seek(0)
        plt.close(fig)

        return send_file(output_image, mimetype='image/png')

    except Exception as e:
        return jsonify({"error": f"Ocurrió un error: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
