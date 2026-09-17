<#
.SYNOPSIS
    Adds or updates an account alias in ~/.git-accounts.json.
.EXAMPLE
    .\Register-GitAccount.ps1 -Alias personal -Username wesnealpi -Name 'Wes Watson' -Email '33036257+wesnealpi@users.noreply.github.com'
    .\Register-GitAccount.ps1 -Alias work -Username acme-wes -Name 'Wes Watson' -Email 'wes@acme.com' -HostName github.com
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$Alias,
    [Parameter(Mandatory)][string]$Username,
    [Parameter(Mandatory)][string]$Name,
    [Parameter(Mandatory)][string]$Email,
    [string]$HostName = 'github.com'
)

$ErrorActionPreference = 'Stop'
$registryPath = Join-Path $env:USERPROFILE '.git-accounts.json'
$registry = if (Test-Path $registryPath) { Get-Content $registryPath -Raw | ConvertFrom-Json } else { [PSCustomObject]@{} }

$entry = [PSCustomObject]@{ host = $HostName; username = $Username; name = $Name; email = $Email }
if ($registry.PSObject.Properties[$Alias]) { $registry.$Alias = $entry }
else { $registry | Add-Member -NotePropertyName $Alias -NotePropertyValue $entry }

$registry | ConvertTo-Json -Depth 3 | Set-Content -Path $registryPath -Encoding utf8
Write-Host "Registered '$Alias' -> $Username@$HostName <$Email> in $registryPath"
