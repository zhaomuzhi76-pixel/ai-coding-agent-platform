# WSL 端口转发脚本（需在 Windows PowerShell 管理员运行一次）
# 把 WSL 的 9022 端口映射到 Windows 本地 9022
$wslIp = (wsl hostname -I).Trim().Split()[0]
Write-Host "WSL IP: $wslIp"

# 清理旧规则
netsh interface portproxy delete v4tov4 listenport=9022 listenaddress=0.0.0.0 2>$null

# 添加新规则
netsh interface portproxy add v4tov4 `
  listenport=9022 listenaddress=0.0.0.0 `
  connectport=9022 connectaddress=$wslIp

# 防火墙放行
New-NetFirewallRule -DisplayName "WSL Backend 9022" `
  -Direction Inbound -LocalPort 9022 -Protocol TCP -Action Allow `
  -ErrorAction SilentlyContinue

Write-Host "✅ 完成，Windows 127.0.0.1:9022 → WSL $wslIp:9022"
