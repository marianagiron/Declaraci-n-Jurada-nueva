from flask import Flask, render_template
from analisis import obtener_analisis

app = Flask(__name__)


@app.route("/")
def dashboard():
    try:
        resultado = obtener_analisis()

        return render_template(
            "dashboard.html",

            total_registros=resultado["total_registros"],
            total_recibido=resultado["total_recibido"],
            total_gastado=resultado["total_gastado"],
            total_saldo=resultado["total_saldo"],

            proyectos=resultado["proyectos"],
            importes_centro=resultado["importes_centro"],
            solicitantes=resultado["solicitantes"],
            registros=resultado["registros"],

            error=None
        )

    except Exception as e:
        print("ERROR EN EL DASHBOARD:", e)
        return render_template("dashboard.html", error=str(e))


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
    