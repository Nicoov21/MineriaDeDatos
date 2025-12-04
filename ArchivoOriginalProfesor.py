from flask import Flask, render_template, request, redirect, url_for, send_file, flash
import pandas as pd
import joblib
import io

app = Flask(__name__)
app.secret_key = "cambia_esto_en_produccion"  # necesario para flash messages

# ============================================
# Cargar modelo entrenado (Pipeline de scikit-learn)
# ============================================

MODEL_PATH = "modelo_churn.pkl"  # TODO: asegurarse de que el archivo existe

try:
    modelo = joblib.load(MODEL_PATH)
except Exception as e:
    print(f"ERROR cargando modelo desde {MODEL_PATH}: {e}")
    modelo = None  # fallará al predecir si no corrigen esto


# ============================================
# Helpers
# ============================================

# Columnas mínimas que el modelo espera (features)
# TODO: actualizar según la sábana real
REQUIRED_COLUMNS = [
    # "monto_neto_promedio_3m",
    # "cantidad_facturas_vencidas_3m",
    # "tickets_totales_3m",
    # "horas_corte_total_3m",
    # "logins_portal_3m",
    # ...
]


def validar_columnas(df):
    """Verifica que el CSV tenga al menos las columnas mínimas requeridas."""
    faltantes = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    return faltantes


def aplicar_reglas_negocio(row, prob_churn):
    """
    TODO: implementar reglas de negocio para generar la recomendación.
    Recibe una fila del dataframe + la probabilidad de churn (0 a 1).
    Debe devolver: (accion_recomendada, prioridad)
    """
    # EJEMPLO MUY SIMPLE (REEMPLAZAR):
    if prob_churn >= 0.8:
        accion = "Contactar urgente: retención premium"
        prioridad = "ALTA"
    elif prob_churn >= 0.5:
        accion = "Ofrecer beneficio / descuento moderado"
        prioridad = "MEDIA"
    elif prob_churn >= 0.3:
        accion = "Mantener contacto ligero (email / campaña)"
        prioridad = "BAJA"
    else:
        accion = "No intervenir por ahora"
        prioridad = "NINGUNA"

    return accion, prioridad


# ============================================
# Rutas
# ============================================

@app.route("/", methods=["GET"])
def index():
    """Página principal: formulario para subir CSV."""
    return render_template("upload.html")


@app.route("/upload", methods=["POST"])
def upload():
    """Procesa el CSV subido, genera predicciones y muestra resultados."""
    if modelo is None:
        flash("El modelo no está disponible. Contactar al equipo técnico.")
        return redirect(url_for("index"))

    if "file" not in request.files:
        flash("No se encontró archivo en la petición.")
        return redirect(url_for("index"))

    file = request.files["file"]

    if file.filename == "":
        flash("No se seleccionó ningún archivo.")
        return redirect(url_for("index"))

    try:
        # Leer CSV en DataFrame
        df_input = pd.read_csv(file)
    except Exception as e:
        flash(f"Error leyendo el CSV: {e}")
        return redirect(url_for("index"))

    # Validar columnas
    faltantes = validar_columnas(df_input)
    if faltantes:
        msg = "Faltan columnas requeridas para el modelo: " + ", ".join(faltantes)
        flash(msg)
        return redirect(url_for("index"))

    # Extraer solo columnas necesarias para el modelo
    X = df_input[REQUIRED_COLUMNS].copy()

    # Generar predicciones de probabilidad (asumiendo que el modelo es un Pipeline)
    try:
        proba = modelo.predict_proba(X)[:, 1]  # probabilidad de churn (clase positiva)
    except Exception as e:
        flash(f"Error al predecir con el modelo: {e}")
        return redirect(url_for("index"))

    df_result = df_input.copy()
    df_result["prob_churn"] = proba
    df_result["prob_churn_pct"] = (df_result["prob_churn"] * 100).round(2)

    # Aplicar reglas de negocio fila a fila
    acciones = []
    prioridades = []

    for _, row in df_result.iterrows():
        accion, prioridad = aplicar_reglas_negocio(row, row["prob_churn"])
        acciones.append(accion)
        prioridades.append(prioridad)

    df_result["accion_recomendada"] = acciones
    df_result["prioridad"] = prioridades

    # Guardar CSV en memoria para descarga
    csv_buffer = io.StringIO()
    df_result.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)

    # Convertir a HTML para mostrar tabla en la página
    table_html = df_result.head(100).to_html(classes="table table-striped table-sm", index=False)

    return render_template(
        "results.html",
        table_html=table_html,
        csv_data=csv_buffer.getvalue()
    )


@app.route("/download", methods=["POST"])
def download():
    """Descarga el CSV con resultados, enviado desde /results."""
    csv_data = request.form.get("csv_data", None)
    if csv_data is None:
        flash("No hay datos para descargar.")
        return redirect(url_for("index"))

    buffer = io.BytesIO()
    buffer.write(csv_data.encode("utf-8"))
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="resultados_churn.csv",
        mimetype="text/csv"
    )


if __name__ == "__main__":
    # TODO: quitar debug=True en producción
    app.run(host="0.0.0.0", port=5000, debug=True)
