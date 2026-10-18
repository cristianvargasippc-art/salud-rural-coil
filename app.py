"""Prototipo: Sistema de Comunicacion de Reportes de Salud (vereda -> hospital rural).

Proyecto COIL Ucompensar (Colombia) - Unicda (Republica Dominicana) - Grupo 6.
Ejecutar localmente:  streamlit run app.py
"""
import html
import sqlite3

import altair as alt
import pandas as pd
import streamlit as st

import db

st.set_page_config(page_title="Salud Rural COIL", page_icon=":material/local_hospital:", layout="wide")


@st.cache_resource
def obtener_conexion():
    return db.inicializar()


con = obtener_conexion()

# ------------------------------------------------------------------ estilos
COLORES = {"Alta": "#dc2626", "Media": "#d97706", "Baja": "#16a34a"}
FONDOS = {"Alta": "#fee2e2", "Media": "#fef3c7", "Baja": "#dcfce7"}
ETIQUETAS = {
    "frecuencia_cardiaca": "FC (lat/min)",
    "frecuencia_respiratoria": "FR (resp/min)",
    "presion_sistolica": "PA sist. (mmHg)",
    "presion_diastolica": "PA diast. (mmHg)",
    "spo2_porcentaje": "SpO2 (%)",
}

st.markdown(
    """
<style>
#MainMenu, footer {visibility: hidden;}
.block-container {padding-top: 2rem; max-width: 1200px;}
[data-testid="stSidebar"] {background: #1b365d;}
[data-testid="stSidebar"] * {color: #e2e8f0 !important;}
[data-testid="stSidebarNavLink"][aria-current="page"] {background: rgba(255,255,255,.12);}
.hero {background: linear-gradient(120deg, #1b365d 0%, #0d9488 100%); color: #fff;
       padding: 1.6rem 2rem; border-radius: 14px; margin-bottom: 1.4rem;}
.hero h1 {color: #fff; font-size: 1.7rem; margin: 0 0 .3rem 0; padding: 0;}
.hero p {color: #dbeafe; margin: 0; font-size: .98rem;}
.kpi {background: #fff; border: 1px solid #e5e9f0; border-radius: 12px; padding: 1rem 1.2rem;
      border-left: 5px solid var(--c, #0d9488);}
.kpi .v {font-size: 1.9rem; font-weight: 700; color: #1b2a41; line-height: 1.1;}
.kpi .l {font-size: .82rem; color: #64748b; text-transform: uppercase; letter-spacing: .04em;}
.badge {display: inline-block; padding: .18rem .7rem; border-radius: 999px; font-size: .8rem;
        font-weight: 600;}
.card {background: #fff; border: 1px solid #e5e9f0; border-radius: 12px; padding: 1.1rem 1.3rem;
       margin-bottom: 1rem;}
.card h4 {margin: 0 0 .4rem 0; color: #1b365d;}
.muted {color: #64748b; font-size: .9rem;}
.vitals {display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: .6rem;
         margin-top: .6rem;}
.vital {border-radius: 10px; padding: .6rem .8rem; background: #f1f5f9;}
.vital.alerta {background: #fee2e2;}
.vital .n {font-size: .75rem; color: #64748b; text-transform: uppercase;}
.vital .x {font-size: 1.3rem; font-weight: 700; color: #1b2a41;}
.vital.alerta .x {color: #b91c1c;}
.step {display: flex; gap: .8rem; align-items: flex-start; margin-bottom: .7rem;}
.step .num {background: #0d9488; color: #fff; border-radius: 50%; min-width: 1.8rem; height: 1.8rem;
            display: flex; align-items: center; justify-content: center; font-weight: 700;}
.canal {border-radius: 10px; padding: .9rem 1rem; font-weight: 500;}
.sidebar-foot {font-size: .8rem; opacity: .8; margin-top: 1rem;}
</style>
""",
    unsafe_allow_html=True,
)


def e(texto):
    return html.escape(str(texto)) if texto is not None else "-"


def encabezado(titulo, subtitulo):
    st.markdown(f'<div class="hero"><h1>{titulo}</h1><p>{subtitulo}</p></div>', unsafe_allow_html=True)


def badge(prioridad):
    return (f'<span class="badge" style="background:{FONDOS[prioridad]};color:{COLORES[prioridad]}">'
            f"{prioridad}</span>")


def kpis(items):
    cols = st.columns(len(items))
    for col, (valor, etiqueta, color) in zip(cols, items):
        col.markdown(f'<div class="kpi" style="--c:{color}"><div class="v">{valor}</div>'
                     f'<div class="l">{etiqueta}</div></div>', unsafe_allow_html=True)


def reporte_df():
    return pd.DataFrame(db.listar(con, db.SQL_REPORTE))


def estilo_tabla(df):
    """Colorea la prioridad y marca en rojo los signos vitales fuera de rango."""
    estilos = pd.DataFrame("", index=df.index, columns=df.columns)
    if "Prioridad" in df.columns:
        for p in COLORES:
            estilos.loc[df["Prioridad"] == p, "Prioridad"] = (
                f"background-color:{FONDOS[p]};color:{COLORES[p]};font-weight:600")
    for col, (bajo, alto) in db.RANGOS_NORMALES.items():
        etiqueta = ETIQUETAS[col]
        if etiqueta in df.columns:
            fuera = (df[etiqueta] < bajo) | (df[etiqueta] > alto)
            estilos.loc[fuera, etiqueta] = "background-color:#fee2e2;color:#b91c1c;font-weight:600"
    return estilos


def grafico_barras(serie, titulo, colores=None):
    datos = serie.rename_axis("categoria").reset_index(name="total")
    color = (alt.Color("categoria:N", scale=alt.Scale(domain=list(colores), range=list(colores.values())),
                       legend=None) if colores else alt.value("#0d9488"))
    chart = (alt.Chart(datos, title=titulo).mark_bar(cornerRadiusEnd=4)
             .encode(x=alt.X("total:Q", title=None, axis=alt.Axis(tickMinStep=1)),
                     y=alt.Y("categoria:N", title=None, sort="-x"), color=color,
                     tooltip=["categoria", "total"])
             .properties(height=180))
    st.altair_chart(chart, width="stretch")


# ------------------------------------------------------------------ paginas
def pagina_inicio():
    encabezado("Sistema de Comunicación de Reportes de Salud",
               "Puesto de salud rural (vereda en Colombia, batey o UNAP en República Dominicana) "
               "conectado con el hospital rural")
    df = reporte_df()
    activos = df[df["estado"] != "Atendido"] if len(df) else df
    kpis([
        (con.execute("SELECT COUNT(*) FROM Paciente").fetchone()[0], "Pacientes", "#1b365d"),
        (len(df), "Consultas", "#0d9488"),
        (int((activos["nivel_prioridad"] == "Alta").sum()) if len(df) else 0, "Prioridad alta sin atender", COLORES["Alta"]),
        (int((df["estado"] == "En cola (sin conexion)").sum()) if len(df) else 0, "En cola sin conexión", COLORES["Media"]),
    ])
    st.write("")
    izq, der = st.columns([3, 2], gap="large")
    with izq:
        st.markdown("#### Cómo funciona")
        pasos = [
            ("Registro", "El promotor de salud registra la identificación y procedencia del paciente."),
            ("Captura clínica", "Se toman los signos vitales con validación de rangos fisiológicos."),
            ("Triaje automático", "El sistema clasifica la prioridad en Alta, Media o Baja."),
            ("Comunicación", "Se elige el canal: sincrónico, asincrónico o cola sin conexión."),
            ("Atención médica", "El médico asigna diagnóstico CIE-10, observación y estado."),
        ]
        for i, (t, d) in enumerate(pasos, 1):
            st.markdown(f'<div class="step"><div class="num">{i}</div><div><b>{t}</b><br>'
                        f'<span class="muted">{d}</span></div></div>', unsafe_allow_html=True)
    with der:
        st.markdown("#### Canales de comunicación")
        st.markdown(
            f'<div class="card"><h4>Sincrónico</h4><span class="muted">Prioridad {badge("Alta")} con '
            'conexión: teleconsulta en tiempo real.</span></div>'
            f'<div class="card"><h4>Asincrónico</h4><span class="muted">Prioridad {badge("Media")} o '
            f'{badge("Baja")} con conexión: el reporte llega a la bandeja del hospital.</span></div>'
            '<div class="card"><h4>Sin conexión</h4><span class="muted">El reporte se guarda en el '
            'dispositivo y se envía al recuperar la señal.</span></div>',
            unsafe_allow_html=True,
        )


def pagina_registro():
    encabezado("Registro de pacientes", "Datos de identificación y procedencia del paciente")
    centros = db.listar(con, "SELECT id_centro, nombre_centro, municipio_vereda FROM CentroMedico")
    with st.form("form_paciente", clear_on_submit=True, border=True):
        c1, c2 = st.columns(2)
        id_paciente = c1.text_input("Documento / ID del paciente *", placeholder="Ej. CC-1234 o cédula RD")
        nombre = c2.text_input("Nombre completo *")
        e1, e2 = c1.columns(2)
        anios = e1.number_input("Edad (años) *", 0, 120, 25)
        meses = e2.number_input("Meses", 0, 11, 0)
        genero = c2.selectbox("Género *", ["M", "F", "Otro"],
                              format_func=lambda g: {"M": "Masculino", "F": "Femenino"}.get(g, g))
        procedencia = c1.text_input("Vereda / Municipio / Batey de procedencia *")
        centro = c2.selectbox("Centro de atención *", centros,
                              format_func=lambda c: f"{c['nombre_centro']} — {c['municipio_vereda']}")
        g1, g2 = c1.columns(2)
        grupo = g1.selectbox("Grupo sanguíneo", ["A", "B", "AB", "O"])
        rh = g2.selectbox("Factor RH", ["P", "N"], format_func=lambda x: "Positivo" if x == "P" else "Negativo")
        enviado = st.form_submit_button("Guardar paciente", type="primary", icon=":material/person_add:")
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
                st.success(f"Paciente {nombre.strip()} registrado correctamente.")
            except sqlite3.IntegrityError:
                st.error("Ya existe un paciente con ese documento.")

    st.markdown("#### Pacientes registrados")
    st.dataframe(pd.DataFrame(db.listar(con, """
        SELECT p.id_paciente AS ID, p.nombre AS Nombre, p.edad AS Edad, p.genero AS Genero,
               p.vereda_municipio AS Procedencia, p.grupo_sanguineo || p.factor_rh AS "Grupo/RH",
               c.nombre_centro AS Centro
        FROM Paciente p LEFT JOIN CentroMedico c ON c.id_centro = p.id_centro
        ORDER BY p.rowid DESC""")), hide_index=True, width="stretch")


def pagina_puesto():
    encabezado("Puesto de salud — Nueva consulta",
               "El promotor registra los signos vitales; el sistema clasifica y envía el reporte")
    pacientes = db.listar(con, "SELECT id_paciente, nombre, vereda_municipio FROM Paciente ORDER BY nombre")
    doctores = db.listar(con, "SELECT id_doctor, nombre_completo FROM Doctor")
    if not pacientes:
        st.info("Primero registre un paciente en el módulo Registro de pacientes.")
        return

    hay_conexion = st.toggle("Hay conexión a internet en el puesto de salud", value=True)
    with st.form("form_consulta", clear_on_submit=True, border=True):
        c1, c2 = st.columns(2)
        paciente = c1.selectbox("Paciente *", pacientes,
                                format_func=lambda p: f"{p['nombre']} ({p['id_paciente']}) — {p['vereda_municipio']}")
        doctor = c2.selectbox("Médico que recibe *", doctores, format_func=lambda d: d["nombre_completo"])
        motivo = st.text_input("Motivo de consulta *")
        st.markdown("**Signos vitales**")
        s1, s2, s3 = st.columns(3)
        fc = s1.number_input("Frecuencia cardíaca (lat/min)", 30, 220, 75)
        fr = s2.number_input("Frecuencia respiratoria (resp/min)", 5, 60, 16)
        spo2 = s3.number_input("Saturación SpO2 (%)", 50.0, 100.0, 97.0, step=1.0)
        pas = s1.number_input("Presión sistólica (mmHg)", 60, 250, 118)
        pad = s2.number_input("Presión diastólica (mmHg)", 30, 150, 76)
        p1, p2 = s3.columns([1, 2])
        tomo_ph = p1.checkbox("pH", help="Marque si se tomó la muestra de pH")
        ph = p2.number_input("Valor pH", 6.8, 7.8, 7.4, step=0.01, label_visibility="collapsed")
        enviado = st.form_submit_button("Registrar y enviar", type="primary", icon=":material/send:")

    if enviado:
        if not motivo.strip():
            st.error("Escriba el motivo de consulta.")
        elif pad >= pas:
            st.error("La presión diastólica debe ser menor que la sistólica.")
        else:
            id_c, prioridad, canal, _ = db.registrar_consulta(
                con, paciente["id_paciente"], doctor["id_doctor"], motivo.strip(), {
                    "frecuencia_cardiaca": fc, "frecuencia_respiratoria": fr,
                    "presion_sistolica": pas, "presion_diastolica": pad,
                    "spo2_porcentaje": spo2, "ph": ph if tomo_ph else None,
                }, hay_conexion)
            if canal.startswith("Sincronico"):
                texto, fondo = f"Canal sincrónico: conectando teleconsulta con {e(doctor['nombre_completo'])}.", "#fee2e2"
            elif canal.startswith("Asincronico"):
                texto, fondo = "Canal asincrónico: el reporte quedó en la bandeja del hospital.", "#dcfce7"
            else:
                texto, fondo = "Sin conexión: el reporte se guardó en el dispositivo y se enviará al recuperar la señal.", "#fef3c7"
                if prioridad == "Alta":
                    texto += " <b>URGENTE: remitir al paciente o comunicar por teléfono o radio.</b>"
            st.markdown(f'<div class="card"><h4>Consulta #{id_c} registrada &nbsp;{badge(prioridad)}</h4>'
                        f'<div class="canal" style="background:{fondo}">{texto}</div></div>',
                        unsafe_allow_html=True)

    en_cola = con.execute("SELECT COUNT(*) FROM ConsultaMedica WHERE estado = 'En cola (sin conexion)'").fetchone()[0]
    with st.container(border=True):
        a, b = st.columns([3, 1], vertical_alignment="center")
        a.markdown(f"**Cola sin conexión:** {en_cola} reporte(s) pendiente(s) de envío.")
        if b.button("Sincronizar", icon=":material/sync:", disabled=en_cola == 0 or not hay_conexion,
                    width="stretch"):
            n = db.sincronizar_pendientes(con)
            st.toast(f"{n} reporte(s) enviados al hospital.")
            st.rerun()


def pagina_hospital():
    encabezado("Hospital rural — Bandeja de reportes",
               "Reportes ordenados por prioridad; los signos vitales alterados se marcan en rojo")
    df = reporte_df()
    activos = df[df["estado"].isin(["Pendiente", "En atencion"])] if len(df) else df
    if activos.empty:
        st.info("No hay reportes pendientes.")
        return

    vista = pd.DataFrame({
        "#": activos["id_consulta"], "Prioridad": activos["nivel_prioridad"],
        "Paciente": activos["nombre"], "Edad": activos["edad"],
        "Procedencia": activos["vereda_municipio"], "Motivo": activos["motivo_consulta"],
        **{ETIQUETAS[c]: activos[c] for c in db.RANGOS_NORMALES},
        "Canal": activos["canal_comunicacion"], "Estado": activos["estado"],
    })
    st.dataframe(vista.style.apply(estilo_tabla, axis=None), hide_index=True, width="stretch")

    st.markdown("#### Atender reporte")
    opciones = activos.to_dict("records")
    sel = st.selectbox("Seleccione la consulta", opciones,
                       format_func=lambda r: f"#{r['id_consulta']} · {r['nivel_prioridad']} · {r['nombre']}")

    signos = [
        ("SpO2", f"{sel['spo2_porcentaje']:g} %", "spo2_porcentaje"),
        ("Presión", f"{sel['presion_sistolica']}/{sel['presion_diastolica']}", None),
        ("FC", f"{sel['frecuencia_cardiaca']} lat/min", "frecuencia_cardiaca"),
        ("FR", f"{sel['frecuencia_respiratoria']} resp/min", "frecuencia_respiratoria"),
    ]
    if pd.notna(sel["ph"]):
        signos.append(("pH", f"{sel['ph']:g}", None))

    def alterado(campo):
        if campo is None:
            bajo_s, alto_s = db.RANGOS_NORMALES["presion_sistolica"]
            bajo_d, alto_d = db.RANGOS_NORMALES["presion_diastolica"]
            return not (bajo_s <= sel["presion_sistolica"] <= alto_s and bajo_d <= sel["presion_diastolica"] <= alto_d)
        bajo, alto = db.RANGOS_NORMALES[campo]
        return not bajo <= sel[campo] <= alto

    tiles = "".join(
        f'<div class="vital{" alerta" if (n != "pH" and alterado(c)) else ""}"><div class="n">{n}</div>'
        f'<div class="x">{v}</div></div>' for n, v, c in signos)
    grupo = f"{sel['grupo_sanguineo'] or '-'}{sel['factor_rh'] or ''}"
    st.markdown(
        f'<div class="card"><h4>{e(sel["nombre"])} &nbsp;{badge(sel["nivel_prioridad"])}</h4>'
        f'<div class="muted">{e(sel["edad"])} · {e(sel["genero"])} · Grupo {e(grupo)} · '
        f'{e(sel["vereda_municipio"])} ({e(sel["nombre_centro"])})</div>'
        f'<div class="muted" style="margin-top:.3rem"><b>Motivo:</b> {e(sel["motivo_consulta"])} · '
        f'<b>Canal:</b> {e(sel["canal_comunicacion"])} · <b>Recibido:</b> {e(sel["fecha_hora"])}</div>'
        f'<div class="vitals">{tiles}</div></div>',
        unsafe_allow_html=True,
    )

    diagnosticos = db.listar(con, "SELECT id_diagnostico, codigo_cie10, nombre_enfermedad FROM DiagnosticoMedico ORDER BY codigo_cie10")
    with st.form("form_atencion", border=True):
        dx = st.selectbox("Diagnóstico (CIE-10)", diagnosticos,
                          format_func=lambda d: f"{d['codigo_cie10']} — {d['nombre_enfermedad']}")
        obs = st.text_area("Observación médica / indicaciones")
        estado = st.radio("Estado", ["En atencion", "Atendido"], horizontal=True, index=1,
                          format_func=lambda s: "En atención" if s == "En atencion" else s)
        if st.form_submit_button("Guardar y responder al puesto de salud", type="primary", icon=":material/check_circle:"):
            db.actualizar_consulta(con, int(sel["id_consulta"]), dx["id_diagnostico"], obs.strip(), estado)
            st.toast("Respuesta registrada y enviada al puesto de salud.")
            st.rerun()


def pagina_reportes():
    encabezado("Reportes", "Consulta, filtra y descarga los reportes de atención")
    df = reporte_df()
    if df.empty:
        st.info("Aún no hay consultas registradas.")
        return
    with st.container(border=True):
        f1, f2, f3 = st.columns(3)
        prioridades = f1.multiselect("Prioridad", ["Alta", "Media", "Baja"], default=["Alta", "Media", "Baja"])
        estados = f2.multiselect("Estado", db.ESTADOS, default=db.ESTADOS)
        texto = f3.text_input("Buscar paciente o procedencia")
    filtrado = df[df["nivel_prioridad"].isin(prioridades) & df["estado"].isin(estados)]
    if texto:
        filtrado = filtrado[filtrado["nombre"].str.contains(texto, case=False, regex=False)
                            | filtrado["vereda_municipio"].str.contains(texto, case=False, regex=False)]
    if filtrado.empty:
        st.info("No hay resultados con esos filtros.")
        return

    c1, c2, c3 = st.columns(3)
    with c1:
        grafico_barras(filtrado["nivel_prioridad"].value_counts(), "Por prioridad", COLORES)
    with c2:
        grafico_barras(filtrado["estado"].value_counts(), "Por estado")
    with c3:
        grafico_barras(filtrado["canal_comunicacion"].value_counts(), "Por canal")

    tabla = filtrado.rename(columns={**ETIQUETAS, "nivel_prioridad": "Prioridad", "id_consulta": "#",
                                     "fecha_hora": "Fecha", "nombre": "Paciente", "edad": "Edad",
                                     "vereda_municipio": "Procedencia", "motivo_consulta": "Motivo",
                                     "estado": "Estado", "canal_comunicacion": "Canal",
                                     "codigo_cie10": "CIE-10", "nombre_enfermedad": "Diagnóstico",
                                     "observaciones_evolucion": "Observación", "doctor": "Médico"})
    columnas = ["#", "Fecha", "Prioridad", "Paciente", "Edad", "Procedencia", "Motivo",
                *ETIQUETAS.values(), "Canal", "Estado", "CIE-10", "Diagnóstico", "Observación", "Médico"]
    tabla = tabla[columnas]
    st.dataframe(tabla.style.apply(estilo_tabla, axis=None), hide_index=True, width="stretch")
    st.download_button("Descargar CSV", filtrado.to_csv(index=False).encode("utf-8-sig"),
                       "reporte_salud_rural.csv", "text/csv", icon=":material/download:")


# ------------------------------------------------------------------ navegacion
paginas = {
    "General": [st.Page(pagina_inicio, title="Inicio", icon=":material/dashboard:", default=True)],
    "Atención": [
        st.Page(pagina_registro, title="Registro de pacientes", icon=":material/person_add:", url_path="registro"),
        st.Page(pagina_puesto, title="Puesto de salud", icon=":material/medical_services:", url_path="puesto"),
        st.Page(pagina_hospital, title="Hospital rural", icon=":material/local_hospital:", url_path="hospital"),
    ],
    "Análisis": [st.Page(pagina_reportes, title="Reportes", icon=":material/analytics:", url_path="reportes")],
}
navegacion = st.navigation(paginas)
st.sidebar.markdown(
    '<div class="sidebar-foot"><b>Salud Rural COIL</b><br>Ucompensar (Colombia)<br>'
    "Unicda (República Dominicana)<br>Grupo 6</div>",
    unsafe_allow_html=True,
)
navegacion.run()
