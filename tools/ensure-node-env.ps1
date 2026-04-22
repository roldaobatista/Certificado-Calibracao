if (-not $env:USERPROFILE) {
    $env:USERPROFILE = [Environment]::GetFolderPath("UserProfile")
}

if (-not $env:HOME -and $env:USERPROFILE) {
    $env:HOME = $env:USERPROFILE
}

$defaults = @{
    APPDATA      = if ($env:USERPROFILE) { Join-Path $env:USERPROFILE "AppData\Roaming" } else { $null }
    LOCALAPPDATA = if ($env:USERPROFILE) { Join-Path $env:USERPROFILE "AppData\Local" } else { $null }
    PROGRAMDATA  = "C:\ProgramData"
    SystemRoot   = "C:\Windows"
    windir       = "C:\Windows"
    TEMP         = if ($env:USERPROFILE) { Join-Path $env:USERPROFILE "AppData\Local\Temp" } else { $null }
    TMP          = if ($env:USERPROFILE) { Join-Path $env:USERPROFILE "AppData\Local\Temp" } else { $null }
}

foreach ($entry in $defaults.GetEnumerator()) {
    if (-not (Get-Item "Env:$($entry.Key)" -ErrorAction SilentlyContinue) -and $entry.Value) {
        $ExecutionContext.SessionState.PSVariable.Set("env:$($entry.Key)", $entry.Value)
    }
}

$extraBins = @(
    (Join-Path $env:APPDATA "npm"),
    (Join-Path $env:USERPROFILE ".local\bin")
) | Where-Object { $_ -and (Test-Path $_) }

foreach ($bin in $extraBins) {
    if (($env:PATH -split ";") -notcontains $bin) {
        $env:PATH = (($env:PATH -split ";") + $bin) -join ";"
    }
}

$commandArgs = @($args)

if ($commandArgs.Count -gt 0 -and $commandArgs[0] -in @("--", "--%")) {
    $commandArgs = if ($commandArgs.Count -gt 1) { $commandArgs[1..($commandArgs.Count - 1)] } else { @() }
}

if ($commandArgs.Count -eq 0) {
    Get-ChildItem Env: |
        Where-Object {
            $_.Name -in @(
                "USERPROFILE",
                "HOME",
                "APPDATA",
                "LOCALAPPDATA",
                "PROGRAMDATA",
                "SystemRoot",
                "windir",
                "TEMP",
                "TMP"
            )
        } |
        Sort-Object Name
    exit 0
}

$command = $commandArgs[0]
$arguments = if ($commandArgs.Count -gt 1) { $commandArgs[1..($commandArgs.Count - 1)] } else { @() }

switch ($command.ToLowerInvariant()) {
    "node" {
        if ($arguments.Count -eq 1 -and $arguments[0] -eq "v") {
            $arguments = @("-v")
        }
    }
    "pnpm" {
        if ($arguments.Count -eq 1 -and $arguments[0] -eq "v") {
            $arguments = @("-v")
        }
    }
}

& $command @arguments
exit $LASTEXITCODE
