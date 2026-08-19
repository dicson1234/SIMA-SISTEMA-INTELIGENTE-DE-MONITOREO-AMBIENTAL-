

---

# 📽️ PARTE 2: ESTRUCTURA COMPLETA DE DIAPOSITIVAS (SIN GUIÓN)

*(Información y contenido listo para copiar directamente a las filminas de la presentación)*

---

### 🖼️ **DIAPOSITIVA 1: Portada Oficial**
* **Expositor:** Pilar
* **Título Principal:** SIMA — Sistema Inteligente de Monitoreo Ambiental y Calidad del Aire
* **Subtítulo:** Adquisición de Datos en Tiempo Real, Clasificación y Reportes Automáticos
* **Elementos en Pantalla:**
  * Nombres de los Integrantes: Dicson, Isabela, Pérez, Pilar.
  * Logotipo institucional del proyecto.
  * Iconos representativos: Microcontrolador, Sensores, Gráfica de Datos y Escudo de IA.

---

### 🖼️ **DIAPOSITIVA 2: El Desafío de la Calidad del Aire y las Variables Ambientales**
* **Expositor:** Pilar
* **Título:** Problemática: La Calidad del Aire en Entornos Críticos
* **Puntos Clave en Filmina:**
  * **Amenaza Invisible:** Partículas suspendidas **PM2.5** ($\le 2.5\,\mu\text{m}$) y **PM10** ($\le 10\,\mu\text{m}$) ingresan al sistema respiratorio y dañan equipos electrónicos.
  * **Variables Clave:** Temperatura y Humedad condicionan la dispersión de tóxicos y el confort térmico.
  * **Sectores Afectados:** Laboratorios, industrias, salas de servidores (Data Centers), hospitales e invernaderos.
  * **Fracaso de la Medición Manual:** Mediciones esporádicas provocan lentitud de respuesta, errores de transcripción y falta de evidencias continuas.

---

### 🖼️ **DIAPOSITIVA 3: La Solución Tecnológica SIMA**
* **Expositor:** Pilar
* **Título:** Nuestra Solución: Plataforma Integrada SIMA
* **Puntos Clave en Filmina:**
  * **1. Captura Automatizada:** Sensores físicos de precisión conectados a microcontrolador.
  * **2. Visualización Intuitiva:** Dashboard gráfico en tiempo real con semáforo de riesgo por colores.
  * **3. Reportes Oficiales:** Generación automática de documentos en PDF y Excel sin intervención humana.
  * **Impacto:** Respuesta inmediata ante emergencias ambientales y reducción del 100% en tiempo de documentación.

---

### 🖼️ **DIAPOSITIVA 4: Arquitectura del Hardware y Módulo de Sensores**
* **Expositor:** Isabela
* **Título:** Componentes de Hardware y Sensores de Precisión
* **Puntos Clave en Filmina:**
  * **Arduino UNO R3:** Microcontrolador ATmega328P ($16\text{ MHz}$) que actúa como cerebro de adquisición física.
  * **Sensor de Material Particulado (PM2.5 / PM10):** Detección óptica por dispersión de luz láser (*Laser Scattering*) en $\mu\text{g/m}^3$.
  * **Sensor de Temperatura y Humedad (DHT11/22):** Medición capacitiva y por termistor NTC.
  * **Sensores de Gases (Serie MQ):** Detección química de contaminantes mediante capas de $\text{SnO}_2$.

---

### 🖼️ **DIAPOSITIVA 5: Circuitos, Instrumentación y Cableado**
* **Expositor:** Isabela
* **Título:** Diagrama de Conexión del Circuito e Instrumentación
* **Puntos Clave en Filmina:**
  * Alimentación centralizada a $5\text{V}$ y referencia común a Tierra ($\text{GND}$).
  * Protocolo monocable (1-Wire) y resistencia de *Pull-Up* de $10\text{k}\Omega$ para estabilizar señales digitales.
  * Muestreo continuo a frecuencia fija de $1\text{ Hz}$ (1 lectura por segundo) con filtrado electrónico de ruido.

---

### 🖼️ **DIAPOSITIVA 6: Transmisión Serial USB y Protocolo de Datos**
* **Expositor:** Isabela
* **Título:** Comunicación Serial USB (Arduino $\rightarrow$ Computadora)
* **Puntos Clave en Filmina:**
  * **Protocolo UART:** Comunicación serial asíncrona a velocidad de **9600 Baudios**.
  * **Estructura de Datos CSV:** Trama de texto plano optimizada:
    $$\text{"Temperatura, Humedad, PM2.5, PM10"}$$
  * Conexión Plug & Play de bajo consumo a través de puertos serie USB (`/dev/ttyUSB` o `COM`).

---

### 🖼️ **DIAPOSITIVA 7: Dashboard Visual de Control en Tiempo Real**
* **Expositor:** Pérez
* **Título:** Interfaz Gráfica: Dashboard de Control en Vivo
* **Puntos Clave en Filmina:**
  * **Interfaz Profesional (PySide6):** Diseño industrial con soporte para Modo Oscuro y Claro.
  * **Tarjetas Métricas:** Indicación numérica instantánea con unidades ($\text{°C}$, $\%$, $\mu\text{g/m}^3$).
  * **Diales Circulares (Gauges):** Representación geométrica vectorial del nivel actual.
  * **Gráficas Continuas (`pyqtgraph`):** Trazado en tiempo real a 60 FPS con zoom interactivo y paneo.

---

### 🖼️ **DIAPOSITIVA 8: Semáforo de Alertas y Clasificación de Riesgo**
* **Expositor:** Pérez
* **Título:** Semáforo de Riesgo Ambiental e Índices Ambientales
* **Puntos Clave en Filmina:**
  * 🟢 **Verde (Zona de Confort / Aire Limpio):** Parámetros óptimos según estándares OMS/EPA.
  * 🔵 **Azul (Zona Fría / Moderada):** Temperaturas o humedades por debajo del nivel de confort.
  * 🟡 **Amarillo (Alerta Moderada):** Elevación inicial de Material Particulado o Temperatura.
  * 🔴 **Rojo (Peligro / Aire Contaminado):** Concentraciones nocivas de PM2.5/PM10 o calor extremo.
  * **Respuesta Dinámica:** Cambio automático del color de acento de la aplicación para advertencia visual inmediata.

---

### 🖼️ **DIAPOSITIVA 9: Generación Automática de Reportes (PDF y Excel)**
* **Expositor:** Pérez
* **Título:** Automatización de Informes Oficiales (PDF y Excel)
* **Puntos Clave en Filmina:**
  * **Reportes Excel (`openpyxl`):** Dos pestañas (Resumen estadístico de Mín/Máx/Promedios e Historial crudo completo).
  * **Reportes PDF Corporativos (`ReportLab`):** Documento listo para imprimir con portada, gráficas vectoriales incrustadas y **conclusiones heurísticas redactadas automáticamente**.
  * **Eficiencia:** Exportación instantánea con un solo clic.

---

### 🖼️ **DIAPOSITIVA 10: Arquitectura de Software Multitarea (MVVM y `QThread`)**
* **Expositor:** Dicson
* **Título:** Arquitectura Interna del Software y Rendimiento Multitarea
* **Puntos Clave en Filmina:**
  * **Patrón MVVM:** Desacoplamiento total entre Modelo (Sensores/Datos), Vista (GUI) y Controlador.
  * **Programación Multihilo (`QThread`):** La lectura serial y la compilación de reportes corren en un hilo secundario independiente.
  * **Mecanismo de Señales y Slots:** Comunicación asíncrona segura entre hilos.
  * **Garantía de Fluidez:** La interfaz gráfica jamás se congela ni sufre retardos.

---

### 🖼️ **DIAPOSITIVA 11: Visión a Futuro: Red Neuronal Predictiva e IA**
* **Expositor:** Dicson
* **Título:** Visión a Futuro: Inteligencia Artificial Predictiva (MLP)
* **Puntos Clave en Filmina:**
  * **Red Neuronal Multicapa (PyTorch):** Módulo predictivo para aprendizaje continuo en tiempo real (*Online Learning*).
  * **Pronóstico Autoregresivo:** Predicción del nivel de Material Particulado y Temperatura a $+1\text{ min}$ y $+5\text{ min}$.
  * **Prevención Proactiva:** Alertar antes de que ocurra la contaminación o el sobrecalentamiento.
  * **Preparado para Agentes Conversacionales (LLM):** Exposición de datos en JSON para interacción con chatbots inteligentes.

---

### 🖼️ **DIAPOSITIVA 12: Conclusiones e Impacto del Proyecto SIMA**
* **Expositor:** Dicson
* **Título:** Conclusiones e Impacto Tecnológico de SIMA
* **Puntos Clave en Filmina:**
  * **Integración Exitosa:** Sinergia entre hardware microcontrolado accesible (Arduino) y software industrial (Python).
  * **Protección y Automatización:** Monitoreo en tiempo real de Calidad del Aire con eliminación del 100% del trabajo manual de reportes.
  * **Plataforma Escalable:** Sistema modular preparado para nuevos sensores y redes neuronales.
  * **Cierre:** Espacio abierto para preguntas del jurado.
