# ICube APK 一键构建脚本
# 用法: ./scripts/build-apk.ps1
# 前置: 需安装 Node.js、Android SDK、JDK 21（路径已写入 android/gradle.properties）
# 可选: 设置 $env:SCP_USER 和 $env:SCP_HOST 自动上传，否则交互式询问

$ErrorActionPreference = "Stop"

$AppDir = "$PSScriptRoot\..\cube_app"
$ApkPath = "$AppDir\android\app\build\outputs\apk\debug\app-debug.apk"

# 从 package.json 提取版本号
$packageJson = Get-Content "$AppDir\package.json" -Raw | ConvertFrom-Json
$version = $packageJson.version
$versionedApkName = "icube-v$version.apk"
$versionedApkPath = "$AppDir\android\app\build\outputs\apk\debug\$versionedApkName"

Write-Host "============================================"
Write-Host "  ICube APK 一键构建  v$version"
Write-Host "============================================"
Write-Host ""

# 第一步：构建前端资源（Vue + Vite 产物 → dist/）
Write-Host "[1/4] 构建前端资源..."
Set-Location $AppDir
npm run build
Write-Host ""

# 第二步：同步 Capacitor（将 dist/ 复制到 android/app/src/main/assets/public/）
Write-Host "[2/4] 同步 Capacitor..."
npx cap sync android
Write-Host ""

# 第三步：构建 APK（Gradle assembleDebug，JDK 路径由 gradle.properties 指定）
Write-Host "[3/4] 构建 APK..."
Set-Location "$AppDir\android"
.\gradlew.bat assembleDebug --no-daemon
Write-Host ""

# 第四步：重命名并上传到服务器（scp 到 downloads 目录，Nginx 提供下载）
if (Test-Path $ApkPath) {
    # 复制为带版本号的文件名
    Copy-Item -Path $ApkPath -Destination $versionedApkPath -Force
    $size = [math]::Round((Get-Item $versionedApkPath).Length / 1MB, 2)
    Write-Host "[4/4] 上传 APK 到服务器..."

    # 同时复制到本地 downloads 目录
    $localDownloads = "$PSScriptRoot\..\downloads"
    if (-not (Test-Path $localDownloads)) { New-Item -ItemType Directory -Path $localDownloads | Out-Null }
    Copy-Item -Path $versionedApkPath -Destination "$localDownloads\$versionedApkName" -Force

    $scpUser = $env:SCP_USER
    $scpHost = $env:SCP_HOST
    if (-not $scpUser) { $scpUser = Read-Host "服务器用户名 (默认 bh, 直接回车跳过上传)" }
    if ($scpUser -and $scpUser -ne "") {
        if (-not $scpHost) { $scpHost = if ($scpUser -eq "bh") { "8.136.100.251" } else { Read-Host "服务器IP" } }
        $remotePath = "$scpUser@$scpHost`:/home/bh/ICube/downloads/$versionedApkName"
        scp $versionedApkPath $remotePath
        Write-Host ""
        Write-Host "============================================"
        Write-Host "  构建并上传成功！  v$version"
        Write-Host "  本地路径: $versionedApkPath"
        Write-Host "  大小: ${size}MB"
        Write-Host "  下载地址: http://$scpHost/apk/$versionedApkName"
        Write-Host "============================================"
    } else {
        Write-Host ""
        Write-Host "============================================"
        Write-Host "  构建成功！（跳过上传）  v$version"
        Write-Host "  路径: $versionedApkPath"
        Write-Host "  大小: ${size}MB"
        Write-Host "============================================"
    }
} else {
    Write-Host "[错误] APK 文件未找到: $ApkPath"
    exit 1
}
