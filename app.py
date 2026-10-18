"""Prototipo: Sistema de Comunicacion de Reportes de Salud (vereda -> hospital rural).

Proyecto COIL Ucompensar (Colombia) - Unicda (Republica Dominicana) - Grupo 6.
Ejecutar localmente:  streamlit run app.py
"""
import sqlite3

import pandas as pd
import streamlit as st

import db

st.set_page_config(page_title="Salud Rural COIL", page_icon="🏥", layout="wide")


@st.cache_resource
def obtener_conexion():
    return db.inicializar()


con = obtener_conexion()

COLOR_PRIORIDAD = {"Alta": "🔴 Alta", "Media": "🟡 Media", "Baja": "🟢 Baja"}
ETIQUETAS = {
    "frecuencia_cardiaca": "FC (lat/min)",
    "frecuencia_respiratoria": "FR (resp/min)",
    "presion_sistolica": "PA sist. (mmHg)",
    "presion_diastolica": "PA diast. (mmHg)",
    "spo2_porcentaje": "SpO2 (%)",
}


def reporte_df():
    return pd.DataFrame(db.listar(con, db.SQL_REPORTE))


def resaltar_signos(df):
    """Pinta en rojo los signos vitales fuera de rango (Actividad 4, pregunta d)."""
    estilos = pd.DataFrame("", index=df.index, columns=df.columns)
    for col, (bajo, alto) in db.RANGOS_NORMALES.items():
        etiqueta = ETIQUETAS[col]
        if etiqueta in df.columns:
            fuera = (df[etiqueta] < bajo) | (df[etiqueta] > alto)
            estilos.loc[fuera, etiqueta] = "background-color: #f8d7da; color: #842029; font-weight: 600"
    return estilos


# ------------------------------------------------------------------ menu
st.sidebar.title("🏥 Salud Rural COIL")
st.sidebar.caption("Ucompensar 🇨🇴 · Unicda 🇩🇴 · Grupo 6")
modulo = st.sidebar.radio(
    "Módulo",
    ["Inicio", "1. Registro de pacientes", "2. Puesto de salud (vereda)",
     "3. Hospital rural (médico)", "4. Reportes"],
)
st.sidebar.divider()
st.sidebar.markdown(
    "**Flujo de comunicación**\n\n"
    "🔴 Alta + conexión → **Sincrónico** (teleconsulta)\n\n"
    "🟡/🟢 + conexión → **Asincrónico** (reporte)\n\n"
    "📴 Sin conexión → **Cola offline**, se envía al recuperar señal"
)

# ------------------------------------------------------------------ inicio
if modulo == "Inicio":
    st.title("Sistema de Comunicación de Reportes de Salud")
    st.write(
        "Prototipo que simula la comunicación entre un **puesto de salud rural** (vereda en "
        "Colombia o batey/UNAP en República Dominicana) y un **hospital rural**: registro del "
        "paciente, captura de signos vitales, triaje automático, envío sincrónico/asincrónico "
        "y respuesta médica."
    )
    df = reporte_df()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Pacientes", con.execute("SELECT COUNT(*) FROM Paciente").fetchone()[0])
    c2.metric("Consultas", len(df))
    c3.metric("🔴 Prioridad alta sin atender",
              int(((df["nivel_prioridad"] == "Alta") & (df["estado"] != "Atendido")).sum()) if len(df) else 0)
    c4.metric("📴 En cola offline",
              int((df["estado"] == "En cola (sin conexion)").sum()) if len(df) else 0)
    st.subheader("Cómo usar la demo")
    st.markdown(
        "1. **Registro de pacientes**: crea un paciente nuevo.\n"
        "2. **Puesto de salud**: el promotor registra la consulta y los signos vitales. El sistema "
        "clasifica la prioridad y decide el canal. Prueba desactivando *Hay conexión*.\n"
        "3. **Hospital rural**: el médico ve la bandeja ordenada por prioridad, asigna el "
        "diagnóstico CIE-10, escribe la observación y actualiza el estado.\n"
        "4. **Reportes**: consulta, filtra y descarga los reportes."
    )

# ------------------------------------------------------------------ 1. registro
elif modulo == "1. Registro de pacientes":
    st.title("👤 Registro de pacientes")
    centros = db.listar(con, "SELECT id_centro, nombre_centro, municipio_vereda FROM CentroMedico")
    with st.form("form_paciente", clear_on_submit=True):
        c1, c2 = st.columns(2)
        id_paciente = c1.text_input("Documento / ID del paciente *", placeholder="CC-1234 o cédula RD")
        nombre = c2.text_input("Nombre completo *")
        anios = c1.number_input("Edad (años) *", 0, 120, 25)
        meses = c2.number_input("Meses", 0, 11, 0)
        genero = c1.selectbox("Género *", ["M", "F", "Otro"])
        procedencia = c2.text_input("Vereda / Municipio / Batey de procedencia *")
        centro = c1.selectbox("Centro de atención *", centros,
                              format_func=lambda c: f"{c['nombre_centro']} — {c['municipio_vereda']}")
        g1, g2 = c2.columns(2)
        grupo = g1.selectbox("Grupo sanguíneo", ["A", "B", "AB", "O"])
        rh = g2.selectbox("Factor RH", ["P", "N"], format_func=lambda x: "Positivo" if x == "P" else "Negativo")
        enviado = st.form_submit_button("Guardar paciente", type="primary")
    if enviado:
        if not id_paciente.strip() or not nombre.strip() or not procedencia.strip():
            st.error("Complete los campos obligatorios (*).")
        else:
            try:
                db.registrar_paciente(con, {
                    "id_paciente": id_paciente.strip(), "nombre": nombre.strip(),
                    "edad": f"{anios}A {meses}M", "genero": genero,
                    "vereda_municipio": procedencia.strip(), "id_centro": centro["id_centro"],
                    "grupo_sanguineo": grupo, "factor_rh": rh,
                })
                st.success(f"Paciente {nombre} registrado.")
            except sqlite3.IntegrityError:
                st.error("Ya existe un paciente con ese documento.")
    st.subheader("Pacientes registrados")
    st.dataframe(pd.DataFrame(db.listar(con, """
        SELECT p.id_paciente AS ID, p.nombre AS Nombre, p.edad AS Edad, p.genero AS Genero,
               p.vereda_municipio AS Procedencia, p.grupo_sanguineo || p.factor_rh AS "Grupo/RH",
               c.nombre_centro AS Centro
        FROM Paciente p LEFT JOIN CentroMedico c ON c.id_centro = p.id_centro
        ORDER BY p.rowid DESC""")), hide_index=True, width="stretch")

# ------------------------------------------------------------------ 2. puesto de salud
elif modulo == "2. Puesto de salud (vereda)":
    st.title("🩺 Puesto de salud — Nueva consulta")
    pacientes = db.listar(con, "SELECT id_paciente, nombre, vereda_municipio FROM Paciente ORDER BY nombre")
    doctores = db.listar(con, "SELECT id_doctor, nombre_completo FROM Doctor")
    if not pacientes:
        st.info("Primero registre un paciente.")
        st.stop()
    hay_conexion = st.toggle("📶 Hay conexión a internet en el puesto de salud", value=True)
    with st.form("form_consulta", clear_on_submit=True):
        c1, c2 = st.columns(2)
        paciente = c1.selectbox("Paciente *", pacientes,
                                format_func=lambda p: f"{p['nombre']} ({p['id_paciente']}) — {p['vereda_municipio']}")
        doctor = c2.selectbox("Médico que recibe *", doctores, format_func=lambda d: d["nombre_completo"])
        motivo = st.text_input("Motivo de consulta *")
        st.markdown("**Signos vitales** (rangos fisiológicos validados)")
        s1, s2, s3 = st.columns(3)
        fc = s1.number_input("Frecuencia cardíaca (lat/min)", 30, 220, 75)
        fr = s2.number_input("Frecuencia respiratoria (resp/min)", 5, 60, 16)
        spo2 = s3.number_input("SpO2 (%)", 50.0, 100.0, 97.0, step=1.0)
        pas = s1.number_input("Presión sistólica (mmHg)", 60, 250, 118)
        pad = s2.number_input("Presión diastólica (mmHg)", 30, 150, 76)
        tomo_ph = s3.checkbox("Se tomó pH")
        ph = s3.number_input("pH", 6.8, 7.8, 7.4, step=0.01)
        enviado = st.form_submit_button("Registrar y enviar", type="primary")
    if enviado:
        if not motivo.strip():
            st.error("Escriba el motivo de consulta.")
        elif pad >= pas:
            st.error("La presión diastólica debe ser menor que la sistólica.")
        else:
            id_c, prioridad, canal, estado = db.registrar_consulta(
                con, paciente["id_paciente"], doctor["id_doctor"], motivo.strip(), {
                    "frecuencia_cardiaca": fc, "frecuencia_respiratoria": fr,
                    "presion_sistolica": pas, "presion_diastolica": pad,
                    "spo2_porcentaje": spo2, "ph": ph if tomo_ph else None,
                }, hay_conexion)
            st.subheader(f"Consulta #{id_c} — Prioridad {COLOR_PRIORIDAD[prioridad]}")
            if canal.startswith("Sincronico"):
                st.error(f"🚨 {canal}: conectando con {doctor['nombre_completo']} en tiempo real.")
            elif canal.startswith("Asincronico"):
                st.success(f"📨 {canal}: el reporte quedó en la bandeja del hospital.")
            else:
                st.warning(f"📴 {canal}: el reporte se guardó en el dispositivo y se enviará al recuperar la señal.")
                if prioridad == "Alta":
                    st.error("URGENTE: remitir al paciente o comunicar por teléfono/radio.")

    st.divider()
    en_cola = con.execute("SELECT COUNT(*) FROM ConsultaMedica WHERE estado = 'En cola (sin conexion)'").fetchone()[0]
    st.markdown(f"**Cola offline:** {en_cola} reporte(s) pendiente(s) de envío.")
    if st.button("🔄 Se recuperó la conexión — sincronizar", disabled=en_cola == 0 or not hay_conexion):
        st.success(f"{db.sincronizar_pendientes(con)} reporte(s) enviados al hospital.")
        st.rerun()

# ------------------------------------------------------------------ 3. hospital
elif modulo == "3. Hospital rural (médico)":
    st.title("🏥 Hospital rural — Bandeja de reportes")
    df = reporte_df()
    activos = df[df["estado"].isin(["Pendiente", "En atencion"])] if len(df) else df
    if activos.empty:
        st.info("No hay reportes pendientes. 🎉")
    else:
        vista = pd.DataFrame({
            "#": activos["id_consulta"],
            "Prioridad": activos["nivel_prioridad"].map(COLOR_PRIORIDAD),
            "Paciente": activos["nombre"], "Edad": activos["edad"],
            "Procedencia": activos["vereda_municipio"], "Motivo": activos["motivo_consulta"],
            **{ETIQUETAS[c]: activos[c] for c in db.RANGOS_NORMALES},
            "Canal": activos["canal_comunicacion"], "Estado": activos["estado"],
        })
        st.caption("Ordenado por prioridad. En rojo: signos vitales fuera de rango normal.")
        st.dataframe(vista.style.apply(resaltar_signos, axis=None), hide_index=True, width="stretch")

        st.subheader("Atender reporte")
        opciones = activos.to_dict("records")
        sel = st.selectbox("Seleccione la consulta", opciones,
                           format_func=lambda r: f"#{r['id_consulta']} · {COLOR_PRIORIDAD[r['nivel_prioridad']]} · {r['nombre']}")
        c1, c2 = st.columns(2)
        c1.markdown(
            f"**{sel['nombre']}** · {sel['edad']} · {sel['genero']} · Grupo {sel['grupo_sanguineo'] or '-'}{sel['factor_rh'] or ''}\n\n"
            f"📍 {sel['vereda_municipio']} ({sel['nombre_centro']})\n\n"
            f"🩺 Motivo: {sel['motivo_consulta']}"
        )
        c2.markdown(
            f"SpO2 **{sel['spo2_porcentaje']} %** · PA **{sel['presion_sistolica']}/{sel['presion_diastolica']}** mmHg\n\n"
            f"FC **{sel['frecuencia_cardiaca']}** lat/min · FR **{sel['frecuencia_respiratoria']}** resp/min"
            + (f" · pH **{sel['ph']}**" if pd.notna(sel["ph"]) else "")
        )
        diagnosticos = db.listar(con, "SELECT id_diagnostico, codigo_cie10, nombre_enfermedad FROM DiagnosticoMedico ORDER BY codigo_cie10")
        with st.form("form_atencion"):
            dx = st.selectbox("Diagnóstico (CIE-10)", diagnosticos,
                              format_func=lambda d: f"{d['codigo_cie10']} — {d['nombre_enfermedad']}")
            obs = st.text_area("Observación médica / indicaciones")
            estado = st.radio("Estado", ["En atencion", "Atendido"], horizontal=True, index=1)
            if st.form_submit_button("Guardar y responder al puesto de salud", type="primary"):
                db.actualizar_consulta(con, int(sel["id_consulta"]), dx["id_diagnostico"], obs.strip(), estado)
                st.success("Respuesta registrada y enviada al puesto de salud.")
                st.rerun()

# ------------------------------------------------------------------ 4. reportes
else:
    st.title("📊 Reportes")
    df = reporte_df()
    if df.empty:
        st.info("Aún no hay consultas registradas.")
        st.stop()
    f1, f2, f3 = st.columns(3)
    prioridades = f1.multiselect("Prioridad", ["Alta", "Media", "Baja"], default=["Alta", "Media", "Baja"])
    estados = f2.multiselect("Estado", db.ESTADOS, default=db.ESTADOS)
    texto = f3.text_input("Buscar paciente o procedencia")
    filtrado = df[df["nivel_prioridad"].isin(prioridades) & df["estado"].isin(estados)]
    if texto:
        filtrado = filtrado[filtrado["nombre"].str.contains(texto, case=False)
                            | filtrado["vereda_municipio"].str.contains(texto, case=False)]

    c1, c2, c3 = st.columns(3)
    c1.bar_chart(filtrado["nivel_prioridad"].value_counts(), horizontal=True)
    c2.bar_chart(filtrado["estado"].value_counts(), horizontal=True)
    c3.bar_chart(filtrado["canal_comunicacion"].value_counts(), horizontal=True)

    tabla = filtrado.rename(columns=ETIQUETAS).assign(
        nivel_prioridad=lambda d: d["nivel_prioridad"].map(COLOR_PRIORIDAD))
    st.dataframe(tabla.style.apply(resaltar_signos, axis=None), hide_index=True, width="stretch")
    st.download_button("⬇️ Descargar CSV", filtrado.to_csv(index=False).encode("utf-8-sig"),
                       "reporte_salud_rural.csv", "text/csv")
