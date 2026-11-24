$ErrorActionPreference = 'Stop'
$workspace = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$manifestPath = Join-Path $PSScriptRoot 'render-cleanup-manifest-2026-11-21.json'
$manifest = Get-Content -LiteralPath $manifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
if ($manifest.root -ne $workspace) { throw 'Manifest workspace mismatch' }
$allowedRoot = (Resolve-Path -LiteralPath (Join-Path $workspace 'scen\3d\kontrakt\ut')).Path + '\'
$beforeFree = [System.IO.DriveInfo]::new([System.IO.Path]::GetPathRoot($workspace)).AvailableFreeSpace
$targets = [System.Collections.Generic.List[System.IO.FileInfo]]::new()
$checkedDirectories = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
foreach ($entry in $manifest.files) {
    $absolute = [System.IO.Path]::GetFullPath((Join-Path $workspace $entry.path))
    if (-not $absolute.StartsWith($allowedRoot, [System.StringComparison]::OrdinalIgnoreCase)) { throw "Outside allowed directory: $absolute" }
    $item = Get-Item -LiteralPath $absolute
    if ($item.PSIsContainer -or $item.Name -notmatch '^f?\d+\.png$' -or $item.Directory.Name -notin @('render','komposit')) { throw "Unexpected file: $absolute" }
    if ($item.Length -ne $entry.bytes) { throw "File changed: $absolute" }
    $seconds = ([DateTimeOffset]$item.LastWriteTimeUtc).ToUnixTimeMilliseconds() / 1000.0
    if ([Math]::Abs($seconds - $entry.mtime) -gt 0.01) { throw "File modified: $absolute" }
    if ($checkedDirectories.Add($item.Directory.FullName)) {
        $ancestor = $item.Directory
        while ($ancestor.FullName.StartsWith($workspace, [System.StringComparison]::OrdinalIgnoreCase)) {
            if (($ancestor.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) { throw "Reparse directory: $absolute" }
            $ancestor = $ancestor.Parent
        }
        if (-not (Test-Path -LiteralPath (Join-Path $item.Directory.Parent.FullName 'scen.blend') -PathType Leaf)) { throw "Missing scene: $absolute" }
        if (-not (Test-Path -LiteralPath (Join-Path $item.Directory.Parent.FullName 'plan.json') -PathType Leaf)) { throw "Missing plan: $absolute" }
    }
    $targets.Add($item)
    if ($targets.Count % 5000 -eq 0) { Write-Output "Checked $($targets.Count) paths" }
}
Write-Output ('Validated {0} PNG files; {1:N3} GB' -f $targets.Count, (($targets | Measure-Object Length -Sum).Sum / 1e9))
$logPath = Join-Path $PSScriptRoot 'render-cleanup-deleted-2026-11-21.jsonl'
$log = [System.IO.StreamWriter]::new($logPath, $false, [System.Text.UTF8Encoding]::new($false))
$deletedBytes = 0L
$deletedCount = 0
try {
    foreach ($item in $targets) {
        $bytes = $item.Length
        Remove-Item -LiteralPath $item.FullName -Force
        $log.WriteLine((@{path=$item.FullName; bytes=$bytes} | ConvertTo-Json -Compress))
        $deletedBytes += $bytes
        $deletedCount++
        if ($deletedCount % 2000 -eq 0) { $log.Flush(); Write-Output "Removed $deletedCount files" }
    }
} finally { $log.Dispose() }
$afterFree = [System.IO.DriveInfo]::new([System.IO.Path]::GetPathRoot($workspace)).AvailableFreeSpace
$result = @{deleted_files=$deletedCount; deleted_bytes=$deletedBytes; free_before=$beforeFree; free_after=$afterFree; observed_freed_bytes=($afterFree-$beforeFree)}
$result | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'render-cleanup-result-2026-11-21.json') -Encoding UTF8
$result | ConvertTo-Json
