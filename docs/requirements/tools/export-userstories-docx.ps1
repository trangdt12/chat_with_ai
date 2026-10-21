# Export docs/requirements/UserStories.md to UserStories.docx with screenshots EMBEDDED in the file.
# Usage (Windows PowerShell, from repo root or anywhere):
#   powershell -ExecutionPolicy Bypass -File docs\requirements\tools\export-userstories-docx.ps1
# Requires: Microsoft Word (COM). Re-run after render-screenshots.ps1 whenever screens change.
# Note: this script is ASCII-only on purpose (PowerShell 5.1 reads BOM-less .ps1 as ANSI);
#       all Vietnamese text comes from the UTF-8 markdown file.

param(
  [string]$Markdown = (Join-Path $PSScriptRoot "..\UserStories.md"),
  [string]$Output   = (Join-Path $PSScriptRoot "..\UserStories.docx")
)

$Markdown = (Resolve-Path $Markdown).Path
$docDir   = Split-Path $Markdown
$Output   = [IO.Path]::GetFullPath($Output)
$tmpHtml  = Join-Path $docDir "_userstories_export.tmp.html"

function Convert-Inline([string]$s) {
  $s = $s -replace '&', '&amp;' -replace '<(?!a id=|/a>)', '&lt;'
  $s = [regex]::Replace($s, '`([^`]+)`', '<code>$1</code>')
  # images: ![alt](path) -> fixed width ~16 cm so they fit an A4 page
  $s = [regex]::Replace($s, '!\[([^\]]*)\]\(([^)]+)\)', '<img src="$2" alt="$1" width="600">')
  $s = [regex]::Replace($s, '\[([^\]]+)\]\(([^)]+)\)', '<a href="$2">$1</a>')
  $s = [regex]::Replace($s, '\*\*(.+?)\*\*', '<b>$1</b>')
  $s = [regex]::Replace($s, '(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])', '<i>$1</i>')
  return $s
}

$lines = [IO.File]::ReadAllLines($Markdown, [Text.Encoding]::UTF8)
$sb = New-Object Text.StringBuilder
[void]$sb.Append(@'
<!doctype html><html><head><meta charset="utf-8"><title>User Stories</title>
<style>
 body { font-family: "Segoe UI", Arial, sans-serif; font-size: 10.5pt; color: #111827; }
 h1 { font-size: 20pt; color: #1e40af; } h2 { font-size: 15pt; color: #1e40af; margin-top: 18pt; }
 h3 { font-size: 12.5pt; color: #111827; margin-top: 14pt; }
 table { border-collapse: collapse; width: 100%; margin: 6pt 0; }
 th, td { border: 1px solid #d1d5db; padding: 3pt 5pt; vertical-align: top; font-size: 9.5pt; }
 th { background: #f3f4f6; text-align: left; }
 blockquote { border-left: 3pt solid #1d4ed8; background: #eff4ff; margin: 6pt 0; padding: 4pt 8pt; }
 code { font-family: Consolas, monospace; font-size: 9pt; color: #374151; }
 img { border: 1px solid #d1d5db; }
 p.caption { color: #4b5563; margin: 8pt 0 2pt; }
</style></head><body>
'@)

$inTable = $false; $headerDone = $false; $inList = $false; $inQuote = $false
function Close-Blocks {
  if ($script:inTable) { [void]$script:sb.Append("</table>`n"); $script:inTable = $false }
  if ($script:inList)  { [void]$script:sb.Append("</ul>`n");    $script:inList  = $false }
  if ($script:inQuote) { [void]$script:sb.Append("</blockquote>`n"); $script:inQuote = $false }
}

foreach ($line in $lines) {
  $t = $line.TrimEnd()
  if ($t -eq '') { Close-Blocks; continue }

  if ($t -match '^\|') {
    if (-not $inTable) { Close-Blocks; [void]$sb.Append("<table>`n"); $inTable = $true; $headerDone = $false }
    if ($t -match '^\|[\s:\-|]+\|$') { $headerDone = $true; continue }   # separator row
    $cells = $t.Trim('|').Split('|') | ForEach-Object { Convert-Inline $_.Trim() }
    $tag = if (-not $headerDone) { 'th' } else { 'td' }
    [void]$sb.Append("<tr>" + (($cells | ForEach-Object { "<$tag>$_</$tag>" }) -join '') + "</tr>`n")
    continue
  }
  if ($inTable) { [void]$sb.Append("</table>`n"); $inTable = $false }

  if ($t -match '^(#{1,6})\s+(.*)$') {
    Close-Blocks; $n = $Matches[1].Length
    [void]$sb.Append("<h$n>" + (Convert-Inline $Matches[2]) + "</h$n>`n"); continue
  }
  if ($t -eq '---') { Close-Blocks; [void]$sb.Append("<hr>`n"); continue }
  if ($t -match '^>\s?(.*)$') {
    if (-not $inQuote) { Close-Blocks; [void]$sb.Append("<blockquote>"); $inQuote = $true }
    [void]$sb.Append("<p>" + (Convert-Inline $Matches[1]) + "</p>"); continue
  }
  if ($t -match '^- (.*)$') {
    if (-not $inList) { Close-Blocks; [void]$sb.Append("<ul>`n"); $inList = $true }
    [void]$sb.Append("<li>" + (Convert-Inline $Matches[1]) + "</li>`n"); continue
  }
  if ($t -match '^<a id="') { Close-Blocks; [void]$sb.Append($t + "`n"); continue }

  Close-Blocks
  $cls = if ($t -match '^\*[^*].*\*$') { ' class="caption"' } else { '' }
  [void]$sb.Append("<p$cls>" + (Convert-Inline $t) + "</p>`n")
}
Close-Blocks
[void]$sb.Append("</body></html>")
[IO.File]::WriteAllText($tmpHtml, $sb.ToString(), (New-Object Text.UTF8Encoding($true)))

# --- Word: open HTML, embed every picture, save as .docx ---
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
try {
  $doc = $word.Documents.Open($tmpHtml, $false, $false, $false, "", "", $false, "", "", 0, 65001)
  $doc.PageSetup.PaperSize = 7            # wdPaperA4
  $doc.PageSetup.TopMargin = 56; $doc.PageSetup.BottomMargin = 56
  $doc.PageSetup.LeftMargin = 56; $doc.PageSetup.RightMargin = 56
  $embedded = 0
  foreach ($shape in @($doc.InlineShapes)) {
    if ($shape.LinkFormat -ne $null) {
      $shape.LinkFormat.SavePictureWithDocument = $true
      $shape.LinkFormat.BreakLink()
      $embedded++
    }
  }
  # Linked pictures can also come in as INCLUDEPICTURE fields; unlink them so the image data stays in the file
  foreach ($f in @($doc.Fields)) { if ($f.Type -eq 67) { $f.Unlink(); $embedded++ } }   # wdFieldIncludePicture
  $doc.SaveAs2($Output, 16)               # wdFormatXMLDocument (.docx)
  $pictures = $doc.InlineShapes.Count
  $doc.Close($false)
  Write-Host ("Saved {0} | inline pictures: {1} | links broken: {2}" -f $Output, $pictures, $embedded)
} finally {
  $word.Quit()
  [void][Runtime.InteropServices.Marshal]::ReleaseComObject($word)
  Remove-Item $tmpHtml -ErrorAction SilentlyContinue
}
