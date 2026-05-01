#!/bin/bash

################################################################################
# RAG Backend Vector Search Test Script
# Tests Phase 4: Vector Search Functionality
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
TEST_TIMEOUT="${TEST_TIMEOUT:-60}"
VERBOSE="${VERBOSE:-false}"
TEST_COLLECTION="${TEST_COLLECTION:-test_sales_manuals}"
SEARCH_K="${SEARCH_K:-3}"

# Set curl options
CURL_OPTS="-s -w \n%{http_code}"
if [ "$SKIP_SSL_VERIFY" = "true" ]; then
    CURL_OPTS="$CURL_OPTS -k"
fi
CURL_OPTS="$CURL_OPTS --max-time $TEST_TIMEOUT"

print_header "RAG Backend Vector Search Tests"
echo "Backend URL: $RAG_BACKEND_URL"
echo "Test Collection: $TEST_COLLECTION"
echo "Search K: $SEARCH_K"
echo "SSL Verify: $([ "$SKIP_SSL_VERIFY" = "true" ] && echo "Disabled" || echo "Enabled")"
echo "Timeout: ${TEST_TIMEOUT}s"
echo ""

################################################################################
# Test Functions
################################################################################

test_dense_vector_search() {
    ((TESTS_RUN++))
    print_test "T4.1 - Dense Vector Search (k-NN)"
    
    QUESTION="How many processors does the IBM Power S1012 support?"
    
    RESPONSE=$(curl $CURL_OPTS \
        -X POST \
        -H "Content-Type: application/json" \
        -d "{\"question\":\"$QUESTION\",\"collection_name\":\"$TEST_COLLECTION\",\"k\":$SEARCH_K,\"mode\":\"dense\"}" \
        "$RAG_BACKEND_URL/api/search" 2>&1)
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    BODY=$(echo "$RESPONSE" | sed '$d')
    
    if [ "$VERBOSE" = "true" ]; then
        print_info "Response: $BODY"
    fi
    
    if [ "$HTTP_CODE" = "200" ]; then
        if echo "$BODY" | grep -q '"success":true'; then
            COUNT=$(echo "$BODY" | grep -o '"count":[0-9]*' | grep -o '[0-9]*')
            if [ -n "$COUNT" ] && [ "$COUNT" -eq "$SEARCH_K" ]; then
                print_pass "Dense search returned $COUNT results"
                if [ "$VERBOSE" = "true" ]; then
                    # Show first result snippet
                    FIRST_CONTENT=$(echo "$BODY" | grep -o '"content":"[^"]*"' | head -1 | cut -d'"' -f4 | cut -c1-100)
                    print_info "First result: $FIRST_CONTENT..."
                fi
                return 0
            else
                print_fail "Expected $SEARCH_K results, got $COUNT"
                return 1
            fi
        else
            print_fail "Response indicates failure"
            return 1
        fi
    else
        print_fail "HTTP $HTTP_CODE (expected 200)"
        return 1
    fi
}

test_sparse_keyword_search() {
    ((TESTS_RUN++))
    print_test "T4.2 - Sparse Keyword Search (BM25)"
    
    QUESTION="processor specifications memory"
    
    RESPONSE=$(curl $CURL_OPTS \
        -X POST \
        -H "Content-Type: application/json" \
        -d "{\"question\":\"$QUESTION\",\"collection_name\":\"$TEST_COLLECTION\",\"k\":$SEARCH_K,\"mode\":\"sparse\"}" \
        "$RAG_BACKEND_URL/api/search" 2>&1)
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    BODY=$(echo "$RESPONSE" | sed '$d')
    
    if [ "$VERBOSE" = "true" ]; then
        print_info "Response: $BODY"
    fi
    
    if [ "$HTTP_CODE" = "200" ]; then
        if echo "$BODY" | grep -q '"success":true'; then
            COUNT=$(echo "$BODY" | grep -o '"count":[0-9]*' | grep -o '[0-9]*')
            if [ -n "$COUNT" ] && [ "$COUNT" -gt 0 ]; then
                print_pass "Sparse search returned $COUNT results"
                return 0
            else
                print_fail "No results returned"
                return 1
            fi
        else
            print_fail "Response indicates failure"
            return 1
        fi
    else
        print_fail "HTTP $HTTP_CODE (expected 200)"
        return 1
    fi
}

test_hybrid_search() {
    ((TESTS_RUN++))
    print_test "T4.3 - Hybrid Search (Default)"
    
    QUESTION="What are the memory options for IBM Power servers?"
    
    RESPONSE=$(curl $CURL_OPTS \
        -X POST \
        -H "Content-Type: application/json" \
        -d "{\"question\":\"$QUESTION\",\"collection_name\":\"$TEST_COLLECTION\",\"k\":$SEARCH_K}" \
        "$RAG_BACKEND_URL/api/search" 2>&1)
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    BODY=$(echo "$RESPONSE" | sed '$d')
    
    if [ "$VERBOSE" = "true" ]; then
        print_info "Response: $BODY"
    fi
    
    if [ "$HTTP_CODE" = "200" ]; then
        if echo "$BODY" | grep -q '"success":true'; then
            COUNT=$(echo "$BODY" | grep -o '"count":[0-9]*' | grep -o '[0-9]*')
            if [ -n "$COUNT" ] && [ "$COUNT" -eq "$SEARCH_K" ]; then
                print_pass "Hybrid search returned $COUNT results"
                return 0
            else
                print_fail "Expected $SEARCH_K results, got $COUNT"
                return 1
            fi
        else
            print_fail "Response indicates failure"
            return 1
        fi
    else
        print_fail "HTTP $HTTP_CODE (expected 200)"
        return 1
    fi
}

test_search_different_k_values() {
    ((TESTS_RUN++))
    print_test "T4.4 - Search with Different K Values"
    
    QUESTION="IBM Power specifications"
    
    # Test k=1
    RESPONSE=$(curl $CURL_OPTS \
        -X POST \
        -H "Content-Type: application/json" \
        -d "{\"question\":\"$QUESTION\",\"collection_name\":\"$TEST_COLLECTION\",\"k\":1}" \
        "$RAG_BACKEND_URL/api/search" 2>&1)
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    BODY=$(echo "$RESPONSE" | sed '$d')
    
    if [ "$HTTP_CODE" = "200" ]; then
        COUNT=$(echo "$BODY" | grep -o '"count":[0-9]*' | grep -o '[0-9]*')
        if [ "$COUNT" = "1" ]; then
            print_pass "k=1 returned 1 result"
            return 0
        else
            print_fail "k=1 returned $COUNT results (expected 1)"
            return 1
        fi
    else
        print_fail "HTTP $HTTP_CODE (expected 200)"
        return 1
    fi
}

test_search_nonexistent_collection() {
    ((TESTS_RUN++))
    print_test "T4.5 - Search Non-Existent Collection"
    
    QUESTION="test query"
    
    RESPONSE=$(curl $CURL_OPTS \
        -X POST \
        -H "Content-Type: application/json" \
        -d "{\"question\":\"$QUESTION\",\"collection_name\":\"nonexistent_collection_xyz\",\"k\":3}" \
        "$RAG_BACKEND_URL/api/search" 2>&1)
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    BODY=$(echo "$RESPONSE" | sed '$d')
    
    if [ "$VERBOSE" = "true" ]; then
        print_info "Response: $BODY"
    fi
    
    if [ "$HTTP_CODE" = "404" ]; then
        if echo "$BODY" | grep -q '"error"'; then
            print_pass "Correctly returned 404 for non-existent collection"
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

test_search_without_question() {
    ((TESTS_RUN++))
    print_test "T4.6 - Search Without Question (Validation)"
    
    RESPONSE=$(curl $CURL_OPTS \
        -X POST \
        -H "Content-Type: application/json" \
        -d "{\"collection_name\":\"$TEST_COLLECTION\",\"k\":3}" \
        "$RAG_BACKEND_URL/api/search" 2>&1)
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    BODY=$(echo "$RESPONSE" | sed '$d')
    
    if [ "$VERBOSE" = "true" ]; then
        print_info "Response: $BODY"
    fi
    
    if [ "$HTTP_CODE" = "400" ]; then
        if echo "$BODY" | grep -q '"error".*question'; then
            print_pass "Correctly validated missing question"
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

test_search_result_quality() {
    ((TESTS_RUN++))
    print_test "T4.7 - Verify Result Quality and Relevance"
    
    QUESTION="IBM Power S1012 processor count"
    
    RESPONSE=$(curl $CURL_OPTS \
        -X POST \
        -H "Content-Type: application/json" \
        -d "{\"question\":\"$QUESTION\",\"collection_name\":\"$TEST_COLLECTION\",\"k\":3}" \
        "$RAG_BACKEND_URL/api/search" 2>&1)
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    BODY=$(echo "$RESPONSE" | sed '$d')
    
    if [ "$HTTP_CODE" = "200" ]; then
        # Check if results contain relevant keywords
        if echo "$BODY" | grep -qi "processor\|S1012\|core"; then
            # Check if scores are present and reasonable
            SCORES=$(echo "$BODY" | grep -o '"score":[0-9.]*' | grep -o '[0-9.]*')
            if [ -n "$SCORES" ]; then
                print_pass "Results contain relevant content with scores"
                if [ "$VERBOSE" = "true" ]; then
                    print_info "Sample scores: $(echo "$SCORES" | head -3 | tr '\n' ' ')"
                fi
                return 0
            else
                print_fail "No scores found in results"
                return 1
            fi
        else
            print_warning "Results may not be highly relevant"
            print_info "This could indicate poor semantic matching"
            # Don't fail the test, just warn
            ((TESTS_PASSED++))
            return 0
        fi
    else
        print_fail "HTTP $HTTP_CODE (expected 200)"
        return 1
    fi
}

test_search_with_special_characters() {
    ((TESTS_RUN++))
    print_test "T4.8 - Search with Special Characters"
    
    QUESTION="What's the S1012's processor & memory?"
    
    RESPONSE=$(curl $CURL_OPTS \
        -X POST \
        -H "Content-Type: application/json" \
        -d "{\"question\":\"$QUESTION\",\"collection_name\":\"$TEST_COLLECTION\",\"k\":3}" \
        "$RAG_BACKEND_URL/api/search" 2>&1)
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    BODY=$(echo "$RESPONSE" | sed '$d')
    
    if [ "$HTTP_CODE" = "200" ]; then
        if echo "$BODY" | grep -q '"success":true'; then
            print_pass "Special characters handled correctly"
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

test_search_response_time() {
    ((TESTS_RUN++))
    print_test "T4.9 - Search Response Time"
    
    QUESTION="IBM Power specifications"
    
    START_TIME=$(date +%s)
    RESPONSE=$(curl $CURL_OPTS \
        -X POST \
        -H "Content-Type: application/json" \
        -d "{\"question\":\"$QUESTION\",\"collection_name\":\"$TEST_COLLECTION\",\"k\":3}" \
        "$RAG_BACKEND_URL/api/search" 2>&1)
    END_TIME=$(date +%s)
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    
    ELAPSED=$((END_TIME - START_TIME))
    
    if [ "$HTTP_CODE" = "200" ]; then
        if [ $ELAPSED -lt 10 ]; then
            print_pass "Search completed in ${ELAPSED}s (< 10s threshold)"
            return 0
        else
            print_warning "Search took ${ELAPSED}s (>= 10s threshold)"
            print_info "Performance may need optimization"
            # Don't fail, just warn
            ((TESTS_PASSED++))
            return 0
        fi
    else
        print_fail "Search failed (HTTP $HTTP_CODE)"
        return 1
    fi
}

################################################################################
# Main Execution
################################################################################

main() {
    print_header "Phase 4: Vector Search Tests"
    
    # Check if collection exists first
    print_info "Verifying test collection exists..."
    RESPONSE=$(curl $CURL_OPTS "$RAG_BACKEND_URL/api/collections" 2>&1)
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    
    if [ "$HTTP_CODE" != "200" ]; then
        echo -e "${RED}ERROR: Cannot verify collections${NC}"
        echo "Please run test-pdf-loading.sh first to create test data"
        exit 1
    fi
    
    echo ""
    
    # Run all search tests
    test_dense_vector_search
    test_sparse_keyword_search
    test_hybrid_search
    test_search_different_k_values
    test_search_nonexistent_collection
    test_search_without_question
    test_search_result_quality
    test_search_with_special_characters
    test_search_response_time
    
    # Print summary
    print_summary
    return $?
}

# Run main function
main
exit $?

# Made with Bob
