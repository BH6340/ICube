<#
.SYNOPSIS
注册 ICube 自动拉取的 Windows 计划任务。
需以管理员权限运行（右键 → 以管理员身份运行 PowerShell，再执行本脚本）。
#>
$ErrorActionPreference = 'Stop'

$taskName = "ICube-AutoPull"
$scriptPath = "E:\BH\PyStudy\ICube\scripts\auto-pull.ps1"
$pwshPath = (Get-Command pwsh.exe -ErrorAction SilentlyContinue).Source
if (-not $pwshPath) { $pwshPath = (Get-Command powershell.exe).Source }

$existing = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($existing) {
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
    Write-Output "已删除旧任务"
}

$trigger = New-ScheduledTaskTrigger -Daily -At 8:00AM
$action = New-ScheduledTaskAction `
    -Execute $pwshPath `
    -Argument "-ExecutionPolicy Bypass -WindowStyle Hidden -File `"$scriptPath`""
$settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -DontStopIfGoingOnBatteries `
    -AllowStartIfOnBatteries
$principal = New-ScheduledTaskPrincipal `
    -UserId "$env:USERDOMAIN\$env:USERNAME" `
    -LogonType S4U `
    -RunLevel Highest

Register-ScheduledTask `
    -TaskName $taskName `
    -Trigger $trigger `
    -Action $action `
    -Settings $settings `
    -Principal $principal `
    -Description "每天 08:00 自动拉取 ICube 远程仓库更新" | Out-Null

Write-Output "计划任务 '$taskName' 已创建，每天 08:00 自动执行"
