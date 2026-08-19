# 🛰️ SIMA — Arquitectura del Sistema, Esquema de Comunicación y Diagramas de Flujo

> **Sistema Inteligente de Monitoreo Ambiental (SIMA)**  
> Documento de Especificación Técnica de Arquitectura, Flujo de Datos y Protocolos de Comunicación.

---

## 📋 Tabla de Contenidos
1. [Visión General de la Arquitectura de Capas](#1-visión-general-de-la-arquitectura-de-capas)
2. [Esquema Integral del Sistema Completo (Bloques y Conexiones)](#2-esquema-integral-del-sistema-completo-bloques-y-conexiones)
3. [Diagramas de Flujo del Sistema (Mermaid)](#3-diagramas-de-flujo-del-sistema-mermaid)
   - [3.1 Diagrama de Flujo General End-to-End (E2E)](#31-diagrama-de-flujo-general-end-to-end-e2e)
   - [3.2 Diagrama de Secuencia de Comunicación Hardware ↔ Software](#32-diagrama-de-secuencia-de-comunicación-hardware--software)
   - [3.3 Diagrama de Flujo del Motor de Clasificación e Índice de Confort](#33-diagrama-de-flujo-del-motor-de-clasificación-e-índice-de-confort)
   - [3.4 Diagrama de Arquitectura Multihilo (QThread vs Qt GUI Loop)](#34-diagrama-de-arquitectura-multihilo-qthread-vs-qt-gui-loop)
   - [3.5 Diagrama de Flujo de Exportación (PDF y Excel)](#35-diagrama-de-flujo-de-exportación-pdf-y-excel)
4. [Especificación del Protocolo de Comunicación SIMA](#4-especificación-del-protocolo-de-comunicación-sima)
5. [Desglose Componente por Componente](#5-desglose-componente-por-componente)
6. [Esquema Electrónico de Conexiones Hardware](#6-esquema-electrónico-de-conexiones-hardware)

---

## 1. Visión General de la Arquitectura de Capas

El proyecto **SIMA** está diseñado bajo un patrón de **Arquitectura Desacoplada por Capas (Layered Architecture)** combinado con el patrón de diseño **MVVM (Model-View-ViewModel)** orientado a eventos en el cliente Python.

```
+-----------------------------------------------------------------------+
|                       1. CAPA DE HARDWARE / SENSORES                  |
|          [DHT11 Temp/Hum]        [LDR Fotorresistencia Lux]           |
+-----------------------------------++----------------------------------+
                                    || (Señales Analógicas / Digitales)
                                    v
+-----------------------------------------------------------------------+
|                      2. CAPA DE FIRMWARE (ARDUINO UNO)                |
|       Lectura no bloqueante (millis) -> Formateador CSV / Protocolo    |
+-----------------------------------++----------------------------------+
                                    || (USB / UART Serial @ 9600 Baud)
                                    v
+-----------------------------------------------------------------------+
|                 3. CAPA DE ADQUISICIÓN SERIAL (QThread)               |
|      SerialReader QThread -> Parseo defensivo -> Emisión de Signals   |
+-----------------------------------++----------------------------------+
                                    || (Qt Signals: new_data, status)
                                    v
+-----------------------------------------------------------------------+
|               4. CAPA DE MODELO Y CLASIFICACIÓN (MVVM Model)          |
|   SensorManager (Buffer Circular) | EnvironmentalClassifier | Stats    |
+-----------------------------------++----------------------------------+
                                    || (Actualización del Estado)
                                    v
+-----------------------------------------------------------------------+
|                 5. CAPA DE PRESENTACIÓN / GUI (PySide6)               |
|   MainWindow | DashboardWidget | Gauges | Cards | pyqtgraph Charts    |
+-----------------------------------++----------------------------------+
                                    || (Acción del Usuario: Exportar)
                                    v
+-----------------------------------------------------------------------+
|                 6. CAPA DE PERSISTENCIA Y REPORTES                    |
|       ExcelManager (openpyxl)     |      PDFManager (ReportLab)       |
+-----------------------------------------------------------------------+
```

---

## 2. Esquema Integral del Sistema Completo (Bloques y Conexiones)

El siguiente esquema en ASCII representa la totalidad de las interacciones, componentes y flujos de información del sistema SIMA:

```
========================================================================================================================
                                       ESQUEMA GENERAL DEL SISTEMA SIMA
========================================================================================================================

 HARDWARE (NODO EMISOR)                         PC HOST (APLICACIÓN PYTHON PYSIDE6)
+------------------------+                     +-----------------------------------------------------------------------+
|  ENTORNO AMBIENTAL     |                     |                                                                       |
| (Temperatura, Humedad, |                     |  +-----------------------------------------------------------------+  |
|      Luminosidad)      |                     |  |                    MAIN THREAD (Qt Event Loop)                  |  |
+-----------+------------+                     |  |                                                                 |  |
            |                                  |  |  +-----------------------------------------------------------+  |  |
            v                                  |  |  |                    gui/mainwindow.py                      |  |  |
+------------------------+                     |  |  |   - Orquestador del ciclo de vida                            |  |  |
|  SENSORES FISICOS      |                     |  |  |   - Captura señales de SerialReader via Slots Qt          |  |  |
|  - DHT11 (Pin D4)      |                     |  |  +-----------------------------+-----------------------------+  |  |
|  - LDR (Pin A0)        |                     |  |                                |                                |  |
+-----------+------------+                     |  |                                v                                |  |
            | Lecturas                         |  |  +-----------------------------------------------------------+  |  |
            v                                  |  |  |                   gui/dashboard.py                        |  |  |
+------------------------+                     |  |  |  - DashboardWidget (Contenedor Principal)                |  |  |
|  ARDUINO UNO (ATmega)  |                     |  |  |  - Cards (Tarjetas de métricas rápidas)                   |  |  |
|  firmware: trabajo.ino |                     |  |  |  - Gauges (Indicadores circulares tipo SCADA)              |  |  |
|  - Temporizador millis()|                    |  |  |  - pyqtgraph Charts (Gráficas vectoriales en tiempo real)|  |  |
|  - Descarte inicial    |                     |  |  |  - QTableWidget (Historial de mediciones)                |  |  |
|  - Control de Errores  |                     |  |  |  - LogConsole (Consola de eventos de sistema)            |  |  |
+-----------+------------+                     |  |  +-----------------------------+-----------------------------+  |  |
            |                                  |  |                                |                                |  |
            | Tramas ASCII / CSV               |  |                                v                                |  |
            |  "24.5,60.2,450.0\n"             |  |  +-----------------------------------------------------------+  |  |
            |  "#STATUS:STABLE\n"              |  |  |                CAPA DE MODELO Y LÓGICA                    |  |  |
            |                                  |  |  |  - sensor_manager.py  (Deque circular & Memory Store)   |  |  |
            v                                  |  |  |  - classification.py (Clasificador fuzzy / Rangos)      |  |  |
    +---------------+                          |  |  |  - statistics_manager.py (Min, Max, Promedio, Desv)     |  |  |
    | PUERTO SERIAL |                          |  |  |  - settings_manager.py (Persistencia JSON de App)       |  |  |
    | USB / /dev/tty|                          |  |  +-----------------------------+-----------------------------+  |  |
    +-------+-------+                          |  |                                |                                |  |
            |                                  |  |                                v                                |  |
            | PySerial                         |  |  +-----------------------------------------------------------+  |  |
            v                                  |  |  |                CAPA DE REPORTES Y GENERACIÓN             |  |  |
+------------------------+                     |  |  |  - excel_manager.py (Libro de trabajo OpenPyXL)         |  |  |
|  serial_reader.py      |                     |  |  |  - pdf_manager.py   (ReportLab Executive PDF + Charts)   |  |  |
|  (QThread Dedicado)    |                     |  |  +-----------------------------------------------------------+  |  |
|  - Lectura asíncrona   |                     |  +-----------------------------------------------------------------+  |
|  - Filtro defensivo    |                     |                                                                       |
|  - Reconexión auto     |                     |                                                                       |
+-----------+------------+                     |                                                                       |
            | Emite Qt Signals                 |                                                                       |
            +----------------------------------+-----------------------------------------------------------------------+
               new_data(temp, hum, light)
               status_received(msg)
               error_occurred(err)
========================================================================================================================
```

---

## 3. Diagramas de Flujo del Sistema (Mermaid)

### 3.1 Diagrama de Flujo General End-to-End (E2E)

Este diagrama describe todo el recorrido del dato desde el fenómeno físico en los sensores hasta su representación en la interfaz visual y exportación final.

```mermaid
flowchart TD
    %% NODO HARDWARE
    subgraph HARDWARE [" Hardware & Sensores (Arduino UNO) "]
        A1[Inicio / Power On Arduino] --> A2[setup: Serial.begin 9600]
        A2 --> A3[dht.begin & Enviar #SIMA:v2:TEMP,HUM,LIGHT]
        A3 --> A4[Loop Principal: ¿Transcurrieron 2000 ms?]
        A4 -- No --> A4
        A4 -- Sí --> A5[Lectura DHT11 Temp/Hum & AnalogRead LDR]
        A5 --> A6{¿Lectura Valida / No NaN?}
        A6 -- No --> A7[Incr. Errores Consecutivos & Enviar #ERROR]
        A7 --> A4
        A6 -- Sí --> A8{¿Conteo <= Lecturas Descarte?}
        A8 -- Sí --> A9[Enviar #STATUS:STABILIZING] --> A4
        A8 -- No --> A10[Enviar Trama CSV: Temp,Hum,Luz\n] --> A4
    end

    %% CANAL SERIAL
    HARDWARE -->|USB Cable Serial UART| SERIAL_BUS[ Puerto Serial / USB /dev/ttyUSB0 ]

    %% BACKEND PYTHON MULTITHREAD
    subgraph PYTHON_BACKEND [" Adquisición & Procesamiento Async (Python) "]
        SERIAL_BUS --> B1[SerialReader QThread: readline]
        B1 --> B2{¿Empieza con '#'}
        B2 -- Sí --> B3[Procesar Línea de Control / Status / Error]
        B3 --> B4[Emitir Signal: status_received / error_occurred]
        B2 -- No --> B5[Split CSV por comas & Casting a float]
        B5 --> B6{¿Valores en Rangos Fisicos Validos?}
        B6 -- No --> B7[Log Warning: Dato Descartado]
        B6 -- Sí --> B8[Emitir Signal Qt: new_data temp, hum, light]
    end

    %% CAPA DE PRESENTACION PYSIDE6
    subgraph PYSIDE6_GUI [" Capa de Presentación & Motor MVVM (PySide6) "]
        B8 --> C1[MainWindow Slot: _handle_new_data]
        C1 --> C2[EnvironmentalClassifier: Evaluar Rangos y Confort]
        C2 --> C3[SensorManager: Guardar en Circular Buffer deque]
        C3 --> C4[StatisticsManager: Actualizar Min/Max/Promedio]
        
        %% Renderizado UI
        C4 --> D1[Dashboard Cards: Actualizar Temp, Hum, Confort]
        C4 --> D2[Dashboard Gauges: Animación de Aguja & Arcos]
        C4 --> D3[pyqtgraph Charts: Re-plot Vectores de Tiempo Real]
        C4 --> D4[QTableWidget: Insertar nueva fila con Badge de Color]
        C4 --> D5[QStatusBar & Console Log: Refrescar Muestras y Status]
    end

    %% CAPA DE PERSISTENCIA
    subgraph EXPORT [" Exportación & Persistencia "]
        E1[Usuario presiona Exportar] --> E2{¿Tipo de Exportación?}
        E2 -- Excel --> E3[ExcelManager: Generar Hojas con openpyxl]
        E2 -- PDF --> E4[PDFManager: Renderizar Gráficas & ReportLab PDF]
        E3 --> E5[Guardar en disco /reports/ o /excel/]
        E4 --> E5
    end

    PYSIDE6_GUI --> EXPORT
```

---

### 3.2 Diagrama de Secuencia de Comunicación Hardware ↔ Software

El siguiente diagrama de secuencia visualiza la sincronización temporal y el protocolo de handshake entre Arduino y el cliente PySide6:

```mermaid
sequenceDiagram
    autonumber
    participant HW as Sensor DHT11 / LDR
    participant ARD as Arduino UNO (Firmware)
    participant SER as Puerto Serial (USB UART)
    participant THR as SerialReader (QThread)
    participant MW as MainWindow (Qt GUI)
    participant SM as SensorManager (Model)

    %% Inicio de conexión
    MW->>THR: start() [Inicia Hilo Serial]
    THR->>SER: PySerial open('/dev/ttyUSB0', 9600)
    SER-->>ARD: Reset por DTR Line
    ARD->>ARD: setup() -> Inicializar DHT11
    ARD->>SER: Enviar "#SIMA:v2:TEMP,HUM,LIGHT\n"
    ARD->>SER: Enviar "#STATUS:READY\n"
    
    SER->>THR: readline() -> "#SIMA:v2:TEMP,HUM,LIGHT\n"
    THR->>MW: emit protocol_info("v2:TEMP,HUM,LIGHT")
    SER->>THR: readline() -> "#STATUS:READY\n"
    THR->>MW: emit status_received("READY")
    MW->>MW: Actualizar LED a Naranja / Estabilizando

    %% Bucle de Lectura
    loop Cada 2000 ms (millis)
        HW->>ARD: Leer Temp, Humedad, Luz
        ARD->>ARD: Validar !isnan() y Estabilización
        ARD->>SER: Enviar "24.5,58.2,420.0\n"
        SER->>THR: readline() -> "24.5,58.2,420.0\n"
        THR->>THR: Parsear float & Validar Rangos
        THR->>MW: emit new_data(24.5, 58.2, 420.0)
        MW->>SM: add_reading(24.5, 58.2, 420.0)
        SM->>SM: Clasificar & Calcular Índice Confort
        MW->>MW: Refrescar Cards, Gauges, pyqtgraph y QTableWidget
    end

    %% Desconexión
    MW->>THR: stop() [Solicitud de Cierre]
    THR->>SER: PySerial close()
    THR->>MW: emit connection_changed(False)
    MW->>MW: Actualizar LED a Rojo (Desconectado)
```

---

### 3.3 Diagrama de Flujo del Motor de Clasificación e Índice de Confort

Este esquema muestra cómo el módulo `classification.py` procesa los datos crudos entrantes para asignar categorías cualitativas y calcular el índice de confort general.

```mermaid
flowchart LR
    subgraph ENTRADA [" Lecturas Crudas "]
        T[Temperatura °C]
        H[Humedad %]
        L[Luminosidad Lux]
    end

    subgraph CLASIFICADOR [" EnvironmentalClassifier "]
        %% Clasificación Temperatura
        T --> CT{Evaluar Temp}
        CT -- "< 18°C" --> CT1["Fresco (#3b82f6)"]
        CT -- "18°C - 25°C" --> CT2["Confort (#10b981)"]
        CT -- "25°C - 30°C" --> CT3["Cálido (#f59e0b)"]
        CT -- "> 30°C" --> CT4["Muy Cálido (#ef4444)"]

        %% Clasificación Humedad
        H --> CH{Evaluar Humedad}
        CH -- "< 30%" --> CH1["Seco (#f59e0b)"]
        CH -- "30% - 60%" --> CH2["Óptimo (#10b981)"]
        CH -- "60% - 80%" --> CH3["Húmedo (#3b82f6)"]
        CH -- "> 80%" --> CH4["Muy Húmedo (#ef4444)"]

        %% Clasificación Luz
        L --> CL{Evaluar Luz}
        CL -- "< 200 Lux" --> CL1["Baja (#6b7280)"]
        CL -- "200 - 800 Lux" --> CL2["Normal (#10b981)"]
        CL -- "> 800 Lux" --> CL3["Alta (#f59e0b)"]

        %% Algoritmo de Confort
        T & H & L --> CONF[Cálculo de Confort Ambiental]
        CONF --> SCORE["Score = 100 - (Penalty Temp + Penalty Hum + Penalty Luz)"]
    end

    subgraph SALIDA [" ComfortResult "]
        SCORE --> CS{Puntaje Final}
        CS -- ">= 85" --> O1["Excelente (#10b981)"]
        CS -- "70 - 84" --> O2["Bueno (#3b82f6)"]
        CS -- "50 - 69" --> O3["Aceptable (#f59e0b)"]
        CS -- "< 50" --> O4["Deficiente (#ef4444)"]
    end
```

---

### 3.4 Diagrama de Arquitectura Multihilo (QThread vs Qt GUI Loop)

Garantizar una interfaz de usuario fluida (60 FPS sin congelamientos) requiere aislar la lectura del puerto serial de I/O en un hilo secundario mediante **QThread**:

```mermaid
graph TD
    subgraph MAIN_THREAD [" Main Thread (GUI & Renderizado Principal) "]
        UI_EVENT[Qt Event Loop]
        RENDER[Renderizado de Interfaz / QPainter / pyqtgraph]
        USER_IN[Eventos del Usuario: Botones, Sliders, Clics]
        SLOT_RECV[Slot: _handle_new_data]

        UI_EVENT --> USER_IN
        UI_EVENT --> RENDER
        SLOT_RECV --> RENDER
    end

    subgraph WORKER_THREAD [" SerialReader Thread (QThread Secundario) "]
        THREAD_LOOP[Bucle while self._running]
        SERIAL_IO[PySerial readline - Bloqueante]
        PARSER[Parseador de Protocolo & Validaciones]
        SIGNAL_EMIT[Emisión de Señales Qt]

        THREAD_LOOP --> SERIAL_IO
        SERIAL_IO --> PARSER
        PARSER --> SIGNAL_EMIT
    end

    %% CONEXION SEGURA ENTRE HILOS
    SIGNAL_EMIT == "Señal QueuedConnection (Thread-Safe)" ==> SLOT_RECV
```

---

### 3.5 Diagrama de Flujo de Exportación (PDF y Excel)

```mermaid
flowchart TD
    START[Clic en Botón Exportar] --> CHK{¿Existen lecturas en memoria?}
    CHK -- No --> ERR[Mostrar QMessageBox Advertencia]
    CHK -- Sí --> OPT{¿Qué formato eligió?}

    %% FLUJO EXCEL
    OPT -- Excel --> EX1[ExcelManager: Crear Workbook OpenPyXL]
    EX1 --> EX2[Crear Hoja 'Resumen' con Estadísticas]
    EX2 --> EX3[Crear Hoja 'Mediciones' con Historial Completo]
    EX3 --> EX4[Aplicar Estilos, Colores, Formatos de Celda]
    EX4 --> EX5[Guardar archivo .xlsx en /excel/]

    %% FLUJO PDF
    OPT -- PDF --> PDF1[PDFManager: Inicializar SimpleDocTemplate ReportLab]
    PDF1 --> PDF2[Compilar Paleta de Colores & Estilos de Párrafo]
    PDF2 --> PDF3[Generar Portada Ejecutiva con Tarjetas de Métricas]
    PDF3 --> PDF4[Renderizar Tabla de Estadísticas y Distribución]
    PDF4 --> PDF5[Convertir Gráficas pyqtgraph a Imágenes PNG]
    PDF5 --> PDF6[Compilar Tabla de Historial Registrado]
    PDF6 --> PDF7[Guardar archivo .pdf en /reports/]

    EX5 --> END[Notificar Éxito en UI y Consola]
    PDF7 --> END
```

---

## 4. Especificación del Protocolo de Comunicación SIMA

El protocolo de comunicación SIMA opera sobre un enlace serie asíncrono (UART) a **9600 Baudios, 8 bits de datos, sin paridad y 1 bit de parada (8N1)**.

### Tipos de Tramas Transmitidas por Arduino:

| Tipo de Trama | Prefijo | Ejemplo de Formato | Descripción |
| :--- | :--- | :--- | :--- |
| **Cabecera de Protocolo** | `#SIMA:` | `#SIMA:v2:TEMP,HUM,LIGHT\n` | Enviado al inicio. Indica la versión y los campos transmitidos. |
| **Mensaje de Estado** | `#STATUS:` | `#STATUS:STABLE\n` | Comunica cambios de estado (`READY`, `STABILIZING`, `STABLE`). |
| **Mensaje de Error** | `#ERROR:` | `#ERROR:DHT11_READ_FAIL\n` | Alerta sobre fallos de hardware o lecturas inválidas. |
| **Lectura de Datos** | *Sin `#`* | `24.5,60.2,450.0\n` | Trama de datos en formato **CSV** (Temperatura, Humedad, Luz). |

---

## 5. Desglose Componente por Componente

### 1. `trabajo.ino` (Firmware Arduino)
- **Función**: Nodo sensor embebido.
- **Temporización**: Uso estricto de `millis()` (sin `delay()`) con intervalo de 2000 ms.
- **Resiliencia**:
  - Descarta las primeras 2 lecturas inestables tras el encendido.
  - Mantiene un contador de errores consecutivos. Si supera 5 errores, emite alerta por serial y enciende el LED integrado (`LED_BUILTIN`).

### 2. `serial_reader.py` (Lector Serial Multihilo)
- **Herencia**: `QThread`.
- **Funcionalidades**:
  - Ejecuta el bucle I/O sin bloquear la interfaz de usuario.
  - Filtra caracteres corruptos (`UnicodeDecodeError`).
  - Aplica un filtro de validación física de rangos (-10°C a 60°C; 0% a 100% Humedad).
  - Gestiona reconexión automática en caso de desconexión del cable USB.

### 3. `sensor_manager.py` (Modelo de Datos)
- **Estructura**: `deque(maxlen=100)` para buffer circular en gráficas + `list` completa para exportación.
- **Thread Safety**: Uso de `threading.Lock()` para garantizar lecturas y escrituras seguras entre hilos.

### 4. `classification.py` (Motor de Clasificación Fuzzy & Confort)
- **Categorización**: Divide los valores numéricos en etiquetas cualitativas con colores Hexadecimales asociados.
- **Índice de Confort**: Algoritmo ponderado de penalización que evalúa la desviación respecto a las zonas ideales de confort humano (21°C - 24°C y 40% - 50% Humedad).

### 5. `gui/mainwindow.py` & `gui/dashboard.py` (Capa de Presentación)
- **Vistas Incluidas**:
  - `Cards`: Tarjetas dinámicas con badges de estado.
  - `Gauges`: Indicadores vectoriales renderizados con `QPainter`.
  - `pyqtgraph Charts`: Gráficas de altísimo rendimiento aceleradas para series de tiempo.
  - `QTableWidget`: Tabla formateada en tiempo real.
  - `LogConsole`: Consola de eventos del sistema.

### 6. `excel_manager.py` & `pdf_manager.py` (Persistencia & Reportes)
- Generación de reportes ejecutivos en formato **Excel (.xlsx)** y **PDF (.pdf)** profesionales con tablas de resumen, estadísticas descriptivas (min, max, media, desviación estándar) e historial filtrado.

---

## 6. Esquema Electrónico de Conexiones Hardware

```
                      +-------------------+
                      |   ARDUINO UNO     |
                      |                   |
                      |              5V   +-----> VCC (DHT11 & LDR)
                      |             GND   +-----> GND (DHT11 & LDR)
                      |                   |
   DHT11 Sensor       |                   |
  +------------+      |                   |
  | VCC        +------+                   |
  | DATA (S)   +----->| Pin Digital 4     |
  | GND        +------+                   |
  +------------+      |                   |
                      |                   |
   Fotorresistencia   |                   |
   LDR + Resistencia  |                   |
  +------------+      |                   |
  | VCC        +------+                   |
  | Signal (S) +----->| Pin Analógico A0  |
  | GND (10kΩ) +------+                   |
  +------------+      +---------+---------+
                                |
                                | Cable USB Tipo B (Serial UART @ 9600)
                                v
                      +-------------------+
                      | PC HOST (PYTHON)  |
                      +-------------------+
```

---

> **SIMA Framework v2.0** — Diseñado y desarrollado con estándares de calidad industrial SCADA.
