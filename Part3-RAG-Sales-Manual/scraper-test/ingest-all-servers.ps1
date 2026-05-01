<#
.SYNOPSIS
    Batch ingest IBM Power server documentation into RAG system
.DESCRIPTION
    Reads server list from ibm-power-servers.json and scrapes/ingests each server's Sales Manual
.PARAMETER ServerModel
    Optional: Specific server model to ingest (e.g., "E1180"). If not specified, processes all servers.
.PARAMETER SkipIndexed
    Skip servers that are already marked as indexed in the JSON file
.EXAMPLE
    .\ingest-all-servers.ps1
    .\ingest-all-servers.ps1 -ServerModel E1180
    .\ingest-all-servers.ps1 -SkipIndexed
#>

param(
    [string]$ServerModel = "",
    [switch]$SkipIndexed = $false
)

$ErrorActionPreference = "Stop"

# Configuration
$BACKEND_URL = "https://rag-backend-llm-on-techzone.apps.p1219.cecc.ihost.com"
$SERVERS_JSON = "ibm-power-servers.json"
$SCRAPER_SCRIPT = "windows_scraper.py"

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "  IBM Power Server Documentation Batch Ingestion" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

# Check if files exist
if (-not (Test-Path $SERVERS_JSON)) {
    Write-Host "ERROR: $SERVERS_JSON not found!" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $SCRAPER_SCRIPT)) {
    Write-Host "ERROR: $SCRAPER_SCRIPT not found!" -ForegroundColor Red
    exit 1
}

# Load server list
Write-Host "[1/3] Loading server list from $SERVERS_JSON..." -ForegroundColor Yellow
$serversData = Get-Content $SERVERS_JSON | ConvertFrom-Json
$servers = $serversData.servers

if ($ServerModel) {
    $servers = $servers | Where-Object { $_.model -eq $ServerModel }
    if ($servers.Count -eq 0) {
        Write-Host "ERROR: Server model '$ServerModel' not found in $SERVERS_JSON" -ForegroundColor Red
        exit 1
    }
    Write-Host "  Found 1 server matching '$ServerModel'" -ForegroundColor Green
} else {
    Write-Host "  Found $($servers.Count) servers in configuration" -ForegroundColor Green
}

if ($SkipIndexed) {
    $servers = $servers | Where-Object { $_.status -ne "indexed" }
    Write-Host "  Filtering to $($servers.Count) servers (skipping already indexed)" -ForegroundColor Green
}

Write-Host ""

# Process each server
$successCount = 0
$failCount = 0
$skippedCount = 0

Write-Host "[2/3] Processing servers..." -ForegroundColor Yellow
Write-Host ""

foreach ($server in $servers) {
    Write-Host "--------------------------------------------------------------------------------" -ForegroundColor Cyan
    Write-Host "Server: $($server.model) - $($server.name)" -ForegroundColor White
    Write-Host "Processor: $($server.processor)" -ForegroundColor Gray
    Write-Host "URL: $($server.url)" -ForegroundColor Gray
    Write-Host ""
    
    # Check if already indexed
    if ($server.status -eq "indexed" -and -not $ServerModel) {
        Write-Host "  SKIPPED: Already indexed" -ForegroundColor Yellow
        $skippedCount++
        Write-Host ""
        continue
    }
    
    # Run scraper with server model parameter
    Write-Host "  Scraping and ingesting to collection: power_$($server.model.ToLower())..." -ForegroundColor Yellow
    try {
        $output = python $SCRAPER_SCRIPT $server.url --backend $BACKEND_URL --server-model $server.model 2>&1
        
        # Check for success indicators in output
        if ($output -match "Successfully scraped" -or $output -match "Quality Score: 100") {
            Write-Host "  SUCCESS: Scraped and ingested $($server.model) to power_$($server.model.ToLower())" -ForegroundColor Green
            $successCount++
            
            # Update JSON to mark as indexed (optional - requires updating the file)
            # This would require reading, modifying, and writing back the JSON
        } else {
            Write-Host "  FAILED: Check output for errors" -ForegroundColor Red
            Write-Host $output -ForegroundColor Gray
            $failCount++
        }
    } catch {
        Write-Host "  ERROR: $($_.Exception.Message)" -ForegroundColor Red
        $failCount++
    }
    
    Write-Host ""
    
    # Add delay between requests to be nice to IBM's servers
    if ($servers.IndexOf($server) -lt ($servers.Count - 1)) {
        Write-Host "  Waiting 5 seconds before next server..." -ForegroundColor Gray
        Start-Sleep -Seconds 5
    }
}

# Summary
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "  Ingestion Complete" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Results:" -ForegroundColor White
Write-Host "  Success: $successCount" -ForegroundColor Green
Write-Host "  Failed:  $failCount" -ForegroundColor $(if ($failCount -gt 0) { "Red" } else { "Gray" })
Write-Host "  Skipped: $skippedCount" -ForegroundColor Yellow
Write-Host ""

if ($successCount -gt 0) {
    Write-Host "You can now query the indexed servers via:" -ForegroundColor Cyan
    Write-Host "  - Carbon UI: C:\Users\029878866\EMEA-AI-SQUAD\RAG-with-Notebook\Part3-RAG-Sales-Manual\carbon-rag-ui" -ForegroundColor Gray
    Write-Host "  - API: $BACKEND_URL/api/generate" -ForegroundColor Gray
}

Write-Host ""

# Made with Bob
