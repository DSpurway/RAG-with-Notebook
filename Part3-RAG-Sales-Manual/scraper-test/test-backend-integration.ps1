# Test Backend Integration
# Sends scraped E1180 data to the RAG backend

$BACKEND_URL = "https://rag-backend-llm-on-techzone.apps.p1219.cecc.ihost.com"

# Skip SSL certificate validation for self-signed certs
add-type @"
    using System.Net;
    using System.Security.Cryptography.X509Certificates;
    public class TrustAllCertsPolicy : ICertificatePolicy {
        public bool CheckValidationResult(
            ServicePoint srvPoint, X509Certificate certificate,
            WebRequest request, int certificateProblem) {
            return true;
        }
    }
"@
[System.Net.ServicePointManager]::CertificatePolicy = New-Object TrustAllCertsPolicy
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.SecurityProtocolType]::Tls12

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "  Testing Backend Integration" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

# Check if e1180.json exists
if (-not (Test-Path "e1180.json")) {
    Write-Host "Error: e1180.json not found!" -ForegroundColor Red
    Write-Host "Please run the scraper first:" -ForegroundColor Yellow
    Write-Host '  python windows_scraper.py "https://www.ibm.com/docs/en/announcements/family-908005-power-e1180-enterprise-server-9080-heu" --output e1180.json' -ForegroundColor Gray
    exit 1
}

Write-Host "[1/3] Checking backend health..." -ForegroundColor Yellow
try {
    $health = Invoke-RestMethod -Uri "$BACKEND_URL/health" -Method Get -TimeoutSec 10
    Write-Host "  OK Backend is healthy" -ForegroundColor Green
    Write-Host "  Backend: $($health | ConvertTo-Json -Depth 1)" -ForegroundColor Gray
} catch {
    Write-Host "  X Backend health check failed" -ForegroundColor Red
    Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    Write-Host "  Note: The backend might not have a /health endpoint yet." -ForegroundColor Yellow
    Write-Host "  Continuing anyway..." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "[2/3] Loading scraped data..." -ForegroundColor Yellow
$scrapedData = Get-Content "e1180.json" -Raw | ConvertFrom-Json
Write-Host "  OK Loaded e1180.json" -ForegroundColor Green
Write-Host "  Title: $($scrapedData.page_title)" -ForegroundColor Gray
Write-Host "  Sections: $($scrapedData.sections.Count)" -ForegroundColor Gray
Write-Host "  Quality Score: $($scrapedData.quality_score.score)%" -ForegroundColor Gray

Write-Host ""
Write-Host "[3/3] Sending data to backend..." -ForegroundColor Yellow
Write-Host "  Endpoint: $BACKEND_URL/ingest-scraped-content" -ForegroundColor Gray

try {
    $jsonBody = $scrapedData | ConvertTo-Json -Depth 10 -Compress
    $utf8Bytes = [System.Text.Encoding]::UTF8.GetBytes($jsonBody)
    
    $response = Invoke-RestMethod -Uri "$BACKEND_URL/ingest-scraped-content" `
        -Method Post `
        -Body $utf8Bytes `
        -ContentType "application/json; charset=utf-8" `
        -TimeoutSec 60
    
    Write-Host "  OK Data sent successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Backend Response:" -ForegroundColor Cyan
    Write-Host ($response | ConvertTo-Json -Depth 3) -ForegroundColor Gray
    
} catch {
    Write-Host "  X Failed to send data" -ForegroundColor Red
    Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    
    if ($_.Exception.Response) {
        $statusCode = $_.Exception.Response.StatusCode.value__
        Write-Host "  HTTP Status: $statusCode" -ForegroundColor Yellow
        
        if ($statusCode -eq 404) {
            Write-Host ""
            Write-Host "  The /ingest-scraped-content endpoint doesn't exist yet." -ForegroundColor Yellow
            Write-Host "  You need to add this endpoint to your RAG backend." -ForegroundColor Yellow
        }
    }
}

Write-Host ""
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "  Test Complete" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan

# Made with Bob
