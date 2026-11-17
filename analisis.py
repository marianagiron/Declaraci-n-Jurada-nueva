
import pandas as pd
import unicodedata
import os
import shutil
from datetime import datetime

from conexion_sheets import obtener_datos


# ==========================================
# FUNCIONES AUXILIARES
# ==========================================

def normalizar(texto):
    texto = str(texto).lower().strip()

    texto = unicodedata.normalize("NFD", texto)

    texto = "".join(
        c for c in texto
        if unicodedata.category(c) != "Mn"
    )

    return " ".join(texto.split())


def buscar_columna(datos, alternativas):

    for columna in datos.columns:

        nombre = normalizar(columna)

        for alternativa in alternativas:

            if normalizar(alternativa) in nombre:
                return columna

    raise ValueError(
        "No se encontro la columna: " + str(alternativas)
    )


def contar_por(datos, columna, nombre):

    resultado = (
        datos[columna]
        .fillna("Sin registro")
        .value_counts()
        .reset_index()
    )

    resultado.columns = [nombre, "Cantidad"]

    return resultado.to_dict("records")


def limpiar_importe(valor):

    if pd.isna(valor):
        return 0.0

    if isinstance(valor, (int, float)):
        return float(valor)

    valor = str(valor).replace("S/", "").strip()

    if "," in valor and "." in valor:
        valor = valor.replace(",", "")
    elif "," in valor:
        valor = valor.replace(",", ".")

    try:
        return float(valor)
    except ValueError:
        return 0.0


def sumar_por(datos, columna, importe, nombre):

    copia = datos.copy()

    copia[importe] = copia[importe].apply(limpiar_importe)

    resultado = (
        copia.groupby(columna)[importe]
        .sum()
        .reset_index()
    )

    resultado.columns = [nombre, "Importe total"]

    return resultado.to_dict("records")


# ==========================================
# MARIANA: FUNCIONES 1 Y 2
# ==========================================

def contar_declaraciones_proyecto(datos):

    proyecto = buscar_columna(datos, ["area"])

    return contar_por(datos, proyecto, "Proyecto")


def sumar_importes_proyecto(datos):

    proyecto = buscar_columna(datos, ["area"])

    importe = buscar_columna(datos, ["monto gastado"])

    return sumar_por(datos, proyecto, importe, "Proyecto")


# ==========================================
# IRMA: FUNCIONES 3 Y 4
# ==========================================

def validar_archivo(archivo):

    return os.path.exists(archivo)


def crear_carpeta_por_mes(ruta_base):

    hoy = datetime.now()

    mes = hoy.strftime("%Y-%m")

    carpeta = os.path.join(ruta_base, mes)

    os.makedirs(carpeta, exist_ok=True)

    return carpeta


def copiar_declaracion(archivo, carpeta_destino):

    if not validar_archivo(archivo):
        raise FileNotFoundError("No existe el archivo.")

    os.makedirs(carpeta_destino, exist_ok=True)

    shutil.copy(archivo, carpeta_destino)

    return carpeta_destino


# ==========================================
# MARIANA E IRMA: FUNCIONES 5 Y 6
# ==========================================

def contar_por_solicitante(datos):

    solicitante = buscar_columna(
        datos,
        ["apellidos y nombres completos"]
    )

    return contar_por(datos, solicitante, "Solicitante")


def contar_por_mes(datos):

    columna_fecha = buscar_columna(
        datos,
        ["fecha en que se realizo el gasto"]
    )

    conteos = {}

    for valor in datos[columna_fecha]:

        fecha = pd.to_datetime(
            valor,
            errors="coerce",
            dayfirst=True
        )

        if pd.isna(fecha):
            mes = "Fecha no valida"
        else:
            mes = fecha.strftime("%Y-%m")

        conteos[mes] = conteos.get(mes, 0) + 1

    return [
        {"Mes": mes, "Cantidad": cantidad}
        for mes, cantidad in sorted(conteos.items())
    ]


# ==========================================
# ANALISIS GENERAL DEL DASHBOARD PROSIP
# ==========================================


def obtener_analisis():


    datos = pd.DataFrame(obtener_datos())

    print("\n========== COLUMNAS REALES ==========")
    print(datos.columns.tolist())
    print("=====================================")

    if datos.empty:
        raise ValueError("No hay registros en Google Sheets.")


    # Buscar las columnas reales de PROSIP
    columna_nombres = buscar_columna(datos, ["nombres"])
    columna_apellidos = buscar_columna(datos, ["apellidos"])

    datos["Solicitante"] = (
        datos[columna_nombres].fillna("").astype(str).str.strip()
        + " "
        + datos[columna_apellidos].fillna("").astype(str).str.strip()
    )

    area = buscar_columna(datos, ["area"])
    concepto = buscar_columna(datos, ["concepto"])
    recibido = buscar_columna(datos, ["monto recibido"])
    gastado = buscar_columna(datos, ["monto gastado"])
    saldo = buscar_columna(datos, ["saldo resultante"])
    # Convertir importes a números
    datos[recibido] = datos[recibido].apply(limpiar_importe)
    datos[gastado] = datos[gastado].apply(limpiar_importe)
    datos[saldo] = datos[saldo].apply(limpiar_importe)

    # 1. Declaraciones por área
    tabla_proyectos = contar_por(
        datos, area, "Proyecto"
    )

    # 2. Importes gastados por concepto
    tabla_centros = sumar_por(
        datos, concepto, gastado, "Centro de costo"
    )

    # 3. Declaraciones por solicitante
    tabla_solicitantes = contar_por(
        datos, "Solicitante","Solicitante"
    )

    # 4. Resumen financiero en soles
    tabla_meses = [
        ("Monto recibido", datos[recibido].sum()),
        ("Monto gastado", datos[gastado].sum()),
        ("Saldo resultante", datos[saldo].sum())
    ]

    return {
        "datos": datos,
        "total_registros": len(datos),
        "total_importe": datos[gastado].sum(),
        "total_recibido": datos[recibido].sum(),
        "total_gastado": datos[gastado].sum(),
        "saldo_total": datos[saldo].sum(),
        "proyectos": tabla_proyectos,
        "centros": datos[concepto].dropna().unique().tolist(),
        "importes_centro": tabla_centros,
        "solicitantes": tabla_solicitantes,
        "meses": tabla_meses
    }