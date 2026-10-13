# Export the Apple iCloud runtime used by the Debian Wine anisette provider.
# Run on a Windows PC where the official AltServer for Windows works.
# The archive contains only Apple's DLLs/resources; no Apple ID, tokens or device state.
# Usage: powershell -ExecutionPolicy Bypass -File export-apple-runtime.ps1 [-Output apple-runtime.tar.gz]
param([string]$Output = (Join-Path (Get-Location) 'apple-runtime.tar.gz'))
$ErrorActionPreference = 'Stop'

$altServerApple = Join-Path $env:LOCALAPPDATA 'AltServer\Apple'
$coreAdi = Join-Path ${env:ProgramFiles(x86)} 'Common Files\Apple\Apple Application Support\CoreADI.dll'
$expected = @{
    'Internet Services\iCloud_main.dll' = '9e3af0c4cf50cc65554a9478aa7b381ff351373bdf034413a877f52912ff5010'
    'Apple Application Support\CoreADI.dll' = '961539f222aa018ef5b32fc0c82fca6d3e2a70100c0037741530ee5324447f9b'
}

foreach ($path in @((Join-Path $altServerApple 'Internet Services'), (Join-Path $altServerApple 'Apple Application Support'), $coreAdi)) {
    if (-not (Test-Path -LiteralPath $path)) {
        throw "Missing $path. Install AltServer for Windows and iCloud (32-bit Apple Application Support) first."
    }
}

$stage = Join-Path ([IO.Path]::GetTempPath()) ('apple-runtime-' + [guid]::NewGuid())
try {
    $apple = Join-Path $stage 'Apple'
    New-Item -ItemType Directory -Path $apple | Out-Null
    Copy-Item -LiteralPath (Join-Path $altServerApple 'Internet Services') -Destination $apple -Recurse
    Copy-Item -LiteralPath (Join-Path $altServerApple 'Apple Application Support') -Destination $apple -Recurse
    # AltServer's extracted CoreADI differs; the provider needs the installed 32-bit CoreADI.
    Copy-Item -LiteralPath $coreAdi -Destination (Join-Path $apple 'Apple Application Support\CoreADI.dll') -Force
    foreach ($entry in $expected.GetEnumerator()) {
        $hash = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $apple $entry.Key)).Hash.ToLowerInvariant()
        if ($hash -ne $entry.Value) {
            throw "Unsupported $($entry.Key) (SHA-256 $hash). This provider is verified with iCloud_main 261.7.0.49 and CoreADI 4.17.0 only."
        }
    }
    & "$env:SystemRoot\System32\tar.exe" -czf $Output -C $stage Apple
    if ($LASTEXITCODE -ne 0) { throw 'tar.exe failed' }
    Write-Output "Created $Output"
    Write-Output 'Copy it to the Debian host, then run: sudo sh install.sh --import-apple-runtime <path>'
} finally {
    Remove-Item -LiteralPath $stage -Recurse -Force -ErrorAction SilentlyContinue
}
