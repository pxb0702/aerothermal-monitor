$out = @()
$out += "=== ELEVATED TEST OUTPUT ==="
$out += "IsAdmin: $([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)"

# 1. NVMe SSD Temperature via StorageReliabilityCounter
try {
    $disk = Get-PhysicalDisk | Where-Object { $_.DeviceId -eq 0 }
    $smart = Get-StorageReliabilityCounter -PhysicalDisk $disk -ErrorAction Stop
    $out += "NVMe Temp: $($smart.Temperature) °C"
    $out += "NVMe Wear: $($smart.Wear) %"
    $out += "NVMe ReadErrors: $($smart.ReadErrorsTotal)"
} catch {
    $out += "StorageReliabilityCounter error: $_"
}

# 2. WMI Thermal Zones
try {
    $tzs = Get-CimInstance -Namespace root/wmi -ClassName MSAcpi_ThermalZoneTemperature -ErrorAction Stop
    foreach ($tz in $tzs) {
        $degC = ($tz.CurrentTemperature - 2732) / 10.0
        $out += "ThermalZone $($tz.InstanceName): $degC °C"
    }
} catch {
    $out += "ThermalZone error: $_"
}

# 3. Lenovo Battery Information
try {
    $bats = Get-CimInstance -Namespace root/wmi -ClassName Lenovo_BatteryInformation -ErrorAction Stop
    foreach ($b in $bats) {
        $out += "Lenovo Battery Info: $($b | Out-String)"
    }
} catch {
    $out += "Lenovo_BatteryInformation error: $_"
}

$out | Out-File -FilePath "$PSScriptRoot\elevated_test_result.txt" -Encoding utf8
