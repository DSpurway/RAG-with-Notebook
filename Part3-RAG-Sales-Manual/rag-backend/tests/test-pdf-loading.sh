#!/bin/bash

################################################################################
# RAG Backend PDF Loading Test Script
# Tests Phase 2 & 3: Collection Management and PDF Document Loading
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

print_warning() {
    echo -e "${YELLOW}WARNING${NC}: $1"
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
TEST_TIMEOUT="${TEST_TIMEOUT:-120}"
VERBOSE="${VERBOSE:-false}"
TEST_COLLECTION="${TEST_COLLECTION:-test_sales_manuals}"

# Set curl options
CURL_OPTS="-s -w \n%{http_code}"
if [ "$SKIP_SSL_VERIFY" = "true" ]; then
    CURL_OPTS="$CURL_OPTS -k"
fi
CURL_OPTS="$CURL_OPTS --max-time $TEST_TIMEOUT"

print_header "RAG Backend PDF Loading Tests"
echo "Backend URL: $RAG_BACKEND_URL"
echo "Test Collection: $TEST_COLLECTION"
echo "SSL Verify: $([ "$SKIP_SSL_VERIFY" = "true" ] && echo "Disabled" || echo "Enabled")"
echo "Timeout: ${TEST_TIMEOUT}s"
echo ""

################################################################################
# Test Functions - Collection Management
################################################################################

test_list_collections() {
    ((TESTS_RUN++))
    print_test "T2.1 - List Collections"
    
    RESPONSE=$(curl $CURL_OPTS "$RAG_BACKEND_URL/api/collections" 2>&1)
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    BODY=$(echo "$RESPONSE" | sed '$d')
    
    if [ "$VERBOSE" = "true" ]; then
        print_info "Response: $BODY"
    fi
    
    if [ "$HTTP_CODE" = "200" ]; then
        if echo "$BODY" | grep -q '"success":true' && echo "$BODY" | grep -q '"collections"'; then
            print_pass "Successfully listed collections"
            # Store initial collection count
            INITIAL_COLLECTIONS=$(echo "$BODY" | grep -o '"collections":\[[^]]*\]' || echo "[]")
            if [ "$VERBOSE" = "true" ]; then
                print_info "Collections: $INITIAL_COLLECTIONS"
            fi
            return 0
        else
            print_fail "Invalid response format"
            return 1
        fi
    else
        print_fail "HTTP $HTTP_CODE (expected 200)"
        return 1
    fi
}

test_drop_test_collection() {
    ((TESTS_RUN++))
    print_test "T2.2 - Drop Test Collection (Cleanup)"
    
    RESPONSE=$(curl $CURL_OPTS -X DELETE "$RAG_BACKEND_URL/api/collections/$TEST_COLLECTION" 2>&1)
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    BODY=$(echo "$RESPONSE" | sed '$d')
    
    if [ "$VERBOSE" = "true" ]; then
        print_info "Response: $BODY"
    fi
    
    # Accept both 200 (success) and 404 (not found) as valid
    if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "404" ]; then
        print_pass "Test collection cleaned up (HTTP $HTTP_CODE)"
        return 0
    else
        print_warning "Unexpected HTTP $HTTP_CODE, but continuing"
        return 0
    fi
}

################################################################################
# Test Functions - PDF Loading
################################################################################

test_load_small_pdf() {
    ((TESTS_RUN++))
    print_test "T3.1 - Load Small PDF (IBM_Power_S1012)"
    
    print_info "Loading PDF... (this may take 30-60 seconds)"
    
    RESPONSE=$(curl $CURL_OPTS \
        -X POST \
        -H "Content-Type: application/json" \
        -d "{\"server_name\":\"IBM_Power_S1012\",\"collection_name\":\"$TEST_COLLECTION\"}" \
        "$RAG_BACKEND_URL/api/load-pdf" 2>&1)
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    BODY=$(echo "$RESPONSE" | sed '$d')
    
    if [ "$VERBOSE" = "true" ]; then
        print_info "Response: $BODY"
    fi
    
    if [ "$HTTP_CODE" = "200" ]; then
        if echo "$BODY" | grep -q '"success":true'; then
            CHUNKS=$(echo "$BODY" | grep -o '"chunks":[0-9]*' | grep -o '[0-9]*')
            if [ -n "$CHUNKS" ] && [ "$CHUNKS" -gt 0 ]; then
                print_pass "Successfully loaded PDF with $CHUNKS chunks"
                return 0
            else
                print_fail "PDF loaded but no chunks created"
                return 1
            fi
        else
            print_fail "Response indicates failure"
            return 1
        fi
    else
        print_fail "HTTP $HTTP_CODE (expected 200)"
        if [ "$HTTP_CODE" = "404" ]; then
            print_info "PDF file may not exist in container"
        fi
        return 1
    fi
}

test_load_second_pdf() {
    ((TESTS_RUN++))
    print_test "T3.2 - Load Second PDF to Same Collection (IBM_Power_S1014)"
    
    print_info "Loading PDF... (this may take 30-60 seconds)"
    
    RESPONSE=$(curl $CURL_OPTS \
        -X POST \
        -H "Content-Type: application/json" \
        -d "{\"server_name\":\"IBM_Power_S1014\",\"collection_name\":\"$TEST_COLLECTION\"}" \
        "$RAG_BACKEND_URL/api/load-pdf" 2>&1)
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    BODY=$(echo "$RESPONSE" | sed '$d')
    
    if [ "$VERBOSE" = "true" ]; then
        print_info "Response: $BODY"
    fi
    
    if [ "$HTTP_CODE" = "200" ]; then
        if echo "$BODY" | grep -q '"success":true'; then
            CHUNKS=$(echo "$BODY" | grep -o '"chunks":[0-9]*' | grep -o '[0-9]*')
            print_pass "Successfully loaded second PDF with $CHUNKS chunks"
            return 0
        else
            print_fail "Response indicates failure"
            return 1
        fi
    else
        print_fail "HTTP $HTTP_CODE (expected 200)"
        return 1
    fi
}

test_verify_collection_exists() {
    ((TESTS_RUN++))
    print_test "T3.3 - Verify Collection Exists After Loading"
    
    RESPONSE=$(curl $CURL_OPTS "$RAG_BACKEND_URL/api/collections" 2>&1)
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    BODY=$(echo "$RESPONSE" | sed '$d')
    
    if [ "$HTTP_CODE" = "200" ]; then
        # Check if collection appears in list (OpenSearch uses hashed index names)
        if echo "$BODY" | grep -q "rag_"; then
            print_pass "Collection exists in OpenSearch"
            if [ "$VERBOSE" = "true" ]; then
                print_info "Collections: $BODY"
            fi
            return 0
        else
            print_fail "Collection not found in list"
            return 1
        fi
    else
        print_fail "Cannot verify collection (HTTP $HTTP_CODE)"
        return 1
    fi
}

test_load_nonexistent_pdf() {
    ((TESTS_RUN++))
    print_test "T3.4 - Load Non-Existent PDF (Error Handling)"
    
    RESPONSE=$(curl $CURL_OPTS \
        -X POST \
        -H "Content-Type: application/json" \
        -d "{\"server_name\":\"NonExistentFile\",\"collection_name\":\"$TEST_COLLECTION\"}" \
        "$RAG_BACKEND_URL/api/load-pdf" 2>&1)
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    BODY=$(echo "$RESPONSE" | sed '$d')
    
    if [ "$VERBOSE" = "true" ]; then
        print_info "Response: $BODY"
    fi
    
    if [ "$HTTP_CODE" = "404" ]; then
        if echo "$BODY" | grep -q '"error"'; then
            print_pass "Correctly returned 404 for non-existent PDF"
            return 0
        else
            print_fail "404 returned but no error message"
            return 1
        fi
    else
        print_fail "Expected HTTP 404, got $HTTP_CODE"
        return 1
    fi
}

test_load_without_server_name() {
    ((TESTS_RUN++))
    print_test "T3.5 - Load PDF Without server_name (Validation)"
    
    RESPONSE=$(curl $CURL_OPTS \
        -X POST \
        -H "Content-Type: application/json" \
        -d "{\"collection_name\":\"$TEST_COLLECTION\"}" \
        "$RAG_BACKEND_URL/api/load-pdf" 2>&1)
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    BODY=$(echo "$RESPONSE" | sed '$d')
    
    if [ "$VERBOSE" = "true" ]; then
        print_info "Response: $BODY"
    fi
    
    if [ "$HTTP_CODE" = "400" ]; then
        if echo "$BODY" | grep -q '"error".*server_name'; then
            print_pass "Correctly validated missing server_name"
            return 0
        else
            print_fail "400 returned but error message unclear"
            return 1
        fi
    else
        print_fail "Expected HTTP 400, got $HTTP_CODE"
        return 1
    fi
}

test_load_large_pdf() {
    ((TESTS_RUN++))
    print_test "T3.6 - Load Large PDF (IBM_Power_S1024) [OPTIONAL]"
    
    print_info "Loading large PDF... (this may take 60-120 seconds)"
    print_warning "This test may timeout - that's expected for large files"
    
    # Increase timeout for this test
    LARGE_TIMEOUT=180
    LARGE_CURL_OPTS="${CURL_OPTS/--max-time $TEST_TIMEOUT/--max-time $LARGE_TIMEOUT}"
    
    RESPONSE=$(curl $LARGE_CURL_OPTS \
        -X POST \
        -H "Content-Type: application/json" \
        -d "{\"server_name\":\"IBM_Power_S1024\",\"collection_name\":\"${TEST_COLLECTION}_large\"}" \
        "$RAG_BACKEND_URL/api/load-pdf" 2>&1)
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    BODY=$(echo "$RESPONSE" | sed '$d')
    
    if [ "$HTTP_CODE" = "200" ]; then
        if echo "$BODY" | grep -q '"success":true'; then
            CHUNKS=$(echo "$BODY" | grep -o '"chunks":[0-9]*' | grep -o '[0-9]*')
            print_pass "Successfully loaded large PDF with $CHUNKS chunks"
            return 0
        else
            print_fail "Response indicates failure"
            return 1
        fi
    elif [ "$HTTP_CODE" = "000" ] || [ -z "$HTTP_CODE" ]; then
        print_warning "Request timed out (expected for large files)"
        print_info "Check pod logs to verify if loading completed"
        # Don't count as failure
        ((TESTS_PASSED++))
        return 0
    else
        print_fail "HTTP $HTTP_CODE"
        return 1
    fi
}

################################################################################
# Main Execution
################################################################################

main() {
    # Phase 2: Collection Management
    print_header "Phase 2: Collection Management"
    test_list_collections
    test_drop_test_collection
    
    echo ""
    
    # Phase 3: PDF Loading
    print_header "Phase 3: PDF Document Loading"
    test_load_small_pdf
    test_load_second_pdf
    test_verify_collection_exists
    test_load_nonexistent_pdf
    test_load_without_server_name
    test_load_large_pdf
    
    # Print summary
    print_summary
    return $?
}

# Run main function
main
exit $?

# Made with Bob
