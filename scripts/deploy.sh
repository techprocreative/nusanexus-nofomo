#!/bin/bash
# NusaNexus NoFOMO Deployment Script
# Automates the deployment process for various environments

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="NusaNexus NoFOMO"
ENVIRONMENT=${1:-development}
SKIP_BUILD=${2:-false}
VERBOSE=${3:-false}

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_dependencies() {
    log_info "Checking dependencies..."
    
    # Check for required tools
    local tools=("git" "node" "npm" "python3" "pip")
    local missing_tools=()
    
    for tool in "${tools[@]}"; do
        if ! command -v $tool &> /dev/null; then
            missing_tools+=($tool)
        fi
    done
    
    if [ ${#missing_tools[@]} -ne 0 ]; then
        log_error "Missing required tools: ${missing_tools[*]}"
        log_info "Please install the missing tools and try again"
        exit 1
    fi
    
    log_success "All dependencies are available"
}

check_environment() {
    log_info "Checking environment configuration..."
    
    # Check if .env files exist
    if [ ! -f "backend/.env" ]; then
        log_warning "Backend .env file not found"
        if [ "$ENVIRONMENT" = "production" ]; then
            log_error "Production deployment requires backend/.env"
            exit 1
        else
            log_info "Creating template .env files..."
            cp backend/.env.example backend/.env 2>/dev/null || true
            cp frontend/.env.example frontend/.env.local 2>/dev/null || true
        fi
    fi
    
    if [ ! -f "frontend/.env.local" ] && [ "$ENVIRONMENT" != "production" ]; then
        log_info "Creating frontend environment file..."
        cp frontend/.env.example frontend/.env.local 2>/dev/null || true
    fi
}

setup_database() {
    log_info "Setting up database..."
    
    cd backend
    
    # Check if migrations exist
    if [ -d "migrations" ]; then
        if [ "$SKIP_BUILD" != "true" ]; then
            log_info "Installing Python dependencies..."
            pip install -r requirements.txt
        fi
        
        log_info "Running database setup..."
        if [ "$ENVIRONMENT" = "production" ]; then
            python scripts/setup_database.py --skip-verification
        else
            python scripts/setup_database.py
        fi
    else
        log_warning "No migration files found, skipping database setup"
    fi
    
    cd ..
}

build_frontend() {
    log_info "Building frontend..."
    
    cd frontend
    
    if [ "$SKIP_BUILD" != "true" ]; then
        log_info "Installing Node.js dependencies..."
        npm install
    fi
    
    if [ "$ENVIRONMENT" = "production" ]; then
        log_info "Building frontend for production..."
        npm run build
        log_success "Frontend built successfully"
    else
        log_info "Frontend development server will be started separately"
    fi
    
    cd ..
}

build_backend() {
    log_info "Building backend..."
    
    cd backend
    
    if [ "$SKIP_BUILD" != "true" ]; then
        log_info "Installing Python dependencies..."
        pip install -r requirements.txt
    fi
    
    log_success "Backend ready"
    cd ..
}

build_ai_engine() {
    log_info "Building AI engine..."
    
    cd ai_engine
    
    if [ "$SKIP_BUILD" != "true" ]; then
        log_info "Installing AI engine dependencies..."
        pip install -r requirements.txt
    fi
    
    log_success "AI engine ready"
    cd ..
}

build_bot_runner() {
    log_info "Building bot runner..."
    
    cd bot-runner
    
    if [ "$SKIP_BUILD" != "true" ]; then
        log_info "Installing bot runner dependencies..."
        pip install -r requirements.txt
        pip install freqtrade[talib] || log_warning "Failed to install freqtrade, continuing..."
    fi
    
    log_success "Bot runner ready"
    cd ..
}

run_tests() {
    if [ "$ENVIRONMENT" != "production" ]; then
        log_info "Running tests..."
        
        # Backend tests
        cd backend
        if [ -d "tests" ]; then
            python -m pytest tests/ -v || log_warning "Some tests failed"
        fi
        cd ..
        
        log_success "Tests completed"
    fi
}

docker_deploy() {
    log_info "Deploying with Docker..."
    
    if command -v docker &> /dev/null && command -v docker-compose &> /dev/null; then
        if [ "$ENVIRONMENT" = "production" ]; then
            docker-compose -f docker-compose.yml up -d --build
        else
            docker-compose -f docker-compose.yml up -d
        fi
        log_success "Docker deployment completed"
    else
        log_warning "Docker not available, skipping Docker deployment"
    fi
}

render_deploy_info() {
    log_info "Render deployment information:"
    echo "To deploy to Render, follow these steps:"
    echo "1. Connect your repository to Render.com"
    echo "2. Create services for:"
    echo "   - Frontend (Next.js) - Port 3000"
    echo "   - Backend (FastAPI) - Port 8000"
    echo "   - Bot Runner - Port 8001"
    echo "   - AI Engine - Port 8002"
    echo "   - Redis (managed service)"
    echo "3. Set environment variables in Render dashboard"
    echo "4. Deploy each service"
}

cloud_deploy_info() {
    log_info "Cloud deployment information:"
    echo "For cloud deployment (AWS/GCP/Azure):"
    echo "1. Build container images:"
    echo "   docker build -t nusanexus-frontend ./frontend"
    echo "   docker build -t nusanexus-backend ./backend"
    echo "   docker build -t nusanexus-bot-runner ./bot-runner"
    echo "   docker build -t nusanexus-ai ./ai_engine"
    echo "2. Push to container registry"
    echo "3. Deploy to your cloud platform"
}

show_post_deploy_info() {
    log_success "Deployment preparation completed!"
    echo ""
    echo "Next steps:"
    echo "1. Review and update environment variables"
    echo "2. Configure external services (Supabase, Tripay, etc.)"
    echo "3. Set up monitoring and logging"
    echo "4. Configure SSL/TLS certificates"
    echo "5. Set up backup procedures"
    echo ""
    echo "Environment: $ENVIRONMENT"
    echo "Skip build: $SKIP_BUILD"
    echo ""
    echo "For detailed deployment instructions, see:"
    echo "- docs/deployment.md"
    echo "- docs/environment-setup.md"
}

# Main deployment flow
main() {
    log_info "Starting deployment for $PROJECT_NAME"
    log_info "Environment: $ENVIRONMENT"
    echo ""
    
    # Check command line arguments
    if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
        echo "Usage: $0 [environment] [skip-build] [verbose]"
        echo ""
        echo "Environments: development, staging, production"
        echo "Options:"
        echo "  --skip-build    Skip dependency installation and building"
        echo "  --verbose       Show detailed output"
        echo "  --help, -h      Show this help message"
        echo ""
        echo "Examples:"
        echo "  $0 development"
        echo "  $0 production true"
        echo "  $0 staging false true"
        exit 0
    fi
    
    # Check dependencies
    check_dependencies
    
    # Check environment
    check_environment
    
    # Set up database
    if [ "$ENVIRONMENT" != "staging" ] || [ "$ENVIRONMENT" = "development" ]; then
        setup_database
    fi
    
    # Build components
    build_backend
    build_ai_engine
    build_bot_runner
    build_frontend
    
    # Run tests
    run_tests
    
    # Docker deployment (optional)
    if [ "$4" = "docker" ] || [ "$5" = "docker" ]; then
        docker_deploy
    else
        log_info "To deploy with Docker, run: $0 $ENVIRONMENT $SKIP_BUILD docker"
    fi
    
    # Show deployment information
    if [ "$ENVIRONMENT" = "production" ]; then
        render_deploy_info
        echo ""
        cloud_deploy_info
    fi
    
    # Show post-deployment information
    show_post_deploy_info
}

# Run main function
main "$@"
