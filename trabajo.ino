/*
  ================================================================
   SIMA — Sistema Inteligente de Monitoreo Ambiental
   Firmware Arduino v1.0
  ================================================================

   Descripción:
     Firmware del nodo sensor para el sistema SIMA. Lee temperatura
     y humedad del sensor DHT11 y transmite los datos por puerto
     serial en formato CSV estandarizado.

   Protocolo de comunicación:
     - Líneas de DATOS:    "valor1,valor2\n"       → Ej: "25.3,62.0"
     - Líneas de CONTROL:  "#CLAVE:valor\n"        → Ej: "#SIMA:v1"
     - Líneas de ERROR:    "#ERROR:descripción\n"   → Ej: "#ERROR:DHT11"
     - Líneas de ESTADO:   "#STATUS:estado\n"       → Ej: "#STATUS:READY"

     Python distingue datos de control verificando si la línea
     comienza con '#'.

   Hardware actual:
     - Arduino UNO
     - Sensor DHT11 en pin digital 4
     - Conexión USB Serial a 9600 baudios

   Hardware futuro (sin cambiar arquitectura):
     - MQ135, MQ2, MQ7  (calidad del aire)
     - CCS811            (CO₂ + VOC)
     - BME680            (temp + hum + presión + gas)
     - Sensores PM2.5 / PM10

   Cuando se agreguen sensores, simplemente se añaden más campos
   al CSV: "25.3,62.0,412,0.8,15,22\n"
   Y se actualiza la cabecera del protocolo:
   "#SIMA:v2:TEMP,HUM,CO2,VOC,PM25,PM10"

   Conexión del sensor DHT11 (módulo de 3 pines):
     VCC  (+)  → 5V del Arduino
     GND  (-)  → GND del Arduino
     DATA (S)  → Pin digital 4

   Si usas el sensor DHT11 de 4 pines (sin módulo), coloca
   una resistencia pull-up de 10kΩ entre DATA y VCC.

   Autor:  Equipo SIMA
   Fecha:  2026-07-14
  ================================================================
*/

// ===================== LIBRERÍAS =====================
#include <DHT.h>              // Librería Adafruit para sensores DHT
#include <Adafruit_Sensor.h>  // Librería base requerida por DHT.h

// ===================== CONFIGURACIÓN DE HARDWARE =====================

// --- Sensor DHT11 ---
#define DHTPIN   4        // Pin digital de datos del DHT11
#define DHTTYPE  DHT11    // Tipo de sensor (DHT11, DHT21 o DHT22)

// --- Sensor de Luz (LDR) ---
#define LIGHTPIN A0       // Pin analógico de lectura de fotorresistencia LDR

// --- Comunicación serial ---
#define SERIAL_BAUD  9600  // Velocidad del puerto serial (baudios)

// --- Temporización ---
// El DHT11 requiere mínimo 2 segundos entre lecturas.
// Usamos millis() en lugar de delay() para no bloquear el procesador,
// permitiendo agregar tareas adicionales en el futuro.
const unsigned long INTERVALO_LECTURA = 2000;  // ms

// --- Protocolo ---
// Versión del protocolo SIMA. Se incrementa al agregar sensores.
// Formato de la cabecera: #SIMA:version:CAMPO1,CAMPO2,...
#define PROTOCOLO_VERSION  "v2"
#define PROTOCOLO_CAMPOS   "TEMP,HUM,LIGHT"

// ===================== CONSTANTES DE ESTABILIDAD =====================

// Número máximo de errores consecutivos antes de emitir una alerta
// crítica. Ayuda a detectar cables sueltos o sensor dañado.
const byte MAX_ERRORES_CONSECUTIVOS = 5;

// Número de lecturas iniciales a descartar. Los primeros valores
// del DHT11 suelen ser inestables o NaN tras el encendido.
const byte LECTURAS_DESCARTE = 2;

// ===================== OBJETOS GLOBALES =====================

// Instancia del sensor DHT11
DHT dht(DHTPIN, DHTTYPE);

// ===================== VARIABLES DE ESTADO =====================

unsigned long ultimaLectura    = 0;     // Timestamp de la última lectura exitosa
byte erroresConsecutivos       = 0;     // Contador de errores seguidos
byte lecturasRealizadas        = 0;     // Contador de lecturas totales (para descarte inicial)
bool sensorEstable             = false; // Indica si ya pasó el periodo de estabilización

// ===================== SETUP =====================
void setup() {
  // --- Inicializar comunicación serial ---
  Serial.begin(SERIAL_BAUD);

  // Esperar a que el puerto serial esté listo.
  // Necesario en algunas placas (Leonardo, Micro). En UNO no es
  // estrictamente necesario, pero es buena práctica.
  while (!Serial) {
    ; // Espera activa
  }

  // --- Inicializar sensor ---
  dht.begin();

  // --- Configurar LED integrado como indicador visual ---
  // LED encendido = error de lectura
  // LED apagado   = funcionamiento normal
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, LOW);

  // --- Enviar cabecera del protocolo ---
  // Python usa esta línea para identificar el dispositivo y
  // conocer los campos que recibirá.
  enviarCabecera();

  // --- Señalar que el sistema está listo ---
  enviarEstado(F("READY"));
}

// ===================== LOOP PRINCIPAL =====================
void loop() {
  // Usamos millis() en lugar de delay() para temporización
  // no bloqueante. Esto permite agregar otras tareas en el
  // loop sin afectar el timing de las lecturas.
  unsigned long ahora = millis();

  if (ahora - ultimaLectura < INTERVALO_LECTURA) {
    return;  // Aún no es momento de leer
  }

  ultimaLectura = ahora;

  // --- Leer sensores ---
  float temperatura = dht.readTemperature(false);  // false = Celsius
  float humedad     = dht.readHumidity();
  int ldrRaw        = analogRead(LIGHTPIN);          // Lectura analógica LDR (0-1023)
  float luz         = map(ldrRaw, 0, 1023, 0, 1000); // Mapeo aproximado a Lux (0-1000 Lux)

  // --- Validar lectura ---
  if (isnan(temperatura) || isnan(humedad)) {
    manejarError();
    return;
  }

  // --- Lectura exitosa ---
  erroresConsecutivos = 0;
  digitalWrite(LED_BUILTIN, LOW);

  // --- Periodo de estabilización ---
  // Descartamos las primeras lecturas para evitar datos basura
  lecturasRealizadas++;
  if (lecturasRealizadas <= LECTURAS_DESCARTE) {
    enviarEstado(F("STABILIZING"));
    return;
  }

  if (!sensorEstable) {
    sensorEstable = true;
    enviarEstado(F("STABLE"));
  }

  // --- Enviar datos en formato CSV ---
  enviarDatos(temperatura, humedad, luz);
}

// ===================== FUNCIONES DE PROTOCOLO =====================

/**
 * Envía la cabecera del protocolo SIMA.
 * Formato: #SIMA:version:CAMPO1,CAMPO2,...
 *
 * Python usa esta información para configurar dinámicamente
 * el parser de datos según la versión del firmware.
 */
void enviarCabecera() {
  Serial.print(F("#SIMA:"));
  Serial.print(F(PROTOCOLO_VERSION));
  Serial.print(F(":"));
  Serial.println(F(PROTOCOLO_CAMPOS));
}

/**
 * Envía una línea de datos en formato CSV.
 * Formato: valor1,valor2,valor3\n
 *
 * @param temperatura  Temperatura en °C
 * @param humedad      Humedad relativa en %
 * @param luz          Luminosidad en Lux
 */
void enviarDatos(float temperatura, float humedad, float luz) {
  Serial.print(temperatura, 1);
  Serial.print(F(","));
  Serial.print(humedad, 1);
  Serial.print(F(","));
  Serial.println(luz, 1);
}

/**
 * Envía un mensaje de estado.
 * Formato: #STATUS:estado\n
 *
 * Estados posibles:
 *   READY        - Sistema iniciado correctamente
 *   STABILIZING  - Descartando lecturas iniciales
 *   STABLE       - Sensor estabilizado, datos confiables
 *
 * @param estado  Texto del estado (usar F() para ahorrar RAM)
 */
void enviarEstado(const __FlashStringHelper* estado) {
  Serial.print(F("#STATUS:"));
  Serial.println(estado);
}

/**
 * Envía un mensaje de error.
 * Formato: #ERROR:descripción\n
 *
 * @param error  Texto descriptivo del error (usar F() para ahorrar RAM)
 */
void enviarError(const __FlashStringHelper* error) {
  Serial.print(F("#ERROR:"));
  Serial.println(error);
}

// ===================== FUNCIONES DE MANEJO DE ERRORES =====================

/**
 * Maneja un error de lectura del sensor.
 *
 * - Incrementa el contador de errores consecutivos.
 * - Enciende el LED integrado como indicador visual.
 * - Envía el error por serial.
 * - Si se superan MAX_ERRORES_CONSECUTIVOS, envía una alerta
 *   crítica indicando posible problema de hardware.
 */
void manejarError() {
  erroresConsecutivos++;
  digitalWrite(LED_BUILTIN, HIGH);

  enviarError(F("DHT11_READ_FAIL"));

  if (erroresConsecutivos >= MAX_ERRORES_CONSECUTIVOS) {
    enviarError(F("DHT11_CHECK_WIRING"));
    // Reiniciar contador para no saturar el serial
    erroresConsecutivos = 0;
  }
}