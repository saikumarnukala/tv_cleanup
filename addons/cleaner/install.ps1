param(
    [string]$TvHost = $env:TV_HOST
)
$ErrorActionPreference = 'Stop'
$OutputEncoding = New-Object System.Text.UTF8Encoding $false

if (-not $TvHost) {
    $devPath = "$PSScriptRoot\..\..\.local_devices.json"
    if (Test-Path $devPath) {
        $devs = Get-Content $devPath | ConvertFrom-Json
        $names = @($devs.PSObject.Properties.Name)
        Write-Host "============================================="
        Write-Host "     Install TV Cleaner to TV               "
        Write-Host "============================================="
        for ($i = 0; $i -lt $names.Count; $i++) {
            Write-Host "  $($i + 1). $($names[$i]) ($($devs.($names[$i])))"
        }
        $sel = Read-Host "Select TV (1-$($names.Count))"
        $idx = [int]$sel - 1
        if ($idx -ge 0 -and $idx -lt $names.Count) {
            $TvHost = $devs.($names[$idx])
        }
    }
    if (-not $TvHost) {
        $TvHost = Read-Host "Enter TV IP address"
    }
}

$env:TV_HOST = $TvHost
$py = "$PSScriptRoot\..\..\tools\venv\Scripts\python.exe"
$apk = "$PSScriptRoot\app\build\outputs\apk\release\app-release.apk"

if (-not (Test-Path $apk)) {
    Write-Host "Building release APK first..."
    $env:JAVA_HOME = "C:\Users\saikumar\AppData\Local\Programs\Eclipse Adoptium\jdk-17.0.17.10-hotspot"
    $env:ANDROID_HOME = "C:\Users\saikumar\scoop\apps\android-clt\current"
    & "$PSScriptRoot\..\..\launcher\gradlew.bat" -p "$PSScriptRoot" assembleRelease -q
}

Write-Host "Connecting to $TvHost..."
& $py "$PSScriptRoot\..\..\tools\tv.py" --probe
if ($LASTEXITCODE -ne 0) {
    Write-Host "[!] Could not reach $TvHost. Make sure ADB/USB Debugging is turned ON on the TV."
    exit 1
}

Write-Host "Uploading TV Cleaner APK (~13 KB)..."
& $py "$PSScriptRoot\..\..\tools\b64push.py" $apk "/data/local/tmp/cleaner.apk"

Write-Host "Installing package com.clean.tvcleaner..."
& $py "$PSScriptRoot\..\..\tools\tv.py" "pm install -r /data/local/tmp/cleaner.apk; rm /data/local/tmp/cleaner.apk"

Write-Host ""
Write-Host "[OK] TV Cleaner is now installed on $TvHost!"
Write-Host "     You can launch it from your TV Apps or Home Screen."
