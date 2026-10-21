# Chụp lại ảnh màn hình (chế độ ?clean) cho docs/requirements/UserStories.md
# Cách dùng (PowerShell, từ thư mục này):  .\render-screenshots.ps1
# Yêu cầu: Google Chrome hoặc Microsoft Edge đã cài đặt.
# Không dùng ErrorActionPreference=Stop: Chrome ghi "bytes written" ra stderr, Windows PowerShell 5.1
# coi đó là lỗi và dừng script. Kết quả được kiểm tra bằng Test-Path cho từng ảnh.
$browser = @(
  "$env:ProgramFiles\Google\Chrome\Application\chrome.exe",
  "${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe",
  "$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe"
) | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $browser) { throw "Không tìm thấy Chrome hoặc Edge." }

$dir = $PSScriptRoot
$out = Join-Path $dir "screenshots"
New-Item -ItemType Directory -Force $out | Out-Null

# trang#trạng-thái — giữ đồng bộ với các ảnh được dùng trong UserStories.md
$targets = @(
  "01-dang-nhap#default", "01-dang-nhap#expired",
  "02-trang-thai-trong#empty", "02-trang-thai-trong#processing",
  "03-xac-nhan-phan-loai",
  "04-tai-tai-lieu-len#member", "04-tai-tai-lieu-len#manager",
  "05-hoi-dap#streaming", "05-hoi-dap#completed", "05-hoi-dap#feedback", "05-hoi-dap#copied",
  "06-trich-dan#normal", "06-trich-dan#removed",
  "07-trang-thai-cau-tra-loi#notfound", "07-trang-thai-cau-tra-loi#clarify", "07-trang-thai-cau-tra-loi#stopped",
  "07-trang-thai-cau-tra-loi#incomplete", "07-trang-thai-cau-tra-loi#ratelimit",
  "08-quan-tri-nhom-truy-cap#list", "08-quan-tri-nhom-truy-cap#add", "08-quan-tri-nhom-truy-cap#notfound",
  "09-quan-tri-go-tai-lieu#list", "09-quan-tri-go-tai-lieu#dialog", "09-quan-tri-go-tai-lieu#done", "09-quan-tri-go-tai-lieu#pending",
  "10-quan-tri-nhat-ky#results", "10-quan-tri-nhat-ky#range",
  "11-khong-co-quyen#nogroup", "11-khong-co-quyen#revoked"
)
$base = "file:///" + ($dir -replace '\\', '/')
foreach ($t in $targets) {
  $page, $state = $t.Split('#')
  $url = "$base/$page.html?clean" + $(if ($state) { "#$state" } else { "" })
  $name = if ($state) { "${page}__$state" } else { $page }
  $png = Join-Path $out "$name.png"
  if (Test-Path $png) { Remove-Item $png }
  & $browser --headless=new --disable-gpu --hide-scrollbars --window-size=1440,900 --screenshot="$png" $url 2>$null | Out-Null
  if (Test-Path $png) { Write-Host "ok   $name" } else { Write-Warning "lỗi $name" }
}
