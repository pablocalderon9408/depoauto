# Configuración de Email (Gmail) para el formulario de contacto

## Opción 1: Configurar desde el Admin de Django

1. Ve a **Admin** → **Site configuration**
2. En la sección **"Email (formulario de contacto)"**:
   - **Contact email**: Correo donde recibes los mensajes (ej: `pablocalderon94@hotmail.com`)
   - **Email SMTP user**: Tu cuenta Gmail (ej: `micuenta@gmail.com`)
   - **Email SMTP password**: Contraseña de aplicación de Gmail

## Opción 2: Variables de entorno (.env)

```bash
EMAIL_PROVIDER=gmail
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=micuenta@gmail.com
EMAIL_HOST_PASSWORD=contraseña-de-aplicacion
CONTACT_EMAIL=pablocalderon94@hotmail.com
```

## Crear contraseña de aplicación en Gmail

1. Activa la **verificación en dos pasos** en tu cuenta Google: [myaccount.google.com/security](https://myaccount.google.com/security)
2. Ve a **Contraseñas de aplicaciones**: [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
3. Crea una contraseña para "Correo" o "Otro (nombre personalizado)"
4. Copia la contraseña de 16 caracteres
5. Pégala en el Admin (SiteConfig) o en `EMAIL_HOST_PASSWORD` del `.env`

## Desarrollo local con Docker

El `docker-compose.yml` usa **Mailpit** por defecto para desarrollo local. Los correos se capturan en [http://localhost:8025](http://localhost:8025) sin enviarse a internet.

Para probar con Gmail en local, añade en tu `.env`:
```bash
EMAIL_PROVIDER=gmail
EMAIL_HOST_USER=micuenta@gmail.com
EMAIL_HOST_PASSWORD=tu-contraseña-de-aplicacion
```
Y comenta o elimina las variables `EMAIL_*` del `environment` del servicio `web` en `docker-compose.yml` para que use las de `.env`.
