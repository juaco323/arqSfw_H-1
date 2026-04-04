param(
    [string]$Root = "C:\Users\jqnfu\Desktop\arqSfw_H-1",
    [int]$Workers = 4,
    [int]$Users = 120,
    [int]$Packages = 25,
    [int]$Reads = 1500,
    [int]$Delay = 2,
    [string]$MicroUrl = "http://localhost:8000",
    [string]$MonolithUrl = "",
    [switch]$CompareWithMonolith
)

$ErrorActionPreference = "Stop"

$loadScript = Join-Path $Root "generate-observability-load.ps1"
if (-not (Test-Path $loadScript)) {
    throw "No existe el script de carga en: $loadScript"
}

function Start-LoadJobs {
    param(
        [string]$Prefix,
        [string]$BaseUrl,
        [int]$Workers,
        [string]$Root,
        [int]$Users,
        [int]$Packages,
        [int]$Reads,
        [int]$Delay
    )

    1..$Workers | ForEach-Object {
        $jobName = "$Prefix$_"
        Start-Job -Name $jobName -ScriptBlock {
            param($root,$baseUrl,$u,$p,$r,$d)
            Set-Location $root
            powershell -ExecutionPolicy Bypass -File .\generate-observability-load.ps1 -BaseUrl $baseUrl -Users $u -PackagesPerUser $p -ReadCycles $r -DelayMs $d
        } -ArgumentList $Root,$BaseUrl,$Users,$Packages,$Reads,$Delay | Out-Null
    }
}

Write-Host "Iniciando carga en microservicios: $MicroUrl" -ForegroundColor Cyan
Start-LoadJobs -Prefix "micro" -BaseUrl $MicroUrl -Workers $Workers -Root $Root -Users $Users -Packages $Packages -Reads $Reads -Delay $Delay

if ($CompareWithMonolith) {
    if ([string]::IsNullOrWhiteSpace($MonolithUrl)) {
        throw "Debes indicar -MonolithUrl cuando usas -CompareWithMonolith"
    }

    Write-Host "Iniciando carga en monolito: $MonolithUrl" -ForegroundColor Yellow
    Start-LoadJobs -Prefix "mono" -BaseUrl $MonolithUrl -Workers $Workers -Root $Root -Users $Users -Packages $Packages -Reads $Reads -Delay $Delay
}

Get-Job | Wait-Job | Out-Null
Get-Job | Receive-Job
Get-Job | Remove-Job

Write-Host "Carga finalizada." -ForegroundColor Green
