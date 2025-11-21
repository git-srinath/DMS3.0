# PowerShell script to find and stop hung scheduler processes
# Usage: .\stop_scheduler.ps1

Write-Host "Searching for scheduler processes..." -ForegroundColor Yellow

# Find all Python processes
$pythonProcesses = Get-Process | Where-Object {
    $_.ProcessName -like "*python*" -or 
    $_.ProcessName -like "*py*" -or
    $_.Path -like "*python*"
} | Select-Object Id, ProcessName, Path, StartTime, @{Name="CPU";Expression={$_.CPU}}, @{Name="Memory(MB)";Expression={[math]::Round($_.WorkingSet64/1MB,2)}}

if ($pythonProcesses) {
    Write-Host "`nFound Python processes:" -ForegroundColor Cyan
    $pythonProcesses | Format-Table -AutoSize
    
    Write-Host "`nTo stop a specific process, use:" -ForegroundColor Yellow
    Write-Host "  Stop-Process -Id <ProcessId> -Force" -ForegroundColor White
    
    # Ask if user wants to stop all Python processes
    $response = Read-Host "`nDo you want to stop ALL Python processes? (y/N)"
    if ($response -eq 'y' -or $response -eq 'Y') {
        foreach ($proc in $pythonProcesses) {
            try {
                Write-Host "Stopping process $($proc.Id) ($($proc.ProcessName))..." -ForegroundColor Yellow
                Stop-Process -Id $proc.Id -Force
                Write-Host "  Process $($proc.Id) stopped." -ForegroundColor Green
            } catch {
                Write-Host "  Failed to stop process $($proc.Id): $_" -ForegroundColor Red
            }
        }
        Write-Host "`nDone!" -ForegroundColor Green
    } else {
        Write-Host "`nNo processes stopped. Use 'Stop-Process -Id <ProcessId> -Force' to stop specific processes." -ForegroundColor Yellow
    }
} else {
    Write-Host "No Python processes found." -ForegroundColor Green
}

# Also check for processes using port 5000 or common scheduler ports
Write-Host "`nChecking for processes using common ports..." -ForegroundColor Yellow
$netstat = netstat -ano | Select-String "LISTENING"
Write-Host "Active listening ports found. Check for scheduler-related ports." -ForegroundColor Cyan

