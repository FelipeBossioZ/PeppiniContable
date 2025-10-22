# Sistema de Contabilidad

Este es un sistema de contabilidad full-stack diseñado para registrar transacciones diarias, gestionar asientos recurrentes y generar reportes mensuales en formato Excel. Cuenta con un sistema de licencias para controlar el acceso de los usuarios.

## Características

- **Backend:** Construido con Django y Django REST Framework.
- **Frontend:** Construido con React.
- **Base de Datos:** SQLite (para desarrollo y despliegues sencillos).
- **Autenticación:** Basada en Tokens.
- **Reportes:** Exportación a Excel de un "Balance de Prueba por Tercero".
- **Automatización:** Comando para generar transacciones recurrentes automáticamente.
- **Licenciamiento:** Control de acceso de usuarios mediante licencias con fecha de vencimiento.
- **Despliegue:** Preparado para ser desplegado con Docker.

---

## Instalación y Ejecución en un Entorno Local

Sigue estos pasos para instalar y correr el proyecto en tu computador para pruebas.

### Prerrequisitos

- Python 3.8 o superior.
- Node.js y npm (para el frontend).

### 1. Clona el Repositorio

Primero, descarga el código fuente en tu máquina.

```bash
git clone <URL_DEL_REPOSITORIO>
cd <NOMBRE_DEL_DIRECTORIO>
```

### 2. Configuración del Backend (Django)

#### 2.1. Crea y Activa un Entorno Virtual

Es una buena práctica aislar las dependencias del proyecto.

```bash
python -m venv env
source env/bin/activate  # En Windows: env\\Scripts\\activate
```

#### 2.2. Instala las Dependencias de Python

```bash
pip install -r requirements.txt
```

#### 2.3. Configura las Variables de Entorno

Crea un archivo `.env` a partir del ejemplo.

```bash
cp .env.example .env
```

Ahora, necesitas generar una nueva `SECRET_KEY`. Ejecuta este comando y pega el resultado en tu archivo `.env`:

```bash
python -c 'from django.core.management.utils import get_random_secret_key; print(f"SECRET_KEY={get_random_secret_key()}")'
```
Tu archivo `.env` debería verse así (con tu clave única):
```
SECRET_KEY=tu_clave_secreta_generada_aqui
```

#### 2.4. Aplica las Migraciones de la Base de Datos

Esto creará el archivo de la base de datos (`db.sqlite3`) con todas las tablas necesarias.

```bash
python manage.py migrate
```

#### 2.5. Crea un Superusuario (Administrador)

Este será tu usuario para gestionar el sistema y las licencias.

```bash
python manage.py createsuperuser
```

Sigue las instrucciones en pantalla para crear tu usuario y contraseña de administrador.

### 3. Configuración del Frontend (React)

#### 3.1. Instala las Dependencias de Node.js

Abre una **nueva terminal**, navega a la carpeta del proyecto y entra al directorio `frontend`.

```bash
cd frontend
npm install
```

### 4. Ejecuta la Aplicación

¡Ya casi está todo listo! Necesitas tener **dos terminales abiertas** al mismo tiempo: una para el backend y otra para el frontend.

- **En la Terminal 1 (Backend):**
  Asegúrate de estar en la raíz del proyecto y que tu entorno virtual esté activado.

  ```bash
  python manage.py runserver
  ```
  El servidor de Django comenzará a correr en `http://127.0.0.1:8000`.

- **En la Terminal 2 (Frontend):**
  Asegúrate de estar en el directorio `frontend`.

  ```bash
  npm start
  ```
  La aplicación de React se abrirá automáticamente en tu navegador en `http://localhost:3000`.

### 5. ¡Listo para Usar!

1.  Abre tu navegador y ve a `http://localhost:3000`.
2.  Inicia sesión con las credenciales del superusuario que creaste.
3.  **Importante:** Para que tu usuario pueda usar la aplicación, primero debes asignarle una licencia.
    - Ve al panel de administrador: `http://127.0.0.1:8000/admin`.
    - Inicia sesión de nuevo con tus credenciales de admin.
    - Ve a la sección "Licenses" y añade una nueva licencia.
    - Selecciona tu usuario, establece una fecha de vencimiento en el futuro y marca la casilla "Is active".
    - ¡Guarda la licencia y vuelve a la aplicación en `http://localhost:3000` para empezar a usarla!
