Starter kit Flask – Proyecto FibraConecta (churn)

Contenido:
- app.py: aplicación Flask con endpoints / y /upload, carga del modelo y reglas de negocio con TODOs.
- templates/base.html: layout base con Bootstrap.
- templates/upload.html: formulario para subir el CSV.
- templates/results.html: tabla de resultados + botón de descarga.
- static/: carpeta para CSS adicional (opcional).

Instrucciones mínimas para los estudiantes:
1. Entrenar el modelo en el notebook de ML y guardar el archivo como `modelo_churn.pkl` en la misma carpeta que app.py.
2. Ajustar la lista REQUIRED_COLUMNS en app.py para que coincida con las columnas de features de la sábana.
3. Implementar la función `aplicar_reglas_negocio` con la lógica que el grupo defina.
4. Ejecutar la app con:
   python app.py
5. Probar subiendo un CSV con la misma estructura de features que el modelo espera.
