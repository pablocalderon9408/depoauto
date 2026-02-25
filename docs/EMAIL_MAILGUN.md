# Configuración de Email para el formulario de contacto

## Mailpit (local, sin configuración)

Al usar `make up` con Docker, el correo se envía a **Mailpit**, que captura todos los mensajes localmente sin enviarlos a internet.

- **Web UI:** [http://localhost:8025](http://localhost:8025) — aquí ves todos los correos enviados
- No requiere credenciales
- Ideal para desarrollo local

---

## Mailgun (producción)

### 1. Crear cuenta en Mailgun

1. Ve a **[mailgun.com](https://www.mailgun.com)** y haz clic en **Sign Up**.
2. Regístrate con tu email (puedes usar tu Hotmail).
3. Verifica tu email y completa el registro.
4. Mailgun ofrece un **plan gratuito** con 5.000 correos/mes durante 3 meses, luego 1.000/mes gratis.

---

## 2. Obtener credenciales SMTP

### Opción A: Usar dominio sandbox (para pruebas)

El dominio sandbox viene por defecto. **Importante:** solo puedes enviar a **destinatarios autorizados** (hasta 5).

1. En el panel de Mailgun, ve a **Sending** → **Domain settings**.
2. Selecciona tu dominio sandbox (ej: `sandboxXXXX.mailgun.org`).
3. Ve a la pestaña **SMTP credentials**.
4. El usuario SMTP es: `postmaster@sandboxXXXX.mailgun.org` (cópialo).
5. Haz clic en **Reset password** para generar una contraseña SMTP.
6. **Copia la contraseña** (solo se muestra una vez).

### Autorizar tu email para recibir (sandbox)

1. En **Domain settings** → **Authorized recipients**.
2. Añade `pablocalderon94@hotmail.com`.
3. Revisa tu bandeja de Hotmail y acepta la invitación de Mailgun.

### Opción B: Usar tu propio dominio (producción)

1. En **Sending** → **Domains**, haz clic en **Add New Domain**.
2. Introduce tu dominio (ej: `depoauto.com`).
3. Mailgun te dará registros DNS (TXT, MX, CNAME) para añadir en tu proveedor de dominio.
4. Una vez verificado, usa `postmaster@tudominio.com` como usuario SMTP.
5. Genera la contraseña SMTP en **Domain settings** → **SMTP credentials**.

---

## 3. Configurar variables de entorno

Crea o edita tu archivo `.env` (o configura las variables en tu entorno):

```bash
# Proveedor de email (mailgun, gmail, outlook)
EMAIL_PROVIDER=mailgun

# Mailgun
EMAIL_HOST=smtp.mailgun.org
EMAIL_PORT=587
EMAIL_HOST_USER=postmaster@sandboxXXXX.mailgun.org
EMAIL_HOST_PASSWORD=tu-contraseña-smtp-de-mailgun

# Correo donde se reciben los mensajes del formulario
CONTACT_EMAIL=pablocalderon94@hotmail.com

# Opcional: dirección "desde" (por defecto usa EMAIL_HOST_USER)
DEFAULT_FROM_EMAIL=noreply@depoauto.com
```

**Región EU:** Si tu cuenta está en Europa, usa:

```bash
MAILGUN_REGION=eu
EMAIL_HOST=smtp.eu.mailgun.org
```

---

## 4. Configurar desde el Admin de Django (opcional)

Si prefieres no usar variables de entorno, puedes configurar en **Site configuration**:

- **Contact email**: `pablocalderon94@hotmail.com`
- **Email SMTP user**: `postmaster@sandboxXXXX.mailgun.org`
- **Email SMTP password**: contraseña SMTP de Mailgun

---

## 5. Usar con Docker (local)

El `docker-compose.yml` ya carga `.env` automáticamente:

1. Crea `.env` en la raíz del proyecto:
   ```bash
   cp .env.example .env
   ```
2. Edita `.env` con tus credenciales de Mailgun.
3. Levanta los servicios: `make up`

**Nota:** Si `.env` no existe, `docker-compose` fallará. Créalo aunque sea vacío (`touch .env`) o desde el ejemplo.

---

## 6. Probar

1. Levanta el proyecto: `make up` (con Docker) o `python manage.py runserver`.
2. Ve a la página de contacto.
3. Envía un mensaje de prueba.
4. Revisa tu bandeja en Hotmail.

---

## Referencias

- [Mailgun SMTP docs](https://documentation.mailgun.com/docs/mailgun/user-manual/sending-messages/send-smtp)
- [Dónde encontrar credenciales SMTP](https://help.mailgun.com/hc/en-us/articles/203380100-Where-can-I-find-my-API-keys-and-SMTP-credentials)
- [Recipientes autorizados (sandbox)](https://help.mailgun.com/hc/en-us/articles/217531258-Authorized-Recipients)
