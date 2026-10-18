"""Capa de datos del prototipo (SQLite) y reglas clinicas.

Usa el esquema de la Actividad 4 (data/esquema.sql). Si la base no existe,
la crea y carga datos de demostracion para que la demo nunca arranque vacia.
"""
import sqlite3
from pathlib import Path

BASE = Path(__file__).parent / "data"
DB_PATH = BASE / "PROYECTO_COIL_GRUPO6.db"
SCHEMA_PATH = BASE / "esquema.sql"

ESTADOS = ["En cola (sin conexion)", "Pendiente", "En atencion", "Atendido"]

# Columnas que aparecen en el modelo E-R pero no estaban en el .sql
COLUMNAS_EXTRA = {
    "Paciente": [("grupo_sanguineo", "TEXT"), ("factor_rh", "TEXT")],
    "ConsultaMedica": [("estado", "TEXT DEFAULT 'Pendiente'"), ("canal_comunicacion", "TEXT")],
}


def conectar():
    con = sqlite3.connect(DB_PATH, check_same_thread=False)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con


def inicializar():
    BASE.mkdir(exist_ok=True)
    con = conectar()
    con.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    for tabla, columnas in COLUMNAS_EXTRA.items():
        existentes = {r["name"] for r in con.execute(f'PRAGMA table_info("{tabla}")')}
        for nombre, tipo in columnas:
            if nombre not in existentes:
                con.execute(f'ALTER TABLE "{tabla}" ADD COLUMN "{nombre}" {tipo}')
    if con.execute("SELECT COUNT(*) FROM CentroMedico").fetchone()[0] == 0:
        _cargar_demo(con)
    con.commit()
    return con


# ---------------------------------------------------------------- reglas
def clasificar_prioridad(fc, fr, pas, pad, spo2):
    """Triaje por reglas (mismo criterio del pseudocodigo de la Actividad 3)."""
    if spo2 < 90 or pas >= 180 or pad >= 120 or fc > 120 or fc < 40 or fr > 30:
        return "Alta"
    if spo2 <= 94 or pas >= 140 or pad >= 90 or fc > 100 or fc < 50 or fr > 24:
        return "Media"
    return "Baja"


def decidir_canal(prioridad, hay_conexion):
    if not hay_conexion:
        return "Offline (envio diferido)"
    return "Sincronico (teleconsulta)" if prioridad == "Alta" else "Asincronico (reporte)"


RANGOS_NORMALES = {  # fuera de estos rangos el valor se resalta en rojo
    "frecuencia_cardiaca": (60, 100),
    "frecuencia_respiratoria": (12, 20),
    "presion_sistolica": (90, 139),
    "presion_diastolica": (60, 89),
    "spo2_porcentaje": (95, 100),
}


# ---------------------------------------------------------------- consultas
def listar(con, sql, params=()):
    return [dict(r) for r in con.execute(sql, params)]


def registrar_paciente(con, d):
    con.execute(
        """INSERT INTO Paciente (id_paciente, nombre, edad, genero, vereda_municipio,
               id_centro, grupo_sanguineo, factor_rh)
           VALUES (:id_paciente, :nombre, :edad, :genero, :vereda_municipio,
               :id_centro, :grupo_sanguineo, :factor_rh)""",
        d,
    )
    con.commit()


def registrar_consulta(con, id_paciente, id_doctor, motivo, signos, hay_conexion):
    prioridad = clasificar_prioridad(
        signos["frecuencia_cardiaca"], signos["frecuencia_respiratoria"],
        signos["presion_sistolica"], signos["presion_diastolica"], signos["spo2_porcentaje"],
    )
    canal = decidir_canal(prioridad, hay_conexion)
    estado = "Pendiente" if hay_conexion else "En cola (sin conexion)"
    cur = con.execute(
        """INSERT INTO ConsultaMedica (id_paciente, id_doctor, fecha_hora, motivo_consulta,
               nivel_prioridad, estado, canal_comunicacion)
           VALUES (?, ?, datetime('now', 'localtime'), ?, ?, ?, ?)""",
        (id_paciente, id_doctor, motivo, prioridad, estado, canal),
    )
    id_consulta = cur.lastrowid
    con.execute(
        """INSERT INTO SignosVitales (id_paciente, id_consulta, frecuencia_cardiaca,
               frecuencia_respiratoria, presion_sistolica, presion_diastolica,
               spo2_porcentaje, ph, fecha_medicion)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now', 'localtime'))""",
        (id_paciente, id_consulta, signos["frecuencia_cardiaca"], signos["frecuencia_respiratoria"],
         signos["presion_sistolica"], signos["presion_diastolica"],
         signos["spo2_porcentaje"], signos["ph"]),
    )
    con.commit()
    return id_consulta, prioridad, canal, estado


def sincronizar_pendientes(con):
    """Simula la recuperacion de la senal: envia al hospital lo que estaba en cola."""
    n = con.execute(
        """UPDATE ConsultaMedica
           SET estado = 'Pendiente',
               canal_comunicacion = CASE nivel_prioridad WHEN 'Alta'
                   THEN 'Sincronico (teleconsulta)' ELSE 'Asincronico (reporte)' END
           WHERE estado = 'En cola (sin conexion)'"""
    ).rowcount
    con.commit()
    return n


def actualizar_consulta(con, id_consulta, id_diagnostico, observacion, estado):
    con.execute(
        """UPDATE ConsultaMedica SET id_diagnostico = ?, observaciones_evolucion = ?, estado = ?
           WHERE id_consulta = ?""",
        (id_diagnostico, observacion, estado, id_consulta),
    )
    con.commit()


SQL_REPORTE = """
SELECT c.id_consulta, c.fecha_hora, c.nivel_prioridad, c.estado, c.canal_comunicacion,
       c.motivo_consulta, c.observaciones_evolucion,
       p.id_paciente, p.nombre, p.edad, p.genero, p.vereda_municipio,
       p.grupo_sanguineo, p.factor_rh,
       s.frecuencia_cardiaca, s.frecuencia_respiratoria, s.presion_sistolica,
       s.presion_diastolica, s.spo2_porcentaje, s.ph,
       d.nombre_completo AS doctor, cm.nombre_centro,
       dg.codigo_cie10, dg.nombre_enfermedad
FROM ConsultaMedica c
JOIN Paciente p ON p.id_paciente = c.id_paciente
JOIN Doctor d ON d.id_doctor = c.id_doctor
LEFT JOIN CentroMedico cm ON cm.id_centro = p.id_centro
LEFT JOIN SignosVitales s ON s.id_consulta = c.id_consulta
LEFT JOIN DiagnosticoMedico dg ON dg.id_diagnostico = c.id_diagnostico
ORDER BY CASE c.nivel_prioridad WHEN 'Alta' THEN 1 WHEN 'Media' THEN 2 ELSE 3 END,
         c.fecha_hora DESC
"""


# ---------------------------------------------------------------- demo
def _cargar_demo(con):
    con.executemany(
        """INSERT INTO CentroMedico (nombre_centro, nit, direccion, municipio_vereda,
               telefono_contacto, tipo_institucion) VALUES (?, ?, ?, ?, ?, ?)""",
        [
            ("Puesto de Salud Vereda El Rosal", "900123456-1", "Km 12 via Facatativa",
             "Vereda El Rosal, Cundinamarca (CO)", "+57 601 555 0101", "Puesto de salud rural"),
            ("UNAP Batey Central", "RNC-401234567", "Calle Principal s/n",
             "Batey Central, Barahona (RD)", "+1 809 555 0102", "Unidad de Atencion Primaria"),
            ("Hospital Rural Regional", "900987654-2", "Cra 5 # 10-20",
             "Cabecera municipal", "+57 601 555 0199", "Hospital rural"),
        ],
    )
    con.executemany(
        "INSERT INTO Doctor VALUES (?, ?, ?, ?, ?, ?)",
        [
            ("DOC-001", "Dra. Laura Mendez", "Medicina general", "RM-10234", "laura.mendez@demo.org", 3),
            ("DOC-002", "Dr. Jose Peralta", "Medicina interna", "EXQ-55821", "jose.peralta@demo.org", 3),
        ],
    )
    con.executemany(
        "INSERT INTO DiagnosticoMedico (codigo_cie10, nombre_enfermedad, descripcion_clinica) VALUES (?, ?, ?)",
        [
            ("I10", "Hipertension esencial (primaria)", "Presion arterial elevada sostenida"),
            ("J06.9", "Infeccion aguda de vias respiratorias superiores", "Cuadro respiratorio leve"),
            ("J18.9", "Neumonia, no especificada", "Infeccion pulmonar"),
            ("J96.0", "Insuficiencia respiratoria aguda", "Hipoxemia, requiere oxigeno"),
            ("E11.9", "Diabetes mellitus tipo 2 sin complicaciones", "Control metabolico"),
            ("A90", "Fiebre del dengue", "Sindrome febril en zona endemica"),
            ("Z00.0", "Examen medico general", "Control de rutina"),
        ],
    )
    # Pacientes de prueba tomados de la muestra de estudiantes (Actividad 2)
    pacientes = [
        ("CC-1001", "Paciente Demo A", "34A 9M", "M", "Vereda El Rosal", 1, "O", "P"),
        ("CC-1002", "Paciente Demo B", "21A 5M", "M", "Vereda El Rosal", 1, "A", "P"),
        ("RD-2001", "Paciente Demo C", "19A 8M", "F", "Batey Central", 2, "O", "P"),
        ("RD-2002", "Paciente Demo D", "17A 6M", "F", "Batey Central", 2, "A", "N"),
    ]
    con.executemany("INSERT INTO Paciente VALUES (?, ?, ?, ?, ?, ?, ?, ?)", pacientes)
    casos = [  # paciente, doctor, motivo, fc, fr, pas, pad, spo2, conexion
        ("CC-1001", "DOC-001", "Control general", 75, 16, 117, 81, 95, True),
        ("CC-1002", "DOC-001", "Cefalea y mareo", 90, 18, 150, 98, 97, True),
        ("RD-2001", "DOC-002", "Dificultad para respirar", 125, 32, 100, 65, 86, True),
        ("RD-2002", "DOC-002", "Fiebre de 3 dias", 98, 20, 99, 65, 96, False),
    ]
    for pid, did, motivo, fc, fr, pas, pad, spo2, conexion in casos:
        registrar_consulta(con, pid, did, motivo, {
            "frecuencia_cardiaca": fc, "frecuencia_respiratoria": fr, "presion_sistolica": pas,
            "presion_diastolica": pad, "spo2_porcentaje": spo2, "ph": None,
        }, conexion)
