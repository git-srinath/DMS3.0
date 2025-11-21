# Version 3.0 Restore Script
# Run this script from the DWTOOL root directory
# Usage: .\RESTORE_V3.0_BACKUP.ps1

Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "Version 3.0 Restore Script" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host ""

$backupDir = "version_backups\v3.0"

# Check if backup exists
if (-not (Test-Path $backupDir)) {
    Write-Host "❌ ERROR: Backup directory not found: $backupDir" -ForegroundColor Red
    Write-Host "Please ensure the backup exists before restoring." -ForegroundColor Yellow
    exit 1
}

# Confirm with user
Write-Host "⚠️  WARNING: This will overwrite your current files!" -ForegroundColor Yellow
Write-Host ""
Write-Host "The following files will be restored from Version 3.0:" -ForegroundColor Cyan
Write-Host "  - backend/modules/mapper/pkgdwmapr_python.py" -ForegroundColor White
Write-Host "  - backend/modules/mapper/mapper.py" -ForegroundColor White
Write-Host "  - backend/modules/helper_functions.py" -ForegroundColor White
Write-Host "  - backend/database/dbconnect.py" -ForegroundColor White
Write-Host "  - frontend/src/app/mapper_module/ReferenceForm.js" -ForegroundColor White
Write-Host ""
$confirm = Read-Host "Do you want to continue? (yes/no)"

if ($confirm -ne "yes") {
    Write-Host "Restore cancelled." -ForegroundColor Yellow
    exit 0
}

# Create backup of current state before restoring
Write-Host ""
Write-Host "Creating backup of current state..." -ForegroundColor Yellow
$currentBackupDir = "version_backups\before_restore_v3.0_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
New-Item -ItemType Directory -Force -Path "$currentBackupDir\backend\modules\mapper" | Out-Null
New-Item -ItemType Directory -Force -Path "$currentBackupDir\backend\database" | Out-Null
New-Item -ItemType Directory -Force -Path "$currentBackupDir\frontend\src\app\mapper_module" | Out-Null

Copy-Item -Path "backend\modules\mapper\*.py" -Destination "$currentBackupDir\backend\modules\mapper\" -Force -ErrorAction SilentlyContinue
Copy-Item -Path "backend\modules\helper_functions.py" -Destination "$currentBackupDir\backend\modules\" -Force -ErrorAction SilentlyContinue
Copy-Item -Path "backend\database\dbconnect.py" -Destination "$currentBackupDir\backend\database\" -Force -ErrorAction SilentlyContinue
Copy-Item -Path "frontend\src\app\mapper_module\ReferenceForm.js" -Destination "$currentBackupDir\frontend\src\app\mapper_module\" -Force -ErrorAction SilentlyContinue

Write-Host "✓ Current state backed up to: $currentBackupDir" -ForegroundColor Green

# Restore files from v3.0 backup
Write-Host ""
Write-Host "Restoring files from Version 3.0..." -ForegroundColor Yellow

Copy-Item -Path "$backupDir\backend\modules\mapper\pkgdwmapr_python.py" -Destination "backend\modules\mapper\" -Force
Copy-Item -Path "$backupDir\backend\modules\mapper\mapper.py" -Destination "backend\modules\mapper\" -Force
Copy-Item -Path "$backupDir\backend\modules\helper_functions.py" -Destination "backend\modules\" -Force
Copy-Item -Path "$backupDir\backend\database\dbconnect.py" -Destination "backend\database\" -Force
Copy-Item -Path "$backupDir\frontend\src\app\mapper_module\ReferenceForm.js" -Destination "frontend\src\app\mapper_module\" -Force

Write-Host ""
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "✅ Version 3.0 restored successfully!" -ForegroundColor Green
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Restart your backend server" -ForegroundColor White
Write-Host "  2. Restart your frontend server" -ForegroundColor White
Write-Host "  3. Verify the application works correctly" -ForegroundColor White
Write-Host ""
Write-Host "Your previous files were backed up to:" -ForegroundColor Cyan
Write-Host "  $currentBackupDir" -ForegroundColor White
Write-Host ""

