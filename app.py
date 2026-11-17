
from flask import Flask, render_template
import pandas as pd

from analisis import obtener_analisis
from graficos import crear_grafico


# ==========================================
# CONFIGURACION DEL SISTEMA PROSIP
# ==========================================

app = Flask(__name__)


# ==========================================
# PAGINA PRINCIPAL DEL DASHBOARD
# ==========================================

@app.route("/")
def dashboard():

    try:

        # 1. Obtener datos y resultados del analisis
        resultado = obtener_analisis()

        # 2. Convertir los resultados en tablas
        tabla_proyectos = pd.DataFrame(
            resultado["proyectos"],
            columns=["Proyecto", "Cantidad"]
        )

        tabla_centros = pd.DataFrame(
            resultado["importes_centro"],
            columns=["Centro de costo", "Importe total"]
        )

        tabla_solicitantes = pd.DataFrame(
            resultado["solicitantes"],
            columns=["Solicitante", "Cantidad"]
        )

        tabla_meses = pd.DataFrame(
            resultado["meses"],
            columns=["Mes", "Cantidad"]
        )

        # 3. Crear los graficos
        grafico_proyectos = crear_grafico(
            tabla_proyectos,
            "Proyecto",
            "Cantidad",
            "Declaraciones por proyecto"
        )

        grafico_centros = crear_grafico(
            tabla_centros,
            "Centro de costo",
            "Importe total",
            "Importes por centro de costo",
            horizontal=True
        )

        grafico_solicitantes = crear_grafico(
            tabla_solicitantes,
            "Solicitante",
            "Cantidad",
            "Declaraciones por solicitante"
        )

        grafico_meses = crear_grafico(
            tabla_meses,
            "Mes",
            "Cantidad",
            "Resumen financiero en soles(S/)",
            tipo="bar"
        )

        # 4. Enviar los datos al HTML
        return render_template(
            "dashboard.html",

            total_registros=resultado["total_registros"],

            total_importe=resultado["total_importe"],

            proyectos=resultado["proyectos"],

            centros=resultado["centros"],

            importes_centro=resultado["importes_centro"],

            solicitantes=resultado["solicitantes"],

            meses=resultado["meses"],

            grafico_proyectos=grafico_proyectos,

            grafico_centros=grafico_centros,

            grafico_solicitantes=grafico_solicitantes,

            grafico_meses=grafico_meses,

            error=None
        )

    except Exception as e:

        print("ERROR EN EL DASHBOARD:", e)

        return render_template(
            "dashboard.html",
            error=str(e)
        )


# ==========================================
# EJECUTAR EL SERVIDOR
# ==========================================

if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )
