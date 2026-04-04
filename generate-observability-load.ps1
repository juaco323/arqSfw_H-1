param(
    [string]$BaseUrl = "http://localhost:8000",
    [int]$Users = 120,
    [int]$PackagesPerUser = 25,
    [int]$ReadCycles = 1500,
    [int]$DelayMs = 2
)

$ErrorActionPreference = "Stop"

function Invoke-Api {
    param(
        [ValidateSet("GET","POST")]
        [string]$Method,
        [string]$Url,
        [object]$Body = $null
    )

    try {
        if ($Method -eq "GET") {
            return Invoke-RestMethod -Method Get -Uri $Url -TimeoutSec 10
        }

        if ($null -ne $Body) {
            $json = $Body | ConvertTo-Json -Depth 10
            return Invoke-RestMethod -Method Post -Uri $Url -Body $json -ContentType "application/json" -TimeoutSec 10
        }

        return Invoke-RestMethod -Method Post -Uri $Url -TimeoutSec 10
    }
    catch {
        Write-Host "[WARN] $Method $Url failed: $($_.Exception.Message)" -ForegroundColor Yellow
        return $null
    }
}

Write-Host "Starting load generation against $BaseUrl" -ForegroundColor Cyan

$health = Invoke-Api -Method GET -Url "$BaseUrl/health"
if ($null -eq $health) {
    Write-Host "Backend is not reachable at $BaseUrl" -ForegroundColor Red
    exit 1
}

Write-Host "Health check OK. Creating traffic..." -ForegroundColor Green

$stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
$userIds = New-Object System.Collections.Generic.List[int]
$trackingCodes = New-Object System.Collections.Generic.List[string]

[int]$okRequests = 0
[int]$failedRequests = 0

# 1) Write traffic: create users
for ($i = 1; $i -le $Users; $i++) {
    $username = "load_user_$i" + "_" + [System.Guid]::NewGuid().ToString("N").Substring(0, 6)
    $email = "$username@example.com"

    $resp = Invoke-Api -Method POST -Url "$BaseUrl/createUser" -Body @{
        username = $username
        email = $email
    }

    if ($null -ne $resp -and $resp.user_id) {
        $userIds.Add([int]$resp.user_id)
        $okRequests++
    }
    else {
        $failedRequests++
    }

    Start-Sleep -Milliseconds $DelayMs
}

# 2) Write traffic: create packages
foreach ($uid in $userIds) {
    for ($j = 1; $j -le $PackagesPerUser; $j++) {
        $resp = Invoke-Api -Method POST -Url "$BaseUrl/createPackage" -Body @{
            user_id = $uid
            package_title = "Load package $uid-$j"
            city = "CDMX"
            location = "Centro"
        }

        if ($null -ne $resp -and $resp.tracking_code) {
            $trackingCodes.Add([string]$resp.tracking_code)
            $okRequests++
        }
        else {
            $failedRequests++
        }

        Start-Sleep -Milliseconds $DelayMs
    }
}

$statuses = @("IN_TRANSIT", "OUT_FOR_DELIVERY", "DELIVERED", "EXCEPTION")

# 3) Mixed traffic: update status + reads
for ($k = 1; $k -le $ReadCycles; $k++) {
    # global reads
    $r1 = Invoke-Api -Method GET -Url "$BaseUrl/getUsers"
    if ($null -ne $r1) { $okRequests++ } else { $failedRequests++ }

    $r2 = Invoke-Api -Method GET -Url "$BaseUrl/getAllPackages"
    if ($null -ne $r2) { $okRequests++ } else { $failedRequests++ }

    if ($trackingCodes.Count -gt 0) {
        $index = Get-Random -Minimum 0 -Maximum $trackingCodes.Count
        $code = $trackingCodes[$index]
        $status = $statuses[(Get-Random -Minimum 0 -Maximum $statuses.Count)]

        $u = Invoke-Api -Method POST -Url "$BaseUrl/updateStatus" -Body @{
            tracking_code = $code
            new_status = $status
            location = "Node-$k"
            note = "load test cycle $k"
        }
        if ($null -ne $u) { $okRequests++ } else { $failedRequests++ }

        $t = Invoke-Api -Method GET -Url "$BaseUrl/getTracking/$code"
        if ($null -ne $t) { $okRequests++ } else { $failedRequests++ }
    }

    Start-Sleep -Milliseconds $DelayMs
}

$stopwatch.Stop()

$total = $okRequests + $failedRequests
$seconds = [Math]::Max(1, [int][Math]::Round($stopwatch.Elapsed.TotalSeconds, 0))
$rps = [Math]::Round($total / $seconds, 2)

Write-Host ""
Write-Host "Load generation finished" -ForegroundColor Cyan
Write-Host "Users created: $($userIds.Count)"
Write-Host "Packages created: $($trackingCodes.Count)"
Write-Host "Successful requests: $okRequests"
Write-Host "Failed requests: $failedRequests"
Write-Host "Total requests: $total"
Write-Host "Elapsed seconds: $seconds"
Write-Host "Approx throughput: $rps req/s"
Write-Host ""
Write-Host "Now open Prometheus and Grafana to inspect charts:" -ForegroundColor Green
Write-Host "- Prometheus: http://localhost:9090"
Write-Host "- Grafana:    http://localhost:3000"