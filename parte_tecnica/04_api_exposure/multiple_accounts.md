# Gestión de Múltiples Cuentas en Google Cloud Platform

Esta guía te ayudará a configurar y gestionar múltiples cuentas de Google Cloud Platform, separando tu entorno personal y laboral.

## Configuraciones Creadas

Ya se han creado las siguientes configuraciones en tu sistema:

- **default**: La configuración por defecto
- **personal**: Para tu cuenta personal
- **trabajo**: Para tu cuenta laboral

## Configuración Inicial

### 1. Configurar Cuenta Personal

```bash
# Activar la configuración personal
gcloud config configurations activate personal

# Iniciar sesión con tu cuenta personal
gcloud auth login

# Configurar el proyecto predeterminado (reemplaza con tu ID de proyecto)
gcloud config set project TU_PROYECTO_PERSONAL

# Configurar la región predeterminada
gcloud config set compute/region us-central1
gcloud config set compute/zone us-central1-a
```

### 2. Configurar Cuenta Laboral

```bash
# Activar la configuración laboral
gcloud config configurations activate trabajo

# Iniciar sesión con tu cuenta laboral
gcloud auth login

# Configurar el proyecto predeterminado (reemplaza con tu ID de proyecto)
gcloud config set project TU_PROYECTO_TRABAJO

# Configurar la región predeterminada
gcloud config set compute/region us-central1
gcloud config set compute/zone us-central1-a
```

## Uso Diario

### Cambiar entre Cuentas

```bash
# Cambiar a cuenta personal
gcloud config configurations activate personal

# Cambiar a cuenta laboral
gcloud config configurations activate trabajo

# Ver la configuración activa actual
gcloud config configurations list
```

### Verificar la Configuración Actual

```bash
# Ver la configuración actual
gcloud config list

# Ver todas las propiedades
gcloud config list --all
```

## Autenticación para Aplicaciones

### Crear Credenciales de Aplicación Predeterminadas (ADC)

Para tu cuenta personal:
```bash
# Activar la configuración personal
gcloud config configurations activate personal

# Crear credenciales de aplicación
gcloud auth application-default login
```

Para tu cuenta laboral:
```bash
# Activar la configuración laboral
gcloud config configurations activate trabajo

# Crear credenciales de aplicación
gcloud auth application-default login
```

### Credenciales para Terraform

Para usar distintas credenciales con Terraform:

1. Para la cuenta personal, usar las ADC predeterminadas.
2. Para la cuenta laboral, exportar credenciales específicas:

```bash
# Activar configuración laboral
gcloud config configurations activate trabajo

# Crear archivo de credenciales de servicio
gcloud iam service-accounts create terraform-trabajo \
  --description="Terraform Service Account para cuenta laboral" \
  --display-name="Terraform Trabajo"

# Otorgar permisos necesarios
gcloud projects add-iam-policy-binding TU_PROYECTO_TRABAJO \
  --member="serviceAccount:terraform-trabajo@TU_PROYECTO_TRABAJO.iam.gserviceaccount.com" \
  --role="roles/editor"

# Crear y descargar la clave
gcloud iam service-accounts keys create ~/.config/gcloud/application_default_credentials_trabajo.json \
  --iam-account=terraform-trabajo@TU_PROYECTO_TRABAJO.iam.gserviceaccount.com
```

## Aliases útiles para ZSH

Añade estos alias a tu archivo `.zshrc` para facilitar el cambio entre cuentas:

```bash
# Aliases para GCP
alias gcpersonal='gcloud config configurations activate personal && echo "Cuenta personal activada"'
alias gctrabajo='gcloud config configurations activate trabajo && echo "Cuenta laboral activada"'
alias gcwho='gcloud config configurations list'
alias gcinfo='gcloud config list'
```

## Uso con Kubernetes

Si trabajas con GKE en ambas cuentas:

```bash
# Obtener credenciales para cluster personal
gcloud config configurations activate personal
gcloud container clusters get-credentials cluster-personal --region us-central1

# Obtener credenciales para cluster laboral
gcloud config configurations activate trabajo
gcloud container clusters get-credentials cluster-trabajo --region us-central1

# Ver contextos disponibles
kubectl config get-contexts

# Cambiar entre contextos
kubectl config use-context gke_TU_PROYECTO_PERSONAL_us-central1_cluster-personal
kubectl config use-context gke_TU_PROYECTO_TRABAJO_us-central1_cluster-trabajo
```

## Integración con VSCode

Para facilitar el desarrollo, configura VSCode:

1. Instala la extensión "Cloud Code" para VSCode
2. Configura perfiles separados para cada cuenta:
   - Un perfil con variables de entorno para tu cuenta personal
   - Otro perfil con variables de entorno para tu cuenta laboral

## Solución de Problemas Comunes

### Conflictos de Credenciales

Si tienes problemas con credenciales mezcladas:

```bash
# Limpiar todas las credenciales almacenadas
gcloud auth revoke --all

# Volver a iniciar sesión
gcloud config configurations activate personal
gcloud auth login
gcloud auth application-default login

gcloud config configurations activate trabajo
gcloud auth login
gcloud auth application-default login
```

### Verificación de Tokens

Para ver qué tokens de acceso estás usando actualmente:

```bash
# Ver tokens activos
gcloud auth list

# Ver información detallada
gcloud auth print-access-token
``` 