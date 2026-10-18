BEGIN TRANSACTION;
CREATE TABLE IF NOT EXISTS "CentroMedico" (
	"id_centro"	INTEGER,
	"nombre_centro"	TEXT NOT NULL,
	"nit"	TEXT NOT NULL UNIQUE,
	"direccion"	TEXT NOT NULL,
	"municipio_vereda"	TEXT NOT NULL,
	"telefono_contacto"	TEXT,
	"tipo_institucion"	TEXT,
	PRIMARY KEY("id_centro" AUTOINCREMENT)
);
CREATE TABLE IF NOT EXISTS "ConsultaMedica" (
	"id_consulta"	INTEGER,
	"id_paciente"	TEXT NOT NULL,
	"id_doctor"	TEXT NOT NULL,
	"id_diagnostico"	INTEGER,
	"fecha_hora"	TEXT DEFAULT CURRENT_TIMESTAMP,
	"motivo_consulta"	TEXT NOT NULL,
	"observaciones_evolucion"	TEXT,
	"nivel_prioridad"	TEXT CHECK("nivel_prioridad" IN ('Alta', 'Media', 'Baja')),
	PRIMARY KEY("id_consulta" AUTOINCREMENT),
	FOREIGN KEY("id_diagnostico") REFERENCES "DiagnosticoMedico"("id_diagnostico"),
	FOREIGN KEY("id_doctor") REFERENCES "Doctor"("id_doctor"),
	FOREIGN KEY("id_paciente") REFERENCES "Paciente"("id_paciente")
);
CREATE TABLE IF NOT EXISTS "DiagnosticoMedico" (
	"id_diagnostico"	INTEGER,
	"codigo_cie10"	TEXT NOT NULL UNIQUE,
	"nombre_enfermedad"	TEXT NOT NULL,
	"descripcion_clinica"	TEXT,
	PRIMARY KEY("id_diagnostico" AUTOINCREMENT)
);
CREATE TABLE IF NOT EXISTS "Doctor" (
	"id_doctor"	TEXT,
	"nombre_completo"	TEXT NOT NULL,
	"especialidad"	TEXT,
	"registro_medico"	TEXT NOT NULL UNIQUE,
	"contacto"	TEXT,
	"id_centro"	INTEGER,
	PRIMARY KEY("id_doctor"),
	FOREIGN KEY("id_centro") REFERENCES "CentroMedico"("id_centro")
);
CREATE TABLE IF NOT EXISTS "Paciente" (
	"id_paciente"	TEXT,
	"nombre"	TEXT NOT NULL,
	"edad"	TEXT NOT NULL,
	"genero"	TEXT CHECK("genero" IN ('M', 'F', 'Otro')),
	"vereda_municipio"	TEXT NOT NULL,
	"id_centro"	INTEGER,
	PRIMARY KEY("id_paciente"),
	FOREIGN KEY("id_centro") REFERENCES "CentroMedico"("id_centro")
);
CREATE TABLE IF NOT EXISTS "SignosVitales" (
	"id_signo"	INTEGER,
	"id_paciente"	TEXT NOT NULL,
	"id_consulta"	INTEGER,
	"frecuencia_cardiaca"	INTEGER NOT NULL,
	"frecuencia_respiratoria"	INTEGER NOT NULL,
	"presion_sistolica"	INTEGER NOT NULL,
	"presion_diastolica"	INTEGER NOT NULL,
	"spo2_porcentaje"	REAL,
	"ph"	REAL,
	"fecha_medicion"	TEXT DEFAULT CURRENT_TIMESTAMP,
	PRIMARY KEY("id_signo" AUTOINCREMENT),
	FOREIGN KEY("id_consulta") REFERENCES "ConsultaMedica"("id_consulta"),
	FOREIGN KEY("id_paciente") REFERENCES "Paciente"("id_paciente")
);
COMMIT;
