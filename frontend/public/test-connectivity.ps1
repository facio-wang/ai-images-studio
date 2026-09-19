# DevTools 平台连通性测试脚本 (PowerShell 版本)
# 在 Win11 上运行：右键 → "使用 PowerShell 运行"

$DEVTOOLS_URL = "http://192.168.31.157:8080"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  DevTools 平台连通性测试" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 测试 1: 访问首页
Write-Host "📋 测试 1: 访问平台首页" -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "${DEVTOOLS_URL}/" -Method GET -UseBasicParsing -TimeoutSec 10
    if ($response.StatusCode -eq 200) {
        Write-Host "   ✅ 首页访问成功 (HTTP $($response.StatusCode))" -ForegroundColor Green
    } else {
        Write-Host "   ❌ 首页访问失败 (HTTP $($response.StatusCode))" -ForegroundColor Red
    }
} catch {
    Write-Host "   ❌ 无法连接到服务器：$($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# 测试 2: 访问登录页
Write-Host "🔐 测试 2: 访问登录页面" -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "${DEVTOOLS_URL}/login" -Method GET -UseBasicParsing -TimeoutSec 10
    Write-Host "   ✅ 登录页访问成功 (HTTP $($response.StatusCode))" -ForegroundColor Green
} catch {
    Write-Host "   ❌ 登录页访问失败" -ForegroundColor Red
}
Write-Host ""

# 测试 3: API 健康检查
Write-Host "🏥 测试 3: API 健康检查" -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "${DEVTOOLS_URL}/api/health" -Method GET -UseBasicParsing -TimeoutSec 10
    Write-Host "   ✅ API 健康检查通过 (HTTP $($response.StatusCode))" -ForegroundColor Green
} catch {
    Write-Host "   ⚠️  API 健康检查返回错误或不可用" -ForegroundColor Yellow
}
Write-Host ""

# 测试 4: 网络延迟
Write-Host "⏱️  测试 4: 网络延迟测试" -ForegroundColor Yellow
try {
    $measure = Measure-Command { Invoke-WebRequest -Uri "${DEVTOOLS_URL}/" -Method GET -UseBasicParsing -TimeoutSec 10 }
    $latency = [math]::Round($measure.TotalMilliseconds, 2)
    Write-Host "   响应时间：${latency}ms" -ForegroundColor Cyan
    if ($latency -lt 100) {
        Write-Host "   ✅ 网络延迟优秀" -ForegroundColor Green
    } elseif ($latency -lt 500) {
        Write-Host "   ✅ 网络延迟良好" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  网络延迟较高" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   ❌ 延迟测试失败" -ForegroundColor Red
}
Write-Host ""

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  测试完成" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📝 访问信息：" -ForegroundColor White
Write-Host "   平台地址：${DEVTOOLS_URL}" -ForegroundColor Green
Write-Host "   测试账号：test@devtools.local" -ForegroundColor Green
Write-Host "   测试密码：DevTools2026!" -ForegroundColor Green
Write-Host ""
Write-Host "按任意键退出..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
