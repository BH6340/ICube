<#
.SYNOPSIS
本地后台启动或关闭 ICube 前后端开发服务器。

.PARAMETER Action
可选值为 start 或 stop，省略时默认执行 start。

.EXAMPLE
.\scripts\dev-local.ps1 start

.EXAMPLE
.\scripts\dev-local.ps1 restart

.EXAMPLE
.\scripts\dev-local.ps1 stop
#>
[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [ValidateSet('start', 'stop', 'restart')]
    [string]$Action = 'start'
)

# 严格检查未定义变量，并让运行错误立即终止脚本。
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# 脚本位于 scripts/ 子目录，向上取一层得到项目根目录。
$root = Split-Path $PSScriptRoot -Parent
$runtimeDir = Join-Path $root '.dev-local'
$pythonPath = 'E:\software\python\python313\env\cube_api\Scripts\python.exe'
$npmCommand = Get-Command npm.cmd -ErrorAction SilentlyContinue

# 每项服务包含启动命令、监听端口、PID 状态文件和日志路径。
$services = @(
    [PSCustomObject]@{
        Name = 'backend'
        Port = 8000
        FilePath = $pythonPath
        Arguments = @(
            'manage.py',
            'runserver',
            '127.0.0.1:8000',
            '--settings=cube_api.settings.dev',
            '--noreload'
        )
        WorkingDirectory = Join-Path $root 'cube_api'
        PidFile = Join-Path $runtimeDir 'backend.json'
        OutputLog = Join-Path $runtimeDir 'backend.out.log'
        ErrorLog = Join-Path $runtimeDir 'backend.err.log'
    },
    [PSCustomObject]@{
        Name = 'frontend'
        Port = 5173
        FilePath = $(if ($npmCommand) { $npmCommand.Source } else { $null })
        Arguments = @('run', 'dev')
        WorkingDirectory = Join-Path $root 'cube_front'
        PidFile = Join-Path $runtimeDir 'frontend.json'
        OutputLog = Join-Path $runtimeDir 'frontend.out.log'
        ErrorLog = Join-Path $runtimeDir 'frontend.err.log'
    }
)

# 读取 PID 状态，并通过进程启动时间防止误操作已复用的 PID。
function Get-ManagedProcess {
    param([PSCustomObject]$Service)

    if (-not (Test-Path $Service.PidFile)) {
        return $null
    }

    try {
        $state = Get-Content -Raw $Service.PidFile | ConvertFrom-Json
        $process = Get-Process -Id ([int]$state.Pid) -ErrorAction Stop
        $startTime = [string]$process.StartTime.ToUniversalTime().Ticks
        if ($startTime -ne [string]$state.StartTime) {
            Remove-Item $Service.PidFile -Force
            return $null
        }
        return $process
    } catch {
        Remove-Item $Service.PidFile -Force -ErrorAction SilentlyContinue
        return $null
    }
}

# 保存 PID 和进程启动时间，供后续 stop 精确定位进程。
function Save-ManagedProcess {
    param(
        [PSCustomObject]$Service,
        [System.Diagnostics.Process]$Process
    )

    @{
        Pid = $Process.Id
        StartTime = [string]$Process.StartTime.ToUniversalTime().Ticks
    } | ConvertTo-Json | Set-Content -Encoding ASCII $Service.PidFile
}

# 判断指定端口当前是否处于监听状态。
function Test-PortListening {
    param([int]$Port)

    return [bool](
        Get-NetTCPConnection -State Listen -LocalPort $Port `
            -ErrorAction SilentlyContinue
    )
}

# 最多等待 60 秒；服务提前退出时直接指向对应错误日志。
function Wait-ServiceReady {
    param([PSCustomObject]$Service)

    for ($i = 0; $i -lt 120; $i++) {
        if (Test-PortListening $Service.Port) {
            return
        }
        if (-not (Get-ManagedProcess $Service)) {
            throw "$($Service.Name) exited. See $($Service.ErrorLog)"
        }
        Start-Sleep -Milliseconds 500
    }

    throw "$($Service.Name) did not listen on port $($Service.Port)"
}

# taskkill 的 /T 会同时关闭 npm、Vite 等子进程，避免残留后台进程。
function Stop-ServiceProcess {
    param(
        [PSCustomObject]$Service,
        [switch]$Quiet
    )

    $process = Get-ManagedProcess $Service
    if (-not $process) {
        if (-not $Quiet) {
            Write-Output "$($Service.Name) is not running"
        }
        return
    }

    & "$env:SystemRoot\System32\taskkill.exe" `
        /PID $process.Id /T /F 2>$null | Out-Null
    Remove-Item $Service.PidFile -Force -ErrorAction SilentlyContinue

    if (-not $Quiet) {
        Write-Output "$($Service.Name) stopped"
    }
}

# 校验本地依赖后依次启动后端和前端；任一失败则回滚本次已启动服务。
function Start-All {
    if (-not (Test-Path $pythonPath)) {
        throw "Python not found: $pythonPath"
    }
    if (-not $npmCommand) {
        throw 'npm.cmd was not found in PATH'
    }

    New-Item -ItemType Directory -Force $runtimeDir | Out-Null
    $started = @()

    try {
        foreach ($service in $services) {
            # 已由本脚本启动的服务保持运行，不重复创建进程。
            $existing = Get-ManagedProcess $service
            if ($existing) {
                Wait-ServiceReady $service
                Write-Output "$($service.Name) already running (PID $($existing.Id))"
                continue
            }
            if (Test-PortListening $service.Port) {
                throw "Port $($service.Port) is already in use"
            }

            # 标准输出和错误输出分开保存，便于定位启动异常。
            $process = Start-Process `
                -FilePath $service.FilePath `
                -ArgumentList $service.Arguments `
                -WorkingDirectory $service.WorkingDirectory `
                -RedirectStandardOutput $service.OutputLog `
                -RedirectStandardError $service.ErrorLog `
                -WindowStyle Hidden `
                -PassThru

            Save-ManagedProcess -Service $service -Process $process
            $started += $service
            Wait-ServiceReady $service
            Write-Output "$($service.Name) started (PID $($process.Id))"
        }
    } catch {
        foreach ($service in $started) {
            Stop-ServiceProcess -Service $service -Quiet
        }
        throw
    }

    Write-Output 'Frontend: http://localhost:5173'
    Write-Output 'Backend:  http://127.0.0.1:8000'
}

# 逆序关闭服务，先停止前端，再停止后端。
function Stop-All {
    for ($i = $services.Count - 1; $i -ge 0; $i--) {
        Stop-ServiceProcess $services[$i]
    }
}

# 根据命令行参数分派启动、关闭或重启操作。
if ($Action -eq 'start') {
    Start-All
} elseif ($Action -eq 'restart') {
    Stop-All
    Start-All
} else {
    Stop-All
}
