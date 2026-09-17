<#
.SYNOPSIS
    Shows which Git identity and GitHub account a repository will use.
.DESCRIPTION
    Reports the effective user.name / user.email, where each value comes from
    (local vs global config), the origin URL, and the account name embedded in
    that URL. Matches the result against the registry in ~/.git-accounts.json.
    With -Strict, exits 1 when the repo is not pinned to a single account.
.EXAMPLE
    .\Get-GitAccount.ps1
    .\Get-GitAccount.ps1 -Strict
#>
[CmdletBinding()]
param(
    [string]$RepoPath = (Get-Location).Path,
    [switch]$Strict
)

$ErrorActionPreference = 'Stop'
$registryPath = Join-Path $env:USERPROFILE '.git-accounts.json'

function Get-ConfigWithScope([string]$key) {
    $local = git -C $RepoPath config --local --get $key 2>$null
    if ($LASTEXITCODE -eq 0 -and $local) { return @{ Value = $local; Scope = 'local' } }
    $global = git config --global --get $key 2>$null
    if ($LASTEXITCODE -eq 0 -and $global) { return @{ Value = $global; Scope = 'global' } }
    return @{ Value = ''; Scope = 'unset' }
}

git -C $RepoPath rev-parse --is-inside-work-tree 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) { Write-Error "Not a git repository: $RepoPath" }

$name  = Get-ConfigWithScope 'user.name'
$email = Get-ConfigWithScope 'user.email'
$origin = git -C $RepoPath remote get-url origin 2>$null
if ($LASTEXITCODE -ne 0) { $origin = '' }

$urlUser = ''
$urlHost = ''
if ($origin -match '^https?://(?:([^@/]+)@)?([^/]+)/') {
    $urlUser = $Matches[1]
    $urlHost = $Matches[2]
} elseif ($origin -match '^(?:[^@]+@)?([^:]+):') {
    $urlHost = $Matches[1]
}

$alias = ''
if (Test-Path $registryPath) {
    $registry = Get-Content $registryPath -Raw | ConvertFrom-Json
    foreach ($prop in $registry.PSObject.Properties) {
        $acct = $prop.Value
        if ($acct.host -eq $urlHost -and $acct.username -eq $urlUser -and $acct.email -eq $email.Value) {
            $alias = $prop.Name
        }
    }
}

$problems = @()
if ($name.Scope  -ne 'local') { $problems += "user.name is $($name.Scope); pin it locally" }
if ($email.Scope -ne 'local') { $problems += "user.email is $($email.Scope); pin it locally" }
if ($origin -and -not $urlUser) { $problems += "origin URL has no account name, so Credential Manager will use the shared '$urlHost' token" }
if ($origin -and -not $alias)   { $problems += "identity and origin do not match any registry entry in $registryPath" }

[PSCustomObject]@{
    Repo        = $RepoPath
    Alias       = if ($alias) { $alias } else { '(none)' }
    UserName    = "$($name.Value) [$($name.Scope)]"
    UserEmail   = "$($email.Value) [$($email.Scope)]"
    Origin      = $origin
    UrlAccount  = if ($urlUser) { $urlUser } else { '(none)' }
    Problems    = if ($problems) { $problems -join '; ' } else { 'none' }
} | Format-List

if ($Strict -and $problems) {
    Write-Host "Account check FAILED. Run Set-GitAccount.ps1 -Account <alias> to fix." -ForegroundColor Red
    exit 1
}
exit 0
