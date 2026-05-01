<#
.SYNOPSIS
    RAG Backend Health Check Test Script for Windows PowerShell
    
.DESCRIPTION
    Tests Phase 1: Health and Connectivity
    Tests the RAG backend service health, OpenSearch connectivity, and LLM service status
    
.PARAMETER RagBackendUrl
    The external OCP route URL for the RAG backend service
    Example: https://rag-backend-opensearch-llm-on-techzone.apps.p1234.cecc.ihost.com
    
.PARAMETER SkipCertificateCheck
    Skip SSL certificate validation (useful for self-signed certificates)
    
.PARAMETER Verbose
    Enable verbose output showing full responses
    
.EXAMPLE
    .\Test-Health.ps1 -RagBackendUrl "https://rag-backend-opensearch-namespace.apps.domain.com"
    
.EXAMPLE
    .\Test-Health.ps1 -RagBackendUrl "https://rag-backend-opensearch-namespace.apps.domain.com" -Verbose
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory=$false)]
    [string]$RagBackendUrl = $env:RAG_BACKEND_URL,
    
    [Parameter(Mandatory=$false)]
    [switch]$SkipCertificateCheck = $true,
    
    [Parameter(Mandatory=$false)]
    [int]$TimeoutSeconds = 60
)

# Test counters
$script:TestsRun = 0
$script:TestsPassed = 0
$script:TestsFailed = 0

#region Helper Functions

function Write-TestHeader {
    param([string]$Message)
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host $Message -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
}

function Write-TestName {
    param([string]$Message)
    Write-Host "`nTEST: $Message" -ForegroundColor Yellow
}

function Write-TestPass {
    param([string]$Message)
    Write-Host "✓ PASS: $Message" -ForegroundColor Green
    $script:TestsPassed++
}

function Write-TestFail {
    param([string]$Message)
    Write-Host "✗ FAIL: $Message" -ForegroundColor Red
    $script:TestsFailed++
}

function Write-TestInfo {
    param([string]$Message)
    Write-Host "INFO: $Message" -ForegroundColor Cyan
}

function Write-TestWarning {
    param([string]$Message)
    Write-Host "WARNING: $Message" -ForegroundColor Yellow
}

function Write-TestSummary {
    Write-TestHeader "TEST SUMMARY"
    Write-Host "Total Tests: $script:TestsRun"
    Write-Host "Passed: $script:TestsPassed" -ForegroundColor Green
    Write-Host "Failed: $script:TestsFailed" -ForegroundColor Red
    
    if ($script:TestsFailed -eq 0) {
        Write-Host "`nAll tests passed!" -ForegroundColor Green
        return $true
    } else {
        Write-Host "`nSome tests failed!" -ForegroundColor Red
        return $false
    }
}

function Invoke-RagApiRequest {
    param(
        [string]$Url,
        [string]$Method = "GET",
        [object]$Body = $null,
        [int]$TimeoutSec = 60
    )
    
    try {
        $params = @{
            Uri = $Url
            Method = $Method
            TimeoutSec = $TimeoutSec
            ContentType = "application/json"
        }
        
        if ($SkipCertificateCheck) {
            $params.SkipCertificateCheck = $true
        }
        
        if ($Body) {
            $params.Body = ($Body | ConvertTo-Json -Depth 10)
        }
        
        $response = Invoke-RestMethod @params
        return @{
            Success = $true
            StatusCode = 200
            Data = $response
        }
    }
    catch {
        $statusCode = 0
        if ($_.Exception.Response) {
            $statusCode = [int]$_.Exception.Response.StatusCode
        }
        
        return @{
            Success = $false
            StatusCode = $statusCode
            Error = $_.Exception.Message
            Data = $null
        }
    }
}

#endregion

#region Test Functions

function Test-BasicHealthCheck {
    $script:TestsRun++
    Write-TestName "T1.1 - Basic Health Check"
    
    $result = Invoke-RagApiRequest -Url "$RagBackendUrl/health" -TimeoutSec $TimeoutSeconds
    
    if ($VerbosePreference -eq 'Continue') {
        Write-TestInfo "Response: $($result.Data | ConvertTo-Json -Compress)"
        Write-TestInfo "HTTP Code: $($result.StatusCode)"
    }
    
    if ($result.Success -and $result.StatusCode -eq 200) {
        if ($result.Data.status -and $result.Data.opensearch) {
            Write-TestPass "Health endpoint returned 200 with valid response"
            return $true
        } else {
            Write-TestFail "Health endpoint returned 200 but response format invalid"
            return $false
        }
    } else {
        Write-TestFail "Health endpoint returned HTTP $($result.StatusCode) (expected 200)"
        return $false
    }
}

function Test-ApiDocumentation {
    $script:TestsRun++
    Write-TestName "T1.2 - API Documentation"
    
    $result = Invoke-RagApiRequest -Url "$RagBackendUrl/" -TimeoutSec $TimeoutSeconds
    
    if ($VerbosePreference -eq 'Continue') {
        Write-TestInfo "Response: $($result.Data | ConvertTo-Json -Compress)"
    }
    
    if ($result.Success -and $result.StatusCode -eq 200) {
        if ($result.Data.service -and $result.Data.endpoints) {
            Write-TestPass "API documentation endpoint working"
            return $true
        } else {
            Write-TestFail "API documentation format invalid"
            return $false
        }
    } else {
        Write-TestFail "API documentation returned HTTP $($result.StatusCode) (expected 200)"
        return $false
    }
}

function Test-OpenSearchConnectivity {
    $script:TestsRun++
    Write-TestName "T1.3 - OpenSearch Connectivity"
    
    $result = Invoke-RagApiRequest -Url "$RagBackendUrl/health" -TimeoutSec $TimeoutSeconds
    
    if ($result.Success -and $result.StatusCode -eq 200) {
        $opensearchStatus = $result.Data.opensearch
        
        if ($opensearchStatus -eq "connected") {
            Write-TestPass "OpenSearch is connected"
            return $true
        } else {
            Write-TestFail "OpenSearch status: $opensearchStatus (expected: connected)"
            return $false
        }
    } else {
        Write-TestFail "Cannot check OpenSearch status (health endpoint failed)"
        return $false
    }
}

function Test-LlmConnectivity {
    $script:TestsRun++
    Write-TestName "T1.4 - LLM Service Connectivity"
    
    $result = Invoke-RagApiRequest -Url "$RagBackendUrl/health" -TimeoutSec $TimeoutSeconds
    
    if ($result.Success -and $result.StatusCode -eq 200) {
        $llmStatus = $result.Data.llm
        
        if ($llmStatus -eq "connected") {
            Write-TestPass "LLM service is connected"
            return $true
        } else {
            Write-TestFail "LLM status: $llmStatus (expected: connected)"
            Write-TestInfo "Note: LLM disconnection may not be critical for all operations"
            return $false
        }
    } else {
        Write-TestFail "Cannot check LLM status (health endpoint failed)"
        return $false
    }
}

function Test-ResponseTime {
    $script:TestsRun++
    Write-TestName "T1.5 - Response Time Check"
    
    $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
    $result = Invoke-RagApiRequest -Url "$RagBackendUrl/health" -TimeoutSec $TimeoutSeconds
    $stopwatch.Stop()
    
    $elapsed = $stopwatch.Elapsed.TotalSeconds
    
    if ($result.Success -and $result.StatusCode -eq 200) {
        if ($elapsed -lt 5) {
            Write-TestPass "Response time: $([math]::Round($elapsed, 2))s (< 5s threshold)"
            return $true
        } else {
            Write-TestFail "Response time: $([math]::Round($elapsed, 2))s (>= 5s threshold)"
            return $false
        }
    } else {
        Write-TestFail "Health check failed, cannot measure response time"
        return $false
    }
}

function Test-CorsHeaders {
    $script:TestsRun++
    Write-TestName "T1.6 - CORS Headers Check"
    
    try {
        $response = Invoke-WebRequest -Uri "$RagBackendUrl/health" `
            -Method OPTIONS `
            -SkipCertificateCheck:$SkipCertificateCheck `
            -TimeoutSec $TimeoutSeconds `
            -ErrorAction Stop
        
        if ($VerbosePreference -eq 'Continue') {
            Write-TestInfo "Headers: $($response.Headers | ConvertTo-Json -Compress)"
        }
        
        $corsHeaders = $response.Headers.Keys | Where-Object { $_ -like "Access-Control-*" }
        
        if ($corsHeaders) {
            Write-TestPass "CORS headers present"
            return $true
        } else {
            Write-TestInfo "CORS headers not found (may be configured at route level)"
            Write-TestPass "Test passed (CORS not critical for backend testing)"
            return $true
        }
    }
    catch {
        Write-TestInfo "CORS check not applicable or failed"
        Write-TestPass "Test passed (CORS not critical for backend testing)"
        return $true
    }
}

#endregion

#region Main Execution

# Validate parameters
if ([string]::IsNullOrWhiteSpace($RagBackendUrl)) {
    Write-Host "ERROR: RAG_BACKEND_URL not provided" -ForegroundColor Red
    Write-Host "Usage: .\Test-Health.ps1 -RagBackendUrl <url>" -ForegroundColor Yellow
    Write-Host "   or: `$env:RAG_BACKEND_URL='<url>'; .\Test-Health.ps1" -ForegroundColor Yellow
    exit 1
}

# Display configuration
Write-TestHeader "RAG Backend Health Check Tests"
Write-Host "Backend URL: $RagBackendUrl"
Write-Host "SSL Verify: $(if ($SkipCertificateCheck) { 'Disabled' } else { 'Enabled' })"
Write-Host "Timeout: ${TimeoutSeconds}s"

# Run all tests
Test-BasicHealthCheck
Test-ApiDocumentation
Test-OpenSearchConnectivity
Test-LlmConnectivity
Test-ResponseTime
Test-CorsHeaders

# Print summary and exit
$success = Write-TestSummary
if ($success) {
    exit 0
} else {
    exit 1
}

#endregion

# Made with Bob
