// =====================================================================
// PROYECTO COIL UCOMPENSAR (Colombia) - UNICDA (Rep. Dominicana)
// Actividad 3: Algoritmo del proceso de atencion y comunicacion
//              sincronica / asincronica entre puesto de salud y hospital
// Actores: Paciente | Promotor de salud (vereda/batey) | Sistema | Medico (hospital rural)
// =====================================================================

// Lee un valor numerico y lo repite hasta que este dentro del rango fisiologico
Funcion valor <- LeerValidado(mensaje, minimo, maximo)
	Definir valor Como Real
	Repetir
		Escribir mensaje, " [", minimo, " - ", maximo, "]: "
		Leer valor
		Si valor < minimo O valor > maximo Entonces
			Escribir "  Valor fuera de rango. Verifique la medicion."
		FinSi
	Hasta Que valor >= minimo Y valor <= maximo
FinFuncion

Algoritmo SistemaComunicacionSalud
	// ---------- Variables de identificacion ----------
	Definir nombre, genero, procedencia Como Caracter
	Definir edad Como Entero
	// ---------- Variables clinicas ----------
	Definir peso, talla, imc, fc, fr, pas, pad, spo2, ph Como Real
	Definir grupoSang, rh Como Caracter
	// ---------- Variables de reporte y seguimiento ----------
	Definir fechaReporte, horaReporte Como Entero
	Definir motivoConsulta, enfermedadCIE10, prioridad, observacionMedica Como Caracter
	// ---------- Variables de comunicacion ----------
	Definir hayConexion, reporteEnviado Como Logico
	Definir resp, canal Como Caracter

	// ===== 1. ACTOR: PROMOTOR DE SALUD - Registro del paciente =====
	Escribir "=== REGISTRO DEL PACIENTE (Puesto de salud) ==="
	Repetir
		Escribir "Nombre completo: "
		Leer nombre
	Hasta Que Longitud(nombre) > 0
	edad <- LeerValidado("Edad en anios", 0, 120)
	Repetir
		Escribir "Genero (M / F / O): "
		Leer genero
		genero <- Mayusculas(genero)
	Hasta Que genero = "M" O genero = "F" O genero = "O"
	Escribir "Vereda / Provincia / Batey de procedencia: "
	Leer procedencia

	// ===== 2. ACTOR: PROMOTOR DE SALUD - Captura de signos vitales =====
	Escribir "=== CAPTURA DE DATOS CLINICOS ==="
	peso  <- LeerValidado("Peso (kg)", 2, 300)
	talla <- LeerValidado("Talla (cm)", 40, 250)
	fc    <- LeerValidado("Frecuencia cardiaca (lat/min)", 30, 220)
	fr    <- LeerValidado("Frecuencia respiratoria (resp/min)", 5, 60)
	pas   <- LeerValidado("Presion sistolica (mmHg)", 60, 250)
	pad   <- LeerValidado("Presion diastolica (mmHg)", 30, 150)
	spo2  <- LeerValidado("Saturacion de oxigeno SpO2 (%)", 50, 100)
	Escribir "Se tomo pH sanguineo? (S/N): "
	Leer resp
	Si Mayusculas(resp) = "S" Entonces
		ph <- LeerValidado("pH", 6.8, 7.8)
	SiNo
		ph <- 0   // campo condicional: 0 = no registrado
	FinSi
	Repetir
		Escribir "Grupo sanguineo (A / B / AB / O): "
		Leer grupoSang
		grupoSang <- Mayusculas(grupoSang)
	Hasta Que grupoSang = "A" O grupoSang = "B" O grupoSang = "AB" O grupoSang = "O"
	Repetir
		Escribir "Factor RH (P / N): "
		Leer rh
		rh <- Mayusculas(rh)
	Hasta Que rh = "P" O rh = "N"
	Escribir "Motivo de consulta: "
	Leer motivoConsulta

	// ===== 3. ACTOR: SISTEMA - Procesamiento automatico =====
	imc <- peso / ((talla / 100) ^ 2)
	imc <- Redon(imc * 100) / 100   // redondeo a 2 decimales
	fechaReporte <- FechaActual()
	horaReporte  <- HoraActual()

	// Triaje por reglas (prioridad Alta / Media / Baja)
	Si spo2 < 90 O pas >= 180 O pad >= 120 O fc > 120 O fc < 40 O fr > 30 Entonces
		prioridad <- "ALTA"
	SiNo
		Si spo2 <= 94 O pas >= 140 O pad >= 90 O fc > 100 O fc < 50 O fr > 24 Entonces
			prioridad <- "MEDIA"
		SiNo
			prioridad <- "BAJA"
		FinSi
	FinSi

	// ===== 4. ACTOR: SISTEMA - Decision del canal de comunicacion =====
	Escribir "Hay conexion a internet en el puesto de salud? (S/N): "
	Leer resp
	Si Mayusculas(resp) = "S" Entonces
		hayConexion <- Verdadero
	SiNo
		hayConexion <- Falso
	FinSi

	Si hayConexion Y prioridad = "ALTA" Entonces
		canal <- "SINCRONICO"      // teleconsulta en tiempo real
	SiNo
		Si hayConexion Entonces
			canal <- "ASINCRONICO"  // envio inmediato del reporte, respuesta diferida
		SiNo
			canal <- "OFFLINE"      // se guarda localmente y se envia al recuperar senal
		FinSi
	FinSi

	Segun canal Hacer
		"SINCRONICO":
			Escribir ">> ALERTA: Prioridad ALTA. Conectando teleconsulta con el medico..."
			reporteEnviado <- Verdadero
		"ASINCRONICO":
			Escribir ">> Reporte enviado al hospital rural. Quedara en cola por prioridad."
			reporteEnviado <- Verdadero
		De Otro Modo:
			Escribir ">> Sin conexion. Reporte guardado en el dispositivo (cola pendiente)."
			reporteEnviado <- Falso
			Si prioridad = "ALTA" Entonces
				Escribir ">> URGENTE: remitir paciente / comunicar por telefono o radio."
			FinSi
			Repetir
				Escribir "Se recupero la conexion? (S/N): "
				Leer resp
			Hasta Que Mayusculas(resp) = "S"
			Escribir ">> Sincronizando reporte pendiente con el hospital..."
			reporteEnviado <- Verdadero
	FinSegun

	Si reporteEnviado Entonces
		// ===== 5. ACTOR: MEDICO (hospital rural) - Recepcion y respuesta =====
		Escribir "=========== REPORTE RECIBIDO EN HOSPITAL ==========="
		Escribir "Prioridad: ", prioridad, "   Canal: ", canal
		Escribir "Fecha: ", fechaReporte, "   Hora: ", horaReporte
		Escribir "Paciente: ", nombre, " | ", edad, " anios | ", genero, " | ", procedencia
		Escribir "SpO2: ", spo2, " %   PA: ", pas, "/", pad, " mmHg"
		Escribir "FC: ", fc, " lat/min   FR: ", fr, " resp/min"
		Escribir "IMC: ", imc, "   Grupo: ", grupoSang, " ", rh
		Si ph > 0 Entonces
			Escribir "pH: ", ph
		FinSi
		Escribir "Motivo: ", motivoConsulta
		Escribir "===================================================="
		Escribir "Medico - Enfermedad de seguimiento (CIE-10): "
		Leer enfermedadCIE10
		Escribir "Medico - Observacion / indicaciones: "
		Leer observacionMedica

		// ===== 6. ACTOR: PACIENTE - Recibe la respuesta =====
		Escribir ">> Respuesta enviada al puesto de salud para el paciente ", nombre, ":"
		Escribir "   Diagnostico: ", enfermedadCIE10
		Escribir "   Indicaciones: ", observacionMedica
	FinSi
FinAlgoritmo
