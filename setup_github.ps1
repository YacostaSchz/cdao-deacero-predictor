# 🚀 Script de Setup para GitHub
# Prueba Técnica CDO DeAcero - Yazmín Acosta

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Setup GitHub - CDO DeAcero Project   " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Verificar que estamos en el directorio correcto
$currentDir = Get-Location
Write-Host "📁 Directorio actual: $currentDir" -ForegroundColor Yellow
Write-Host ""

# Paso 1: Backup del .gitignore original
Write-Host "PASO 1: Backup del .gitignore original..." -ForegroundColor Green
if (Test-Path ".gitignore") {
    Copy-Item ".gitignore" ".gitignore.original.backup"
    Write-Host "✅ Backup creado: .gitignore.original.backup" -ForegroundColor Green
}

# Paso 2: Usar el .gitignore para entrega
Write-Host ""
Write-Host "PASO 2: Configurando .gitignore para entrega..." -ForegroundColor Green
if (Test-Path ".gitignore.delivery") {
    Copy-Item ".gitignore.delivery" ".gitignore" -Force
    Write-Host "✅ .gitignore actualizado para permitir archivos de entrega" -ForegroundColor Green
} else {
    Write-Host "⚠️  No se encontró .gitignore.delivery" -ForegroundColor Yellow
}

# Paso 3: Verificar Git
Write-Host ""
Write-Host "PASO 3: Verificando instalación de Git..." -ForegroundColor Green
$gitInstalled = Get-Command git -ErrorAction SilentlyContinue
if ($gitInstalled) {
    $gitVersion = git --version
    Write-Host "✅ Git instalado: $gitVersion" -ForegroundColor Green
} else {
    Write-Host "❌ Git no está instalado. Instálalo desde: https://git-scm.com/download/win" -ForegroundColor Red
    Write-Host "   Después de instalar, reinicia PowerShell y vuelve a ejecutar este script." -ForegroundColor Yellow
    exit
}

# Paso 4: Verificar si ya es un repositorio Git
Write-Host ""
Write-Host "PASO 4: Verificando estado del repositorio..." -ForegroundColor Green
if (Test-Path ".git") {
    Write-Host "⚠️  Ya existe un repositorio Git. Saltando inicialización." -ForegroundColor Yellow
} else {
    Write-Host "Inicializando repositorio Git..." -ForegroundColor Yellow
    git init
    Write-Host "✅ Repositorio Git inicializado" -ForegroundColor Green
}

# Paso 5: Configurar Git (si es necesario)
Write-Host ""
Write-Host "PASO 5: Configurando Git..." -ForegroundColor Green
$gitUser = git config user.name
if ([string]::IsNullOrEmpty($gitUser)) {
    Write-Host "⚠️  Git no está configurado. Configurando..." -ForegroundColor Yellow
    git config user.name "Yazmin Acosta"
    git config user.email "dra.acostas@gmail.com"
    Write-Host "✅ Git configurado" -ForegroundColor Green
} else {
    Write-Host "✅ Git ya configurado como: $gitUser" -ForegroundColor Green
}

# Paso 6: Agregar archivos
Write-Host ""
Write-Host "PASO 6: Agregando archivos al staging..." -ForegroundColor Green
git add .
$filesAdded = git diff --cached --name-only | Measure-Object -Line
Write-Host "✅ Archivos agregados: $($filesAdded.Lines)" -ForegroundColor Green

# Paso 7: Mostrar archivos que se van a subir (primeros 20)
Write-Host ""
Write-Host "📋 Primeros 20 archivos a subir:" -ForegroundColor Cyan
git diff --cached --name-only | Select-Object -First 20 | ForEach-Object {
    Write-Host "   - $_" -ForegroundColor Gray
}
Write-Host "   ..." -ForegroundColor Gray

# Paso 8: Commit
Write-Host ""
Write-Host "PASO 7: Creando commit..." -ForegroundColor Green
$commitMessage = "Entrega final - Prueba Tecnica CDO DeAcero - API Prediccion Varilla Corrugada"
git commit -m "$commitMessage"
Write-Host "✅ Commit creado" -ForegroundColor Green

# Paso 9: Verificar el tamaño del repositorio
Write-Host ""
Write-Host "PASO 8: Verificando tamaño del repositorio..." -ForegroundColor Green
$repoSize = (Get-ChildItem -Recurse -Force -ErrorAction SilentlyContinue | 
    Where-Object { $_.FullName -notmatch '\\\.git\\' -and $_.FullName -notmatch '\\venv\\' } | 
    Measure-Object -Property Length -Sum).Sum / 1MB
Write-Host "📊 Tamaño estimado: $([math]::Round($repoSize, 2)) MB" -ForegroundColor Cyan

if ($repoSize -gt 100) {
    Write-Host "⚠️  ADVERTENCIA: El repositorio es muy grande (>100MB)" -ForegroundColor Yellow
    Write-Host "   GitHub tiene un límite de ~100MB por repositorio gratuito." -ForegroundColor Yellow
    Write-Host "   Considera usar Git LFS para archivos grandes o Google Drive como alternativa." -ForegroundColor Yellow
}

# Paso 10: Instrucciones finales
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   ✅ PREPARACIÓN COMPLETADA" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📌 SIGUIENTES PASOS MANUALES:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Ve a GitHub.com y crea un nuevo repositorio:" -ForegroundColor White
Write-Host "   - Nombre sugerido: cdao-deacero-predictor" -ForegroundColor Gray
Write-Host "   - Descripción: Prueba Tecnica CDO DeAcero - API Prediccion Varilla Corrugada" -ForegroundColor Gray
Write-Host "   - Privacidad: PRIVADO (para proteger tu trabajo)" -ForegroundColor Gray
Write-Host "   - NO inicialices con README, .gitignore o licencia" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Copia la URL del repositorio (algo como: https://github.com/tu-usuario/cdao-deacero-predictor.git)" -ForegroundColor White
Write-Host ""
Write-Host "3. Ejecuta estos comandos en PowerShell:" -ForegroundColor White
Write-Host ""
Write-Host "   git remote add origin https://github.com/TU-USUARIO/cdao-deacero-predictor.git" -ForegroundColor Cyan
Write-Host "   git branch -M main" -ForegroundColor Cyan
Write-Host "   git push -u origin main" -ForegroundColor Cyan
Write-Host ""
Write-Host "4. Otorga acceso al equipo evaluador:" -ForegroundColor White
Write-Host "   - En GitHub: Settings → Collaborators → Add people" -ForegroundColor Gray
Write-Host "   - O comparte el link del repo privado en tu correo" -ForegroundColor Gray
Write-Host ""
Write-Host "5. Actualiza tu CORREO_ENTREGA.md con el link del repositorio" -ForegroundColor White
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Presiona Enter para salir..." -ForegroundColor Gray
Read-Host

# Opcional: Abrir GitHub en el navegador
$openGitHub = Read-Host "¿Quieres abrir GitHub.com ahora? (S/N)"
if ($openGitHub -eq "S" -or $openGitHub -eq "s") {
    Start-Process "https://github.com/new"
}
