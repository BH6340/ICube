<#
.SYNOPSIS
自动拉取远程仓库最新代码，处理本地冲突并记录日志。

.DESCRIPTION
每天由 Windows 计划任务调用，执行 git pull --rebase。
若本地有未提交的自动备份提交会自动 rebase 到远程之上；
若存在冲突则记录日志并退出，不破坏工作区。

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

    # 拉取远程更新（rebase 模式，保持线性历史）
    $output = git pull --rebase origin main 2>&1
    Write-Log "git pull --rebase origin main"
    Write-Log ($output -join "`n")

    # 检查是否有实际更新
    if ($output -match 'Already up to date|Already up.*date') {
        Write-Log "已是最新，无需更新"
    } else {
        Write-Log "拉取成功"
    }
} catch {
    Write-Log "ERROR: $_"
    exit 1
}
