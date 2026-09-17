<#
.SYNOPSIS
    Pins a repository to one GitHub/GitLab account from ~/.git-accounts.json.
.DESCRIPTION
    Sets user.name and user.email in the repo's local config and rewrites the
    origin URL to https://<username>@<host>/... so Git Credential Manager keeps
    a separate token per account. The global config is never touched.
.EXAMPLE
    .\Set-GitAccount.ps1 -Account personal
    .\Set-GitAccount.ps1 -Account work -RepoPath C:\dev\git\some-repo
#>
[CmdletBinding(SupportsShouldProcess)]
param(
    [Parameter(Mandatory)][string]$Account,
    [string]$RepoPath = (Get-Location).Path
)

$ErrorActionPreference = 'Stop'
$registryPath = Join-Path $env:USERPROFILE '.git-accounts.json'
if (-not (Test-Path $registryPath)) {
    Write-Error "No registry at $registryPath. Run Register-GitAccount.ps1 first."
}
$registry = Get-Content $registryPath -Raw | ConvertFrom-Json
$acct = $registry.$Account
if (-not $acct) {
    $known = ($registry.PSObject.Properties.Name) -join ', '
    Write-Error "Unknown account '$Account'. Known: $known"
}
if (-not $acct.email) {
    Write-Error "Account '$Account' has no email in the registry. Fix it with Register-GitAccount.ps1."
}

git -C $RepoPath rev-parse --is-inside-work-tree 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) { Write-Error "Not a git repository: $RepoPath" }

if ($PSCmdlet.ShouldProcess($RepoPath, "set user.name='$($acct.name)' user.email='$($acct.email)'")) {
    git -C $RepoPath config --local user.name  $acct.name
    git -C $RepoPath config --local user.email $acct.email
    git -C $RepoPath config --local credential.username $acct.username
}

$origin = git -C $RepoPath remote get-url origin 2>$null
if ($LASTEXITCODE -eq 0 -and $origin -match '^(https?)://(?:[^@/]+@)?([^/]+)/(.+)$') {
    $scheme, $urlHost, $path = $Matches[1], $Matches[2], $Matches[3]
    if ($urlHost -ne $acct.host) {
        Write-Warning "origin host '$urlHost' does not match account host '$($acct.host)'. URL left unchanged."
    } else {
        $newUrl = "${scheme}://$($acct.username)@${urlHost}/${path}"
        if ($newUrl -ne $origin -and $PSCmdlet.ShouldProcess('origin', "set-url $newUrl")) {
            git -C $RepoPath remote set-url origin $newUrl
        }
    }
} elseif ($origin) {
    Write-Warning "origin '$origin' is not an https URL. Only identity was set; SSH remotes need a per-account Host in ~/.ssh/config."
} else {
    Write-Warning "No origin remote yet. Add it as https://$($acct.username)@$($acct.host)/<owner>/<repo>.git"
}

& (Join-Path $PSScriptRoot 'Get-GitAccount.ps1') -RepoPath $RepoPath
