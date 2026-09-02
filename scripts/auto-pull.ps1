<#
.SYNOPSIS
自动拉取远程仓库 main 和 dev 分支最新代码，处理本地冲突并记录日志。

.DESCRIPTION
每天由 Windows 计划任务调用。
- main 分支：git pull --rebase，保持本地 main 与远程同步（参考、对比用）
- dev 分支：git fetch + reset --hard，确保开发分支与远程完全一致
  （sync-dev 会 force push dev，必须用 reset 而非 rebase，否则会冲突）
若工作区有未提交改动则跳过拉取并记录日志，不破坏工作区。

.EXAMPLE
.\scripts\auto-pull.ps1
#>
[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$logDir = Join-Path $root '.dev-local'
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Force $logDir | Out-Null }
$logFile = Join-Path $logDir 'auto-pull.log'

function Write-Log {
    param([string]$Message)
    $ts = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    $line = "[$ts] $Message"
    Add-Content -Path $logFile -Value $line -Encoding UTF8
    Write-Output $line
}

try {
    Set-Location $root

    # 检查工作区是否干净（忽略未跟踪文件）
    $dirty = git status --porcelain 2>&1 | Where-Object { $_ -match '^\s?[MADRC]' }
    if ($dirty) {
        Write-Log "WARN: 工作区有未提交的改动，跳过拉取"
        Write-Log ($dirty -join "`n")
        exit 0
    }

    # 记录当前分支，拉取后切回
    $currentBranch = (git rev-parse --abbrev-ref HEAD 2>&1) -join ""

    # ---- 拉取 main 分支 ----
    $output = git fetch origin main 2>&1
    Write-Log "git fetch origin main"
    Write-Log ($output -join "`n")

    $output = git pull --rebase origin main 2>&1
    Write-Log "git pull --rebase origin main"
    Write-Log ($output -join "`n")

    if ($output -match 'Already up to date|Already up.*date') {
        Write-Log "main: 已是最新"
    } else {
        Write-Log "main: 拉取成功"
    }

    # ---- 同步 dev 分支 ----
    # sync-dev 会 force push dev，必须用 reset --hard 而非 rebase
    $output = git fetch origin dev 2>&1
    Write-Log "git fetch origin dev"
    Write-Log ($output -join "`n")

    # 先存当前分支状态，切到 dev 同步
    $output = git checkout dev 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Log "WARN: 切换到 dev 失败: $($output -join '`n')"
    } else {
        $output = git reset --hard origin/dev 2>&1
        Write-Log "git reset --hard origin/dev"
        Write-Log ($output -join "`n")
        Write-Log "dev: 已同步到远程"
    }

    # ---- 切回原分支 ----
    $output = git checkout $currentBranch 2>&1
    Write-Log "切回分支: $currentBranch"

} catch {
    Write-Log "ERROR: $_"
    # 确保切回原分支
    try { git checkout $currentBranch 2>&1 | Out-Null } catch {}
    exit 1
}
