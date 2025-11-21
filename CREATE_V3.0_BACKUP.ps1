# Version 3.0 Backup Script
# Run this script from the DWTOOL root directory
# Usage: .\CREATE_V3.0_BACKUP.ps1

Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "Version 3.0 Backup Script" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host ""

$backupDir = "version_backups\v3.0"

# Create backup directories if they don't exist
Write-Host "Creating backup directories..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path "$backupDir\backend\modules\mapper" | Out-Null
New-Item -ItemType Directory -Force -Path "$backupDir\backend\database" | Out-Null
New-Item -ItemType Directory -Force -Path "$backupDir\frontend\src\app\mapper_module" | Out-Null
New-Item -ItemType Directory -Force -Path "$backupDir\docs" | Out-Null

# Copy backend files
Write-Host "Copying backend files..." -ForegroundColor Yellow
Copy-Item -Path "backend\modules\mapper\pkgdwmapr_python.py" -Destination "$backupDir\backend\modules\mapper\" -Force
Copy-Item -Path "backend\modules\mapper\mapper.py" -Destination "$backupDir\backend\modules\mapper\" -Force
Copy-Item -Path "backend\modules\helper_functions.py" -Destination "$backupDir\backend\modules\" -Force
Copy-Item -Path "backend\database\dbconnect.py" -Destination "$backupDir\backend\database\" -Force

# Copy frontend files
Write-Host "Copying frontend files..." -ForegroundColor Yellow
Copy-Item -Path "frontend\src\app\mapper_module\ReferenceForm.js" -Destination "$backupDir\frontend\src\app\mapper_module\" -Force

# Copy documentation
Write-Host "Copying documentation..." -ForegroundColor Yellow
Copy-Item -Path "TARGET_CONNECTION_IMPLEMENTATION_COMPLETE.md" -Destination "$backupDir\docs\" -Force -ErrorAction SilentlyContinue
Copy-Item -Path "TARGET_CONNECTION_PROGRESS.md" -Destination "$backupDir\docs\" -Force -ErrorAction SilentlyContinue
Copy-Item -Path "TESTING_GUIDE.md" -Destination "$backupDir\docs\" -Force -ErrorAction SilentlyContinue

# Verify backup
Write-Host ""
Write-Host "Verifying backup..." -ForegroundColor Yellow
$backupFiles = Get-ChildItem -Path $backupDir -Recurse -File
Write-Host "Total files backed up: $($backupFiles.Count)" -ForegroundColor Green

Write-Host ""
Write-Host "Backup file list:" -ForegroundColor Cyan
$backupFiles | ForEach-Object {
    $relativePath = $_.FullName.Replace((Get-Location).Path + "\", "")
    Write-Host "  ✓ $relativePath" -ForegroundColor Green
}

# Create ZIP archive
Write-Host ""
Write-Host "Creating ZIP archive..." -ForegroundColor Yellow
$zipPath = "version_backups\version_3.0_backup_$(Get-Date -Format 'yyyyMMdd_HHmmss').zip"
Compress-Archive -Path "$backupDir\*" -DestinationPath $zipPath -Force

Write-Host ""
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "✅ Backup completed successfully!" -ForegroundColor Green
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host ""
Write-Host "Backup location:" -ForegroundColor Cyan
Write-Host "  Folder: $backupDir" -ForegroundColor White
Write-Host "  ZIP: $zipPath" -ForegroundColor White
Write-Host ""
Write-Host "To restore this version, see:" -ForegroundColor Cyan
Write-Host "  $backupDir\VERSION_3.0_README.md" -ForegroundColor White
Write-Host "  $backupDir\BACKUP_MANIFEST.txt" -ForegroundColor White
Write-Host ""

