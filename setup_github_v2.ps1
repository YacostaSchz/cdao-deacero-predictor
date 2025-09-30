# Script de Setup para GitHub - CDO DeAcero Project
# Version 2 - Corregida

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Setup GitHub - CDO DeAcero Project   " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Verificar directorio actual
$currentDir = Get-Location
Write-Host "Directorio actual: $currentDir" -ForegroundColor Yellow
Write-Host ""

# Paso 1: Backup del .gitignore original
Write-Host "PASO 1: Backup del .gitignore original..." -ForegroundColor Green
if (Test-Path ".gitignore") {
    Copy-Item ".gitignore" ".gitignore.original.backup" -Force
    Write-Host "[OK] Backup creado: .gitignore.original.backup" -ForegroundColor Green
} else {
    Write-Host "[INFO] No hay .gitignore previo" -ForegroundColor Yellow
}

# Paso 2: Usar el .gitignore para entrega
Write-Host ""
Write-Host "PASO 2: Configurando .gitignore para entrega..." -ForegroundColor Green
if (Test-Path ".gitignore.delivery") {
    Copy-Item ".gitignore.delivery" ".gitignore" -Force
    Write-Host "[OK] .gitignore actualizado" -ForegroundColor Green
} else {
    Write-Host "[ADVERTENCIA] No se encontro .gitignore.delivery" -ForegroundColor Yellow
    Write-Host "Continuando con .gitignore actual..." -ForegroundColor Yellow
}

# Paso 3: Verificar Git
Write-Host ""
Write-Host "PASO 3: Verificando instalacion de Git..." -ForegroundColor Green
try {
    $gitVersion = git --version 2>$null
    Write-Host "[OK] Git instalado: $gitVersion" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Git no esta instalado" -ForegroundColor Red
    Write-Host "Instala Git desde: https://git-scm.com/download/win" -ForegroundColor Yellow
    Write-Host "Despues de instalar, reinicia PowerShell y vuelve a ejecutar." -ForegroundColor Yellow
    Read-Host "Presiona Enter para salir"
    exit
}

# Paso 4: Verificar si ya es un repositorio Git
Write-Host ""
Write-Host "PASO 4: Verificando estado del repositorio..." -ForegroundColor Green
if (Test-Path ".git") {
    Write-Host "[INFO] Ya existe un repositorio Git" -ForegroundColor Yellow
    $respuesta = Read-Host "Quieres reinicializarlo? (S/N)"
    if ($respuesta -eq "S" -or $respuesta -eq "s") {
        Remove-Item -Recurse -Force .git
        git init
        Write-Host "[OK] Repositorio reinicializado" -ForegroundColor Green
    } else {
        Write-Host "[INFO] Usando repositorio existente" -ForegroundColor Yellow
    }
} else {
    git init
    Write-Host "[OK] Repositorio Git inicializado" -ForegroundColor Green
}

# Paso 5: Configurar Git
Write-Host ""
Write-Host "PASO 5: Configurando Git..." -ForegroundColor Green
$gitUser = git config user.name 2>$null
if ([string]::IsNullOrEmpty($gitUser)) {
    git config user.name "Yazmin Acosta"
    git config user.email "dra.acostas@gmail.com"
    Write-Host "[OK] Git configurado como: Yazmin Acosta" -ForegroundColor Green
} else {
    Write-Host "[OK] Git ya configurado como: $gitUser" -ForegroundColor Green
}

# Paso 6: Agregar archivos
Write-Host ""
Write-Host "PASO 6: Agregando archivos al staging..." -ForegroundColor Green
Write-Host "Esto puede tomar unos segundos..." -ForegroundColor Yellow
git add .
Write-Host "[OK] Archivos agregados" -ForegroundColor Green

# Paso 7: Mostrar archivos que se van a subir
Write-Host ""
Write-Host "Primeros 20 archivos a subir:" -ForegroundColor Cyan
git diff --cached --name-only 2>$null | Select-Object -First 20 | ForEach-Object {
    Write-Host "   - $_" -ForegroundColor Gray
}

# Paso 8: Commit
Write-Host ""
Write-Host "PASO 7: Creando commit..." -ForegroundColor Green
$commitMsg = "Entrega final - Prueba Tecnica CDO DeAcero - API Prediccion Varilla Corrugada"
git commit -m $commitMsg
Write-Host "[OK] Commit creado exitosamente" -ForegroundColor Green

# Paso 9: Instrucciones finales
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   PREPARACION COMPLETADA" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "SIGUIENTES PASOS:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Ve a GitHub.com y crea un nuevo repositorio:" -ForegroundColor White
Write-Host "   - Nombre: cdao-deacero-predictor" -ForegroundColor Gray
Write-Host "   - Privado: SI" -ForegroundColor Gray
Write-Host "   - NO inicialices con README" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Ejecuta estos comandos (reemplaza TU-USUARIO):" -ForegroundColor White
Write-Host ""
Write-Host "   git remote add origin https://github.com/TU-USUARIO/cdao-deacero-predictor.git" -ForegroundColor Cyan
Write-Host "   git branch -M main" -ForegroundColor Cyan
Write-Host "   git push -u origin main" -ForegroundColor Cyan
Write-Host ""
Write-Host "3. Actualiza CORREO_ENTREGA.md con el link del repo" -ForegroundColor White
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Preguntar si abrir GitHub
$openGitHub = Read-Host "Quieres abrir GitHub.com ahora? (S/N)"
if ($openGitHub -eq "S" -or $openGitHub -eq "s") {
    Start-Process "https://github.com/new"
    Write-Host "[OK] Abriendo GitHub en el navegador..." -ForegroundColor Green
}

Write-Host ""
Write-Host "Script completado. Presiona Enter para salir..." -ForegroundColor Gray
Read-Host
