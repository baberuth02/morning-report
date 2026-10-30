# 將 TradingView MCP 加入 Claude 桌面 App（claude_desktop_config.json）
# 會保留原有設定，並先備份舊檔

$ErrorActionPreference = 'Stop'

# 1. 找 server.js
$candidates = @(
  (Join-Path $env:USERPROFILE 'tradingview-mcp-jackson\src\server.js'),
  (Join-Path (Split-Path $PSScriptRoot -Parent) 'src\server.js')
)
$server = $candidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $server) {
  $server = Read-Host '找不到 server.js，請輸入完整路徑（例如 C:\Users\User\tradingview-mcp-jackson\src\server.js）'
  if (-not (Test-Path $server)) { throw "檔案不存在：$server" }
}
$server = (Resolve-Path $server).Path
Write-Host "使用 server.js：$server"

# 2. 確認有 Node.js
if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
  throw '找不到 Node.js，請先安裝 https://nodejs.org/'
}

# 3. 讀取或建立設定檔
$dir  = Join-Path $env:APPDATA 'Claude'
$path = Join-Path $dir 'claude_desktop_config.json'
New-Item -ItemType Directory -Force -Path $dir | Out-Null

$config = [pscustomobject]@{}
if (Test-Path $path) {
  $raw = [IO.File]::ReadAllText($path)
  if ($raw.Trim()) { $config = $raw | ConvertFrom-Json }
  $backup = "$path.bak-$(Get-Date -Format yyyyMMdd-HHmmss)"
  Copy-Item $path $backup
  Write-Host "已備份舊設定：$backup"
}

if (-not ($config.PSObject.Properties.Name -contains 'mcpServers')) {
  $config | Add-Member -NotePropertyName mcpServers -NotePropertyValue ([pscustomobject]@{})
}
$entry = [pscustomobject]@{ command = 'node'; args = @($server) }
if ($config.mcpServers.PSObject.Properties.Name -contains 'tradingview') {
  $config.mcpServers.tradingview = $entry
} else {
  $config.mcpServers | Add-Member -NotePropertyName tradingview -NotePropertyValue $entry
}

# 4. 寫回（UTF-8 不含 BOM）
$json = $config | ConvertTo-Json -Depth 20
[IO.File]::WriteAllText($path, $json, (New-Object Text.UTF8Encoding $false))

Write-Host ''
Write-Host "完成！已寫入：$path"
Write-Host $json
Write-Host ''
Write-Host '下一步：在工作列對 Claude 圖示按右鍵選 Quit，完全關閉後再重新開啟 Claude。'
