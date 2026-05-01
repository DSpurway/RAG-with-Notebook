# Copy IBM Power PDFs to OpenSearch backend pod
# Change to the script directory
Set-Location $PSScriptRoot

Write-Host 'Copying IBM Power PDFs to OpenSearch backend...' -ForegroundColor Cyan

# Get the actual pod name
$podName = (oc get pods -l app=rag-backend-opensearch -o jsonpath='{.items[0].metadata.name}')
Write-Host "Target pod: $podName" -ForegroundColor Cyan

$pdfs = @(
    'IBM_Power_S1012.pdf',
    'IBM_Power_S1014.pdf',
    'IBM_Power_S1022.pdf',
    'IBM_Power_S1022s.pdf',
    'IBM_Power_S1024.pdf'
)

foreach ($pdf in $pdfs) {
    Write-Host "Copying $pdf..." -ForegroundColor Yellow
    oc cp $pdf ${podName}:/app/pdfs/$pdf
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  Success: $pdf copied" -ForegroundColor Green
    } else {
        Write-Host "  Failed: $pdf" -ForegroundColor Red
    }
}

Write-Host "`nVerifying PDFs in pod..." -ForegroundColor Cyan
oc exec $podName -- ls -lh /app/pdfs/

Write-Host "`nPDFs are ready! You can now load them in the UI:" -ForegroundColor Green
Write-Host "  - IBM_Power_S1012" -ForegroundColor White
Write-Host "  - IBM_Power_S1014" -ForegroundColor White
Write-Host "  - IBM_Power_S1022" -ForegroundColor White
Write-Host "  - IBM_Power_S1022s" -ForegroundColor White
Write-Host "  - IBM_Power_S1024" -ForegroundColor White

# Made with Bob
