# 🚀 Instrucciones Paso a Paso para Subir a GitHub

**Última actualización**: 2025-09-30  
**Tiempo estimado**: 10-15 minutos

---

## ✅ Prerequisitos

- [x] Tener cuenta en GitHub (si no, créala en https://github.com/signup)
- [x] Tener Git instalado (verifica con `git --version` en PowerShell)
  - Si no está instalado: https://git-scm.com/download/win

---

## 🎯 Método 1: AUTOMÁTICO (Recomendado)

### Ejecutar el Script PowerShell

```powershell
# 1. Abrir PowerShell en la carpeta del proyecto
cd C:\Users\draac\Documents\cursor\cdao_model

# 2. Permitir ejecución de scripts (solo primera vez)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 3. Ejecutar el script
.\setup_github.ps1
```

El script hará:
- ✅ Backup de tu .gitignore actual
- ✅ Configurar .gitignore para incluir archivos importantes
- ✅ Inicializar Git
- ✅ Agregar todos los archivos
- ✅ Crear el primer commit
- ✅ Mostrarte los siguientes pasos

---

## 🎯 Método 2: MANUAL (Paso a Paso)

### PASO 1: Preparar el Repositorio Local

```powershell
# Abrir PowerShell en la carpeta del proyecto
cd C:\Users\draac\Documents\cursor\cdao_model

# Backup del .gitignore original
Copy-Item .gitignore .gitignore.original.backup

# Usar el .gitignore para entrega
Copy-Item .gitignore.delivery .gitignore

# Inicializar Git (si no lo has hecho)
git init

# Configurar Git (si es primera vez)
git config user.name "Yazmin Acosta"
git config user.email "dra.acostas@gmail.com"
```

### PASO 2: Agregar Archivos y Crear Commit

```powershell
# Ver qué archivos se van a incluir
git status

# Agregar todos los archivos
git add .

# Crear el commit
git commit -m "Entrega final - Prueba Tecnica CDO DeAcero - API Prediccion Varilla Corrugada"
```

### PASO 3: Crear Repositorio en GitHub

1. Ve a https://github.com/new
2. Configura:
   - **Repository name**: `cdao-deacero-predictor`
   - **Description**: `Prueba Tecnica CDO DeAcero - API Prediccion Varilla Corrugada - MAPE 1.53%`
   - **Privacy**: ⭐ **PRIVATE** (importante para proteger tu trabajo)
   - **Initialize**: ❌ NO marcar README, .gitignore ni licencia
3. Click "Create repository"

### PASO 4: Conectar y Subir

```powershell
# Reemplaza TU-USUARIO con tu usuario de GitHub
git remote add origin https://github.com/TU-USUARIO/cdao-deacero-predictor.git

# Renombrar branch a main
git branch -M main

# Subir a GitHub
git push -u origin main
```

**Ejemplo real**:
```powershell
# Si tu usuario es "yazminacosta"
git remote add origin https://github.com/yazminacosta/cdao-deacero-predictor.git
git branch -M main
git push -u origin main
```

---

## 🔐 PASO 5: Dar Acceso al Equipo Evaluador

### Opción A: Hacer el Repo Público (No Recomendado)

```
Settings → Change visibility → Make public
```

⚠️ **NO recomendado**: Otros candidatos podrían ver tu trabajo.

### Opción B: Invitar Colaboradores (Recomendado)

```
Settings → Collaborators → Add people
```

Invita a los emails del equipo evaluador con rol "Read".

### Opción C: Compartir Link Privado en el Correo

```
En tu correo menciona:
"Repositorio privado: https://github.com/TU-USUARIO/cdao-deacero-predictor
Favor de indicar usuario de GitHub para otorgar acceso."
```

---

## 📝 PASO 6: Actualizar el Correo de Entrega

Edita `CORREO_ENTREGA.md` y reemplaza:

```markdown
**Repositorio de Código**:
```
C:\Users\draac\Documents\cursor\cdao_model
```
```

Por:

```markdown
**Repositorio de Código (GitHub)**:
```
https://github.com/TU-USUARIO/cdao-deacero-predictor
```

**Nota**: Repositorio privado. Favor de indicar los usuarios de GitHub del equipo evaluador para otorgar acceso de lectura.

**Incluye**:
- ✅ Código fuente completo (~14,500 líneas)
- ✅ Documentación exhaustiva (25+ archivos)
- ✅ Modelo entrenado (TWO_STAGE_MODEL.pkl)
- ✅ Datasets procesados
- ✅ Terraform infrastructure as code
- ✅ Scripts de testing (Postman collection)
```

---

## 🔍 Verificación Final

Verifica que tu repositorio en GitHub tenga:

### ✅ Archivos Importantes Presentes

```bash
# En GitHub, verifica que existan:
✅ README.md
✅ DOCUMENTACION_COMPLETA_ENTREGA.md
✅ ENTREGA_FINAL.md
✅ CORREO_ENTREGA.md
✅ parte_tecnica/03_feature_engineering/outputs/TWO_STAGE_MODEL.pkl
✅ parte_tecnica/03_feature_engineering/outputs/features_dataset_latest.csv
✅ parte_tecnica/04_api_exposure/terraform/ (archivos .tf)
✅ docs/requirement/reto_tecnico.txt
```

### ✅ Tamaño Aceptable

- GitHub tiene límite de ~100MB por archivo
- Repositorio total debería ser <500MB
- Si es muy grande, considera Git LFS o Google Drive como alternativa

---

## 🆘 Solución de Problemas

### Problema: "Git no reconocido como comando"

**Solución**: Instalar Git
```powershell
# Descargar de: https://git-scm.com/download/win
# Después de instalar, REINICIAR PowerShell
```

### Problema: "Repository too large"

**Solución 1**: Verificar archivos grandes
```powershell
# Ver archivos >10MB
git ls-files -z | xargs -0 du -h | sort -h | tail -20
```

**Solución 2**: Usar .gitignore más estricto
```powershell
# Excluir archivos muy grandes específicos
echo "ruta/al/archivo/grande.csv" >> .gitignore
git rm --cached ruta/al/archivo/grande.csv
git commit --amend
```

**Solución 3**: Usar Google Drive en su lugar (ver abajo)

### Problema: "Permission denied (publickey)"

**Solución**: Usar HTTPS en lugar de SSH
```powershell
# URL debe empezar con https://
git remote set-url origin https://github.com/TU-USUARIO/cdao-deacero-predictor.git
```

### Problema: "Error al hacer push"

**Solución**: Verificar credenciales
```powershell
# GitHub puede pedir usuario y token
# Token: Settings → Developer settings → Personal access tokens
```

---

## 🎯 Plan B: Google Drive (Si GitHub falla)

Si el repositorio es muy grande o tienes problemas:

```powershell
# Crear ZIP del proyecto
Compress-Archive -Path * -DestinationPath ..\cdao_deacero_yacosta.zip `
  -Exclude venv,__pycache__,.git

# Subir el ZIP a Google Drive
# Link a compartir en el correo
```

---

## 📞 Resumen de URLs para el Correo

Después de subir a GitHub, tendrás:

```markdown
**API Desplegado**: 
https://steel-predictor-190635835043.us-central1.run.app

**Repositorio de Código**:
https://github.com/TU-USUARIO/cdao-deacero-predictor

**Documentación Interactiva**:
https://steel-predictor-190635835043.us-central1.run.app/docs
```

---

## ✅ Checklist Final

Antes de enviar el correo, verifica:

- [ ] Repositorio creado en GitHub
- [ ] Código subido completamente
- [ ] Archivos importantes verificados (modelo .pkl, CSVs, docs)
- [ ] Privacidad configurada (PRIVATE)
- [ ] README.md visible y completo
- [ ] Correo actualizado con link del repositorio
- [ ] Plan para dar acceso a evaluadores (invitación o mencionar en correo)

---

**¡Listo para enviar!** 🚀

---

*Si tienes algún problema, revisa la sección de Solución de Problemas o considera usar Google Drive como plan B.*
