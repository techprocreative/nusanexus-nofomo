#!/bin/bash

# NusaNexus NoFOMO - Deployment Configuration Testing Script
# This script validates all deployment configurations before production

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test functions
print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# Configuration files to check
CONFIG_FILES=(
    "render.yaml"
    "docker-compose.yml"
    ".env.development"
    ".env.staging"
    ".env.production"
    ".env.example"
    "backend/Dockerfile.production"
    "frontend/Dockerfile.production"
    "ai_engine/Dockerfile.production"
    "bot-runner/Dockerfile.production"
    "deployment/nginx/nginx.conf"
    "deployment/nginx/Dockerfile"
    "deployment/security/security-headers.conf"
    "deployment/security/rate-limiting.conf"
    "deployment/monitoring/prometheus/prometheus.yml"
    "deployment/monitoring/loki/loki-config.yml"
    "deployment/monitoring/promtail/promtail-config.yml"
    "deployment/database/supabase-config.sql"
    ".github/workflows/ci.yml"
)

# Test categories
test_config_files() {
    print_header "Testing Configuration Files"
    
    local failed=0
    for file in "${CONFIG_FILES[@]}"; do
        if [[ -f "$file" ]]; then
            print_success "Found: $file"
            
            # Test YAML files
            if [[ "$file" == *.yaml || "$file" == *.yml ]]; then
                if command -v yamllint &> /dev/null; then
                    if yamllint "$file" &> /dev/null; then
                        print_success "YAML validation passed: $file"
                    else
                        print_error "YAML validation failed: $file"
                        failed=$((failed + 1))
                    fi
                else
                    print_warning "yamllint not available, skipping YAML validation"
                fi
            fi
        else
            print_error "Missing configuration file: $file"
            failed=$((failed + 1))
        fi
    done
    
    return $failed
}

test_environment_files() {
    print_header "Testing Environment Configuration"
    
    local failed=0
    
    # Check required environment variables
    local required_vars=(
        "SECRET_KEY"
        "SUPABASE_URL"
        "SUPABASE_KEY"
        "OPENROUTER_API_KEY"
        "DATABASE_URL"
    )
    
    for env_file in ".env.development" ".env.staging" ".env.production"; do
        if [[ -f "$env_file" ]]; then
            print_info "Testing environment file: $env_file"
            
            # Check for placeholder values
            if grep -q "your-.*-key" "$env_file" 2>/dev/null; then
                print_error "Environment file contains placeholder values: $env_file"
                failed=$((failed + 1))
            else
                print_success "No placeholder values found: $env_file"
            fi
            
            # Check for required variables
            for var in "${required_vars[@]}"; do
                if grep -q "^$var=" "$env_file" 2>/dev/null; then
                    print_success "Found required variable: $var in $env_file"
                else
                    print_warning "Missing required variable: $var in $env_file"
                fi
            done
        else
            print_error "Environment file not found: $env_file"
            failed=$((failed + 1))
        fi
    done
    
    return $failed
}

test_dockerfiles() {
    print_header "Testing Docker Configuration"
    
    local failed=0
    
    # Test Dockerfiles
    local dockerfiles=(
        "backend/Dockerfile.production"
        "frontend/Dockerfile.production"
        "ai_engine/Dockerfile.production"
        "bot-runner/Dockerfile.production"
    )
    
    for dockerfile in "${dockerfiles[@]}"; do
        if [[ -f "$dockerfile" ]]; then
            print_success "Found Dockerfile: $dockerfile"
            
            # Check for security best practices
            if grep -q "USER.*app" "$dockerfile" 2>/dev/null; then
                print_success "Non-root user configured: $dockerfile"
            else
                print_warning "No non-root user found: $dockerfile"
            fi
            
            if grep -q "HEALTHCHECK" "$dockerfile" 2>/dev/null; then
                print_success "Health check configured: $dockerfile"
            else
                print_warning "No health check found: $dockerfile"
            fi
        else
            print_error "Dockerfile not found: $dockerfile"
            failed=$((failed + 1))
        fi
    done
    
    return $failed
}

test_nginx_config() {
    print_header "Testing Nginx Configuration"
    
    local failed=0
    
    local nginx_files=(
        "deployment/nginx/nginx.conf"
        "deployment/nginx/Dockerfile"
    )
    
    for file in "${nginx_files[@]}"; do
        if [[ -f "$file" ]]; then
            print_success "Found Nginx configuration: $file"
        else
            print_error "Nginx configuration missing: $file"
            failed=$((failed + 1))
        fi
    done
    
    # Test nginx configuration syntax if nginx is available
    if command -v nginx &> /dev/null; then
        if nginx -t -c "$(pwd)/deployment/nginx/nginx.conf" 2>/dev/null; then
            print_success "Nginx configuration syntax is valid"
        else
            print_error "Nginx configuration syntax is invalid"
            failed=$((failed + 1))
        fi
    else
        print_warning "Nginx not available for syntax testing"
    fi
    
    return $failed
}

test_security_config() {
    print_header "Testing Security Configuration"
    
    local failed=0
    
    # Test security headers
    if [[ -f "deployment/security/security-headers.conf" ]]; then
        print_success "Security headers configuration found"
        
        # Check for required security headers
        if grep -q "Content-Security-Policy" "deployment/security/security-headers.conf"; then
            print_success "CSP header configured"
        else
            print_error "CSP header missing"
            failed=$((failed + 1))
        fi
        
        if grep -q "X-Frame-Options" "deployment/security/security-headers.conf"; then
            print_success "X-Frame-Options header configured"
        else
            print_error "X-Frame-Options header missing"
            failed=$((failed + 1))
        fi
        
        if grep -q "Strict-Transport-Security" "deployment/security/security-headers.conf"; then
            print_success "HSTS header configured"
        else
            print_error "HSTS header missing"
            failed=$((failed + 1))
        fi
    else
        print_error "Security headers configuration missing"
        failed=$((failed + 1))
    fi
    
    # Test rate limiting
    if [[ -f "deployment/security/rate-limiting.conf" ]]; then
        print_success "Rate limiting configuration found"
    else
        print_error "Rate limiting configuration missing"
        failed=$((failed + 1))
    fi
    
    return $failed
}

test_monitoring_config() {
    print_header "Testing Monitoring Configuration"
    
    local failed=0
    
    local monitoring_files=(
        "deployment/monitoring/docker-compose.monitoring.yml"
        "deployment/monitoring/prometheus/prometheus.yml"
        "deployment/monitoring/loki/loki-config.yml"
        "deployment/monitoring/promtail/promtail-config.yml"
    )
    
    for file in "${monitoring_files[@]}"; do
        if [[ -f "$file" ]]; then
            print_success "Found monitoring configuration: $file"
        else
            print_error "Monitoring configuration missing: $file"
            failed=$((failed + 1))
        fi
    done
    
    return $failed
}

test_github_actions() {
    print_header "Testing GitHub Actions Configuration"
    
    local failed=0
    
    if [[ -f ".github/workflows/ci.yml" ]]; then
        print_success "GitHub Actions workflow found"
        
        # Check for required jobs
        if grep -q "test:" ".github/workflows/ci.yml"; then
            print_success "Test job configured"
        else
            print_error "Test job missing in GitHub Actions"
            failed=$((failed + 1))
        fi
        
        if grep -q "build:" ".github/workflows/ci.yml"; then
            print_success "Build job configured"
        else
            print_error "Build job missing in GitHub Actions"
            failed=$((failed + 1))
        fi
    else
        print_error "GitHub Actions workflow missing"
        failed=$((failed + 1))
    fi
    
    return $failed
}

test_render_config() {
    print_header "Testing Render Configuration"
    
    local failed=0
    
    if [[ -f "render.yaml" ]]; then
        print_success "Render configuration found"
        
        # Check for required services
        local services=(
            "nusafx-backend"
            "nusafx-frontend"
            "nusafx-ai-engine"
            "nusafx-bot-runner"
        )
        
        for service in "${services[@]}"; do
            if grep -q "$service" "render.yaml"; then
                print_success "Service configured: $service"
            else
                print_error "Service missing: $service"
                failed=$((failed + 1))
            fi
        done
    else
        print_error "Render configuration missing"
        failed=$((failed + 1))
    fi
    
    return $failed
}

test_database_config() {
    print_header "Testing Database Configuration"
    
    local failed=0
    
    if [[ -f "deployment/database/supabase-config.sql" ]]; then
        print_success "Database configuration found"
        
        # Check for required SQL features
        if grep -q "CREATE EXTENSION" "deployment/database/supabase-config.sql"; then
            print_success "Database extensions configured"
        else
            print_warning "No database extensions found"
        fi
        
        if grep -q "ROW LEVEL SECURITY" "deployment/database/supabase-config.sql" || grep -q "RLS" "deployment/database/supabase-config.sql"; then
            print_success "Row Level Security configured"
        else
            print_warning "No Row Level Security found"
        fi
    else
        print_error "Database configuration missing"
        failed=$((failed + 1))
    fi
    
    return $failed
}

run_connectivity_tests() {
    print_header "Testing Connectivity"
    
    # Test external services
    local services=(
        "https://api.openrouter.ai"
        "https://api.binance.com"
        "https://api.bybit.com"
    )
    
    for service in "${services[@]}"; do
        if curl -s --max-time 10 "$service" > /dev/null 2>&1; then
            print_success "Service accessible: $service"
        else
            print_warning "Service not accessible: $service"
        fi
    done
}

generate_test_report() {
    print_header "Generating Test Report"
    
    local total_tests=0
    local passed_tests=0
    local failed_tests=0
    
    # Count test results
    for test_file in /tmp/nusafx-test-*.log; do
        if [[ -f "$test_file" ]]; then
            local test_count=$(grep -c "✓" "$test_file" 2>/dev/null || echo 0)
            local fail_count=$(grep -c "✗" "$test_file" 2>/dev/null || echo 0)
            
            total_tests=$((total_tests + test_count + fail_count))
            passed_tests=$((passed_tests + test_count))
            failed_tests=$((failed_tests + fail_count))
        fi
    done
    
    echo -e "${BLUE}Test Summary:${NC}"
    echo "Total Tests: $total_tests"
    echo -e "${GREEN}Passed: $passed_tests${NC}"
    echo -e "${RED}Failed: $failed_tests${NC}"
    
    if [[ $failed_tests -eq 0 ]]; then
        print_success "All tests passed! Deployment configuration is ready for production."
        return 0
    else
        print_error "Some tests failed. Please review the configuration before deploying to production."
        return 1
    fi
}

# Main execution
main() {
    print_header "NusaNexus NoFOMO - Deployment Configuration Tests"
    print_info "Running comprehensive deployment configuration tests..."
    
    local total_failures=0
    
    # Run all tests
    test_config_files || total_failures=$((total_failures + $?))
    test_environment_files || total_failures=$((total_failures + $?))
    test_dockerfiles || total_failures=$((total_failures + $?))
    test_nginx_config || total_failures=$((total_failures + $?))
    test_security_config || total_failures=$((total_failures + $?))
    test_monitoring_config || total_failures=$((total_failures + $?))
    test_github_actions || total_failures=$((total_failures + $?))
    test_render_config || total_failures=$((total_failures + $?))
    test_database_config || total_failures=$((total_failures + $?))
    run_connectivity_tests
    
    # Generate final report
    if [[ $total_failures -eq 0 ]]; then
        print_success "All configuration tests passed!"
        generate_test_report
        exit 0
    else
        print_error "Configuration tests failed. Please review and fix issues."
        generate_test_report
        exit 1
    fi
}

# Run the tests
main "$@"
