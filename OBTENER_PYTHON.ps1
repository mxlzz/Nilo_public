# Bootstrap unicamente local de CPython embebible, sin modificacion de PATH/registro.
# Fuente oficial y SHA256 de distribucion fijada.
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$runtime = Join-Path $root 'python'
$exe = Join-Path $runtime 'python.exe'
$pythonVersion = '3.12.10'
$filename = 'python-3.12.10-embed-amd64.zip'
$downloadUrl = 'https://www.python.org/ftp/python/3.12.10/python-3.12.10-embed-amd64.zip'
$expectedSha256 = '4ACBED6DD1C744B0376E3B1CF57CE906F9DC9E95E68824584C8099A63025A3C3'
$archiveInFolder = Join-Path $root $filename
$downloadTemp = Join-Path $root '.python_portable_download.tmp'
$staging = Join-Path $root '.python_portable_staging'
try {
    if (Test-Path -LiteralPath $exe) { Write-Host 'Python portable ya estaba disponible.'; exit 0 }
    if (-not [Environment]::Is64BitOperatingSystem) { throw 'Este paquete requiere Windows de 64 bits.' }
    if (Test-Path -LiteralPath $runtime) { throw 'La carpeta python existe pero esta incompleta. Renombrala antes de reintentar.' }
    if (Test-Path -LiteralPath $staging) { throw 'Existe una extraccion incompleta (.python_portable_staging). Eliminá SOLO esa carpeta antes de reintentar.' }

    if (Test-Path -LiteralPath $archiveInFolder) {
        Write-Host 'Usando el archivo oficial que copiaste junto a Nilo.'
        $archive = $archiveInFolder
    } else {
        $archive = $downloadTemp
        if (Test-Path -LiteralPath $downloadTemp) { Remove-Item -LiteralPath $downloadTemp -Force }
        Write-Host 'Descargando el motor oficial de Python 3.12.10 desde python.org (unos 11 MB)...'
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        $client = New-Object Net.WebClient
        try { $client.DownloadFile($downloadUrl, $downloadTemp) }
        finally { $client.Dispose() }
    }
    $sha = (Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash.ToUpperInvariant()
    if ($sha -ne $expectedSha256) {
        throw "El ZIP de Python no coincide con la suma SHA256 esperada. No se ejecutara. Verifica que descargaste $filename desde python.org."
    }
    Write-Host 'SHA256 del interprete verificado.'
    New-Item -Path $staging -ItemType Directory | Out-Null
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    [IO.Compression.ZipFile]::ExtractToDirectory($archive, $staging)
    $pth = Join-Path $staging 'python312._pth'
    if (-not (Test-Path -LiteralPath $pth)) { throw 'La distribucion descargada no tiene python312._pth.' }
    if (-not (Test-Path -LiteralPath (Join-Path $staging 'python312.zip'))) { throw 'La distribucion esta incompleta.' }
    # Solo permite importar biblioteca estandar, runtime local y codigo Nilo (..).
    [IO.File]::WriteAllText($pth, "python312.zip`r`n.`r`n..`r`n", [Text.Encoding]::ASCII)
    Move-Item -LiteralPath $staging -Destination $runtime
    Write-Host 'Python portable preparado dentro de Nilo. Windows no fue modificado.'
    if ($archive -eq $downloadTemp -and (Test-Path -LiteralPath $downloadTemp)) {
        Remove-Item -LiteralPath $downloadTemp -Force
    }
    exit 0
} catch {
    Write-Host ''
    Write-Host ('ERROR: ' + $_.Exception.Message) -ForegroundColor Red
    Write-Host ('Si la notebook bloquea la descarga, baja manualmente ' + $filename)
    Write-Host 'en otra computadora, copialo a esta carpeta y vuelve a iniciar Nilo.'
    exit 1
}
