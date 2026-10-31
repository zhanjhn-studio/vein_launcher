# Build the frontend: bundle src/main.tsx -> dist/app.js and copy static assets.
# Usage: powershell -ExecutionPolicy Bypass -File build.ps1
param(
  [string]$Esbuild = ""
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

function Resolve-Esbuild {
  if ($Esbuild) { return $Esbuild }
  if ($env:ESBUILD) { return $env:ESBUILD }
  $cmd = Get-Command esbuild -ErrorAction SilentlyContinue
  if ($cmd) { return $cmd.Source }
  $local = "C:\Users\zzzzz\d1-rest\node_modules\.bin\esbuild.cmd"
  if (Test-Path $local) { return $local }
  throw "esbuild not found: install it, set `$env:ESBUILD, or pass -Esbuild <path>."
}

$esbuild = Resolve-Esbuild
New-Item -ItemType Directory -Force dist | Out-Null
New-Item -ItemType Directory -Force dist\icons | Out-Null
New-Item -ItemType Directory -Force dist\vendor | Out-Null

& $esbuild src/main.tsx --bundle --outfile=dist/app.js --jsx=automatic --minify
if ($LASTEXITCODE -ne 0) { throw "esbuild failed (exit $LASTEXITCODE)" }

Copy-Item index.html         dist\index.html -Force
Copy-Item src\styles.css     dist\styles.css -Force
Copy-Item src\logo.png       dist\logo.png   -Force
Copy-Item assets\icons\*.png dist\icons\     -Force
Copy-Item assets\vendor\*    dist\vendor\    -Recurse -Force

Write-Host "Frontend build done: dist\app.js + static assets"
