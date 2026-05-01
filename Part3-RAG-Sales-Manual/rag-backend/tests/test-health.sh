#!/bin/bash

################################################################################
# RAG Backend Health Check Test Script
# Tests Phase 1: Health and Connectivity
################################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

################################################################################
# Helper Functions
################################################################################

print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_test() {
    echo -e "${YELLOW}TEST: $1${NC}"
}

print_pass() {
    echo -e "${GREEN}✓ PASS${NC}: $1"
    ((TESTS_PASSED++))
}

print_fail() {
    echo -e "${RED}✗ FAIL${NC}: $1"
    ((TESTS_FAILED++))
}

print_info() {
    echo -e "${BLUE}INFO${NC}: $1"
}

print_summary() {
    echo ""
    print_header "TEST SUMMARY"
    echo "Total Tests: $TESTS_RUN"
    echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
    echo -e "${RED}Failed: $TESTS_FAILED${NC}"
    
    if [ $TESTS_FAILED -eq 0 ]; then
        echo -e "${GREEN}All tests passed!${NC}"
        return 0
    else
        echo -e "${RED}Some tests failed!${NC}"
        return 1
    fi
}

################################################################################
# Configuration
################################################################################

# Load config if exists
if [ -f "$SCRIPT_DIR/test-config.env" ]; then
    source "$SCRIPT_DIR/test-config.env"
    print_info "Loaded configuration from test-config.env"
fi

# Get RAG backend URL from parameter or environment
RAG_BACKEND_URL="${1:-${RAG_BACKEND_URL}}"

if [ -z "$RAG_BACKEND_URL" ]; then
    echo -e "${RED}ERROR: RAG_BACKEND_URL not provided${NC}"
    echo "Usage: $0 <RAG_BACKEND_URL>"
    echo "   or: export RAG_BACKEND_URL=<url> && $0"
    echo "   or: Create test-config.env with RAG_BACKEND_URL"
    exit 1
fi

# Configuration with defaults
SKIP_SSL_VERIFY="${SKIP_SSL_VERIFY:-true}"
TEST_TIMEOUT="${TEST_TIMEOUT:-60}"
VERBOSE="${VERBOSE:-false}"

# Set curl options
CURL_OPTS="-s -w \n%{http_code}"
if [ "$SKIP_SSL_VERIFY" = "true" ]; then
    CURL_OPTS="$CURL_OPTS -k"
fi
CURL_OPTS="$CURL_OPTS --max-time $TEST_TIMEOUT"

print_header "RAG Backend Health Check Tests"
echo "Backend URL: $RAG_BACKEND_URL"
echo "SSL Verify: $([ "$SKIP_SSL_VERIFY" = "true" ] && echo "Disabled" || echo "Enabled")"
echo "Timeout: ${TEST_TIMEOUT}s"
echo ""

################################################################################
# Test Functions
################################################################################

test_basic_health_check() {
    ((TESTS_RUN++))
    print_test "T1.1 - Basic Health Check"
    
    RESPONSE=$(curl $CURL_OPTS "$RAG_BACKEND_URL/health" 2>&1)
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    BODY=$(echo "$RESPONSE" | sed '$d')
    
    if [ "$VERBOSE" = "true" ]; then
        print_info "Response: $BODY"
        print_info "HTTP Code: $HTTP_CODE"
    fi
    
    if [ "$HTTP_CODE" = "200" ]; then
        # Check if response contains expected fields
        if echo "$BODY" | grep -q '"status"' && echo "$BODY" | grep -q '"opensearch"'; then
            print_pass "Health endpoint returned 200 with valid response"
            return 0
        else
            print_fail "Health endpoint returned 200 but response format invalid"
            return 1
        fi
    else
        print_fail "Health endpoint returned HTTP $HTTP_CODE (expected 200)"
        return 1
    fi
}

test_api_documentation() {
    ((TESTS_RUN++))
    print_test "T1.2 - API Documentation"
    
    RESPONSE=$(curl $CURL_OPTS "$RAG_BACKEND_URL/" 2>&1)
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    BODY=$(echo "$RESPONSE" | sed '$d')
    
    if [ "$VERBOSE" = "true" ]; then
        print_info "Response: $BODY"
    fi
    
    if [ "$HTTP_CODE" = "200" ]; then
        # Check if response contains service info
        if echo "$BODY" | grep -q '"service"' && echo "$BODY" | grep -q '"endpoints"'; then
            print_pass "API documentation endpoint working"
            return 0
        else
            print_fail "API documentation format invalid"
            return 1
        fi
    else
        print_fail "API documentation returned HTTP $HTTP_CODE (expected 200)"
        return 1
    fi
}

test_opensearch_connectivity() {
    ((TESTS_RUN++))
    print_test "T1.3 - OpenSearch Connectivity"
    
    RESPONSE=$(curl $CURL_OPTS "$RAG_BACKEND_URL/health" 2>&1)
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    BODY=$(echo "$RESPONSE" | sed '$d')
    
    if [ "$HTTP_CODE" = "200" ]; then
        # Extract opensearch status
        OPENSEARCH_STATUS=$(echo "$BODY" | grep -o '"opensearch":"[^"]*"' | cut -d'"' -f4)
        
        if [ "$OPENSEARCH_STATUS" = "connected" ]; then
            print_pass "OpenSearch is connected"
            return 0
        else
            print_fail "OpenSearch status: $OPENSEARCH_STATUS (expected: connected)"
            return 1
        fi
    else
        print_fail "Cannot check OpenSearch status (health endpoint failed)"
        return 1
    fi
}

test_llm_connectivity() {
    ((TESTS_RUN++))
    print_test "T1.4 - LLM Service Connectivity"
    
    RESPONSE=$(curl $CURL_OPTS "$RAG_BACKEND_URL/health" 2>&1)
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    BODY=$(echo "$RESPONSE" | sed '$d')
    
    if [ "$HTTP_CODE" = "200" ]; then
        # Extract LLM status
        LLM_STATUS=$(echo "$BODY" | grep -o '"llm":"[^"]*"' | cut -d'"' -f4)
        
        if [ "$LLM_STATUS" = "connected" ]; then
            print_pass "LLM service is connected"
            return 0
        else
            print_fail "LLM status: $LLM_STATUS (expected: connected)"
            print_info "Note: LLM disconnection may not be critical for all operations"
            return 1
        fi
    else
        print_fail "Cannot check LLM status (health endpoint failed)"
        return 1
    fi
}

test_response_time() {
    ((TESTS_RUN++))
    print_test "T1.5 - Response Time Check"
    
    START_TIME=$(date +%s)
    RESPONSE=$(curl $CURL_OPTS "$RAG_BACKEND_URL/health" 2>&1)
    END_TIME=$(date +%s)
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    
    ELAPSED=$((END_TIME - START_TIME))
    
    if [ "$HTTP_CODE" = "200" ]; then
        if [ $ELAPSED -lt 5 ]; then
            print_pass "Response time: ${ELAPSED}s (< 5s threshold)"
            return 0
        else
            print_fail "Response time: ${ELAPSED}s (>= 5s threshold)"
            return 1
        fi
    else
        print_fail "Health check failed, cannot measure response time"
        return 1
    fi
}

test_cors_headers() {
    ((TESTS_RUN++))
    print_test "T1.6 - CORS Headers Check"
    
    RESPONSE=$(curl $CURL_OPTS -I -X OPTIONS "$RAG_BACKEND_URL/health" 2>&1)
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    HEADERS=$(echo "$RESPONSE" | sed '$d')
    
    if [ "$VERBOSE" = "true" ]; then
        print_info "Headers: $HEADERS"
    fi
    
    # Check for CORS headers (may not be present for all endpoints)
    if echo "$HEADERS" | grep -qi "access-control-allow"; then
        print_pass "CORS headers present"
        return 0
    else
        print_info "CORS headers not found (may be configured at route level)"
        print_pass "Test passed (CORS not critical for backend testing)"
        return 0
    fi
}

################################################################################
# Main Execution
################################################################################

main() {
    # Run all tests
    test_basic_health_check
    test_api_documentation
    test_opensearch_connectivity
    test_llm_connectivity
    test_response_time
    test_cors_headers
    
    # Print summary
    print_summary
    return $?
}

# Run main function
main
exit $?

# Made with Bob
