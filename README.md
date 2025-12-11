# Onto AI Desktop

Aplicación de escritorio multiplataforma para gestionar información de coachees y realizar consultas a proveedores de IA.

## Características

- Gestión completa de coachees (agregar, buscar, listar)
- Registro de sesiones con notas detalladas
- Integración con múltiples proveedores de IA:
  - OpenAI (GPT-4, GPT-3.5)
  - GroqCloud
  - GPT4All (modelos locales)
  - Mixtral
  - Google Gemini
- Modo claro/oscuro
- Diseño responsive y minimalista
- Almacenamiento local con SQLite
- Multiplataforma (Windows, macOS, Linux)

## Requisitos

- Python 3.8 o superior
- PySide6

## Instalación

1. Clonar o descargar el proyecto

2. Instalar las dependencias:

```bash
pip install -r requirements.txt
```

## Uso

Ejecutar la aplicación:

```bash
python main.py
```

## Configuración de Proveedores de IA

1. Ir a la pestaña "Configuración"
2. Seleccionar el proveedor deseado
3. Ingresar la API Key correspondiente (o ruta del modelo para GPT4All)
4. Seleccionar el modelo
5. Hacer clic en "Test de Conexión" para verificar
6. Guardar la configuración

### Obtener API Keys

- **OpenAI**: https://platform.openai.com/api-keys
- **GroqCloud**: https://console.groq.com/keys
- **Google Gemini**: https://makersuite.google.com/app/apikey

### GPT4All

Para usar modelos locales con GPT4All:

1. Descargar un modelo desde https://gpt4all.io/
2. En configuración, seleccionar "GPT4All"
3. Hacer clic en "Examinar" y seleccionar el archivo del modelo (.bin o .gguf)

## Estructura del Proyecto

```
/project
├── main.py                 # Punto de entrada
├── requirements.txt        # Dependencias
├── coachees.db            # Base de datos SQLite (generada automáticamente)
├── /models
│   ├── coachee.py         # Modelo de datos de coachee
│   └── session.py         # Modelo de datos de sesión
├── /services
│   ├── storage.py         # Gestión de base de datos
│   └── ai_providers.py    # Proveedores de IA
└── /ui
    ├── main_window.py     # Ventana principal
    ├── coachee_form.py    # Formulario de coachee
    ├── sessions_view.py   # Vista de sesiones
    └── settings.py        # Configuración
```

## Funcionalidades Principales

### Gestión de Coachees

- Agregar nuevos coachees con validación de campos
- Buscar coachees por nombre, apellido, email o teléfono
- Ver lista completa de coachees

### Sesiones

- Crear notas de sesión para cada coachee
- Ver historial completo de sesiones
- Consultar IA para análisis de notas

### Consulta de IA

- Análisis automático de notas de sesión
- Sugerencias para próximas sesiones
- Consultas personalizadas a diferentes proveedores
