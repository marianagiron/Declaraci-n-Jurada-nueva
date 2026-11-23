
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

    import re
    import unicodedata

    # ==========================================
    # 1. OBTENER DATOS DE GOOGLE SHEETS
    # ==========================================

    datos = pd.DataFrame(obtener_datos())

    if datos.empty:
        raise ValueError(
            "No hay registros en Google Sheets."
        )

    print("\n========== COLUMNAS REALES ==========")
    print(datos.columns.tolist())
    print("\nPRIMEROS REGISTROS:")
    print(datos.head().to_string())
    print("=====================================")

    # ==========================================
    # 2. NORMALIZAR COLUMNAS
    # ==========================================

    def normalizar_columna(texto):

        texto = str(texto).lower().strip()

        texto = unicodedata.normalize("NFD", texto)

        texto = "".join(
            c for c in texto
            if unicodedata.category(c) != "Mn"
        )

        return re.sub(r"[^a-z0-9]", "", texto)

    def obtener_columna(opciones):

        columnas = {
            normalizar_columna(col): col
            for col in datos.columns
        }

        # Buscar coincidencia exacta
        for opcion in opciones:

            clave = normalizar_columna(opcion)

            if clave in columnas:
                return columnas[clave]

        # Buscar coincidencia parcial
        for opcion in opciones:

            clave = normalizar_columna(opcion)

            for columna in datos.columns:

                if clave in normalizar_columna(columna):
                    return columna

        raise ValueError(
            f"No se encontró la columna {opciones}. "
            f"Columnas disponibles: {datos.columns.tolist()}"
        )

    # ==========================================
    # 3. IDENTIFICAR COLUMNAS
    # ==========================================

    # Nombres: puede existir una columna completa
    # o dos columnas separadas.

    try:

        columna_nombres = obtener_columna(
            ["nombres", "nombre"]
        )

        columna_apellidos = obtener_columna(
            ["apellidos", "apellido"]
        )

        nombres_separados = True

    except ValueError:

        columna_completa = obtener_columna([
            "apellidos y nombres completos",
            "nombres y apellidos completos",
            "nombres y apellidos",
            "solicitante"
        ])

        nombres_separados = False

    area = obtener_columna([
        "area",
        "area solicitante",
        "departamento",
        "proyecto"
    ])

    concepto = obtener_columna([
        "concepto",
        "concepto del gasto"
    ])

    recibido = obtener_columna([
        "monto recibido",
        "importe recibido",
        "total recibido"
    ])

    gastado = obtener_columna([
        "monto gastado",
        "importe gastado",
        "total gastado"
    ])

    # El saldo puede existir o calcularse
    try:

        saldo = obtener_columna([
            "saldo resultante",
            "saldo"
        ])

    except ValueError:

        saldo = None

    # ==========================================
    # 4. COMPROBAR LOS DATOS REALES
    # ==========================================

    print("\n====== COMPROBACIÓN DE IMPORTES ======")

    print("Columna recibido:", recibido)
    print("Columna gastado:", gastado)

    print("\nVALORES ORIGINALES:")

    print(
        datos[[recibido, gastado]]
        .head(10)
        .to_string()
    )

    print("======================================")

    # ==========================================
    # 5. UNIR NOMBRES Y APELLIDOS
    # ==========================================

    if nombres_separados:

        datos["Nombres"] = (
            datos[columna_nombres]
            .fillna("")
            .astype(str)
            .str.strip()
        )

        datos["Apellidos"] = (
            datos[columna_apellidos]
            .fillna("")
            .astype(str)
            .str.strip()
        )

        datos["Solicitante"] = (
            datos["Nombres"] + " " + datos["Apellidos"]
        ).str.strip()

    else:

        datos["Solicitante"] = (
            datos[columna_completa]
            .fillna("")
            .astype(str)
            .str.strip()
        )

        datos["Nombres"] = datos["Solicitante"]
        datos["Apellidos"] = ""

    # ==========================================
    # 6. CONVERTIR IMPORTES A NÚMEROS
    # ==========================================

    def convertir_dinero(valor):

        if pd.isna(valor):
            return 0.0

        texto = str(valor).strip()

        if not texto:
            return 0.0

        texto = texto.replace("S/.", "")
        texto = texto.replace("S/", "")
        texto = texto.replace("s/", "")
        texto = texto.replace(" ", "")

        texto = re.sub(
            r"[^0-9,.-]",
            "",
            texto
        )

        if not texto:
            return 0.0

        if "," in texto and "." in texto:

            if texto.rfind(",") > texto.rfind("."):

                texto = texto.replace(".", "")
                texto = texto.replace(",", ".")

            else:

                texto = texto.replace(",", "")

        elif "," in texto:

            partes = texto.split(",")

            if len(partes[-1]) in (1, 2):

                texto = texto.replace(",", ".")

            else:

                texto = texto.replace(",", "")

        elif "." in texto:

            partes = texto.split(".")

            if len(partes[-1]) == 3 and len(partes) > 1:

                texto = texto.replace(".", "")

        try:

            return float(texto)

        except ValueError:

            return 0.0

    datos[recibido] = datos[recibido].apply(
        convertir_dinero
    )

    datos[gastado] = datos[gastado].apply(
        convertir_dinero
    )

    # ==========================================
    # 7. CALCULAR SALDO
    # ==========================================

    if saldo is not None:

        datos[saldo] = datos[saldo].apply(
            convertir_dinero
        )

        if datos[saldo].isna().all():
            datos[saldo] = (
                datos[recibido] - datos[gastado]
            )

    else:

        datos["Saldo calculado"] = (
            datos[recibido] - datos[gastado]
        )

        saldo = "Saldo calculado"

    # ==========================================
    # 8. ANALISIS POR AREA
    # ==========================================

    tabla_proyectos = contar_por(
        datos,
        area,
        "Proyecto"
    )

    # ==========================================
    # 9. ANALISIS POR CONCEPTO
    # ==========================================

    tabla_centros = sumar_por(
        datos,
        concepto,
        gastado,
        "Centro de costo"
    )

    # ==========================================
    # 10. ANALISIS POR SOLICITANTE
    # ==========================================

    tabla_solicitantes = contar_por(
        datos,
        "Solicitante",
        "Solicitante"
    )

    # ==========================================
    # 11. RESUMEN FINANCIERO
    # ==========================================

    total_recibido = float(
        datos[recibido].sum()
    )

    total_gastado = float(
        datos[gastado].sum()
    )

    total_saldo = float(
        datos[saldo].sum()
    )

    tabla_meses = [
        ("Monto recibido", total_recibido),
        ("Monto gastado", total_gastado),
        ("Saldo resultante", total_saldo)
    ]

    # ==========================================
    # 12. PREPARAR REGISTROS PARA EL DASHBOARD
    # ==========================================

    registros = []

    for _, fila in datos.iterrows():

        registros.append({

            "Nombres": str(fila["Nombres"]),

            "Apellidos": str(fila["Apellidos"]),

            "Solicitante": str(fila["Solicitante"]),

            "Area": str(fila[area]),

            "Concepto": str(fila[concepto]),

            "Monto recibido": float(fila[recibido]),

            "Monto gastado": float(fila[gastado]),

            "Saldo resultante": float(fila[saldo])

        })

    # ==========================================
    # 13. DEVOLVER TODOS LOS RESULTADOS
    # ==========================================

    return {

        "total_registros": len(datos),

        "total_importe": total_recibido,

        "total_recibido": total_recibido,

        "total_gastado": total_gastado,

        "total_saldo": total_saldo,

        "proyectos": tabla_proyectos,

        "centros": datos[concepto]
            .dropna()
            .unique()
            .tolist(),

        "importes_centro": tabla_centros,

        "solicitantes": tabla_solicitantes,

        "meses": tabla_meses,

        "registros": registros

    }