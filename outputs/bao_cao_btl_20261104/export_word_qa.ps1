$ErrorActionPreference = 'Stop'
$reportRoot = [System.IO.Path]::GetFullPath($PSScriptRoot)
$reportSource = Join-Path $reportRoot 'BAO_CAO_BTL_M3DIFF.docx'
$qaRoot = Join-Path $reportRoot 'qa_render'
New-Item -ItemType Directory -Force -Path $qaRoot | Out-Null
$reportPdf = Join-Path $qaRoot 'BAO_CAO_BTL_M3DIFF.pdf'
$wordInstance = $null
$reportDocument = $null
try {
    $wordInstance = New-Object -ComObject Word.Application
    $wordInstance.Visible = $false
    $wordInstance.DisplayAlerts = 0
    $wordInstance.AutomationSecurity = 3
    $reportDocument = $wordInstance.Documents.Open($reportSource, $false, $true, $false)
    $reportDocument.Fields.Update() | Out-Null
    $reportDocument.Repaginate()
    $reportPageCount = $reportDocument.ComputeStatistics(2)
    $reportDocument.ExportAsFixedFormat($reportPdf, 17)
    @{ backend = 'Microsoft Word ExportAsFixedFormat'; pages = $reportPageCount; pdf = $reportPdf; source = $reportSource; read_only_source = $true } | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $reportRoot 'WORD_RENDER.json') -Encoding utf8
    Write-Output "Word render completed: $reportPageCount pages"
}
finally {
    if ($null -ne $reportDocument) {
        $reportDocument.Close(0)
        [System.Runtime.InteropServices.Marshal]::ReleaseComObject($reportDocument) | Out-Null
    }
    if ($null -ne $wordInstance) {
        $wordInstance.Quit(0)
        [System.Runtime.InteropServices.Marshal]::ReleaseComObject($wordInstance) | Out-Null
    }
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
}
