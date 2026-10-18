# Prototipo: Sistema de Comunicación de Reportes de Salud Rural

Proyecto COIL **Ucompensar (Colombia) – Unicda (República Dominicana)** · Grupo 6 · Actividad 5

Simula la comunicación entre un puesto de salud rural (vereda / batey) y un hospital rural:

1. **Registro de pacientes**: identificación, procedencia, grupo sanguíneo.
2. **Puesto de salud**: captura de signos vitales validados, triaje automático (Alta/Media/Baja)
   y decisión del canal: **sincrónico** (teleconsulta), **asincrónico** (reporte) u **offline** (cola local).
3. **Hospital rural**: bandeja ordenada por prioridad, signos alterados en rojo, diagnóstico CIE-10,
   observación médica y actualización del estado.
4. **Reportes**: filtros, gráficos y descarga CSV.

## Tecnologías
- Python + [Streamlit](https://streamlit.io) (interfaz web)
- SQLite (`sqlite3`, esquema de la Actividad 4 en `data/esquema.sql`)

## Ejecutar localmente
```bash
pip install -r requirements.txt
streamlit run app.py
```
La base `data/PROYECTO_COIL_GRUPO6.db` se crea automáticamente con datos de demostración.

> Nota: en Streamlit Community Cloud la base se reinicia con los datos de demostración
> cada vez que la app se reinicia o se redespliega.
