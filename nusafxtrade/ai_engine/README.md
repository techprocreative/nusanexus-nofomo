# NusaNexus NoFOMO - AI Engine

A comprehensive AI-powered trading platform engine that integrates multiple LLM models for strategy generation, optimization, and intelligent trading automation.

## 🚀 Features

### Core AI Components

- **Strategy Generator** (`strategy_generator_enhanced.py`) - Generate trading strategies from natural language prompts
- **Parameter Optimizer** (`parameter_optimizer.py`) - AI-powered hyperparameter optimization
- **Market Analyzer** (`market_analyzer.py`) - Market trend analysis and predictions
- **AI Assistant** (`ai_assistant.py`) - Chat interface for trading insights
- **Supervisor Agent** (`supervisor_agent.py`) - Bot performance monitoring
- **Prompt Manager** (`prompt_manager.py`) - Template and context management
- **WebSocket Manager** (`websocket_manager.py`) - Real-time AI updates
- **Storage Manager** (`storage_manager.py`) - Supabase integration for data persistence

### Key Capabilities

- **Natural Language to Strategy** - Convert trading ideas into executable Freqtrade strategies
- **AI-Powered Optimization** - Bayesian, genetic, and guided optimization methods
- **Real-time Market Analysis** - Technical analysis with AI insights
- **Intelligent Chat Assistant** - Context-aware trading advice and education
- **Bot Supervision** - Performance monitoring and risk management
- **WebSocket Integration** - Real-time updates and notifications
- **Supabase Storage** - Secure data persistence and analytics
- **Multi-Model Support** - OpenRouter integration for multiple LLM models

## 🏗️ Architecture

```
AI Engine Core
├── Strategy Generator
│   ├── Natural Language Processing
│   ├── Strategy Template Engine
│   └── Code Generation
├── Parameter Optimizer
│   ├── Bayesian Optimization
│   ├── Genetic Algorithm
│   └── Grid Search
├── Market Analyzer
│   ├── Technical Indicators
│   ├── Sentiment Analysis
│   └── Price Predictions
├── AI Assistant
│   ├── Chat Interface
│   ├── Context Management
│   └── Trading Education
├── Supervisor Agent
│   ├── Performance Monitoring
│   ├── Risk Assessment
│   └── Bot Management
├── WebSocket Manager
│   ├── Real-time Updates
│   ├── Connection Management
│   └── Broadcasting
└── Storage Manager
    ├── Supabase Integration
    ├── Local File Storage
    └── Data Analytics
```

## 📦 Installation

### Prerequisites

- Python 3.8+
- FastAPI
- Supabase account (optional)
- OpenRouter API key

### Setup

1. **Install Dependencies**
```bash
pip install -r requirements.txt
```

2. **Environment Configuration**
```bash
# Copy environment template
cp .env.example .env

# Configure your settings
OPENROUTER_API_KEY=your_api_key_here
OPENROUTER_MODEL=anthropic/claude-3-sonnet
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_service_key
```

3. **AI Engine Setup**
```python
from nusafxtrade.ai_engine.ai_engine_core import get_ai_engine, EngineConfig
from nusafxtrade.ai_engine.storage_manager import get_storage_manager

# Initialize AI Engine
config = EngineConfig(
    max_concurrent_tasks=10,
    enable_supervisor=True,
    enable_realtime_monitoring=True
)

ai_engine = get_ai_engine(config)
await ai_engine.start()

# Initialize Storage
storage_manager = get_storage_manager()
```

## 🛠️ Usage Examples

### Strategy Generation

```python
from nusafxtrade.ai_engine.strategy_generator_enhanced import StrategyPrompt

# Create strategy prompt
prompt = StrategyPrompt(
    prompt="Create a momentum strategy using RSI and volume for swing trading",
    trading_pair="BTC/USDT",
    timeframe="4h",
    risk_level="medium",
    style="swing",
    max_parameters=15,
    strategy_complexity="medium",
    optimization_goals=["profit", "sharpe_ratio", "max_drawdown"]
)

# Generate strategy
result = await ai_engine.generate_strategy(
    user_id="user_123",
    prompt=prompt,
    optimize=True,
    backtest=True
)

print(f"Generated: {result['strategy']['strategy_name']}")
print(f"Confidence: {result['strategy']['confidence_score']}")
print(f"Parameters: {result['strategy']['parameters']}")
```

### Market Analysis

```python
from nusafxtrade.ai_engine.market_analyzer import AnalysisType, TimeHorizon

# Analyze market
analysis = await ai_engine.analyze_market(
    user_id="user_123",
    symbol="ETH/USDT",
    analysis_type="comprehensive",
    time_horizon="medium"
)

print(f"Analysis ID: {analysis['analysis_id']}")
print(f"Signals: {len(analysis['market_signals'])}")
print(f"Predictions: {analysis.get('predictions', {})}")
print(f"Confidence: {analysis['confidence_score']}")
```

### Parameter Optimization

```python
from nusafxtrade.ai_engine.parameter_optimizer import ParameterRange, OptimizationObjective

# Define parameter ranges
parameter_ranges = [
    ParameterRange(
        name="rsi_period",
        param_type="int",
        min_value=10,
        max_value=30,
        step=2
    ),
    ParameterRange(
        name="rsi_overbought",
        param_type="int", 
        min_value=60,
        max_value=80,
        step=2
    )
]

# Define optimization objectives
objectives = [
    OptimizationObjective(
        metric="sharpe_ratio",
        direction="maximize",
        weight=0.6
    ),
    OptimizationObjective(
        metric="max_drawdown",
        direction="minimize", 
        weight=0.4
    )
]

# Run optimization
result = await ai_engine.optimize_strategy(
    user_id="user_123",
    strategy_code=generated_strategy_code,
    parameters=strategy_parameters,
    objectives=["sharpe_ratio", "max_drawdown"],
    method="bayesian"
)

print(f"Best Score: {result['best_score']}")
print(f"Improvement: {result['improvement_percentage']}%")
print(f"Best Parameters: {result['best_parameters']}")
```

### AI Chat Assistant

```python
# Chat with AI assistant
response = await ai_engine.chat_with_ai(
    user_id="user_123",
    message="What are the best risk management practices for crypto trading?",
    context_type="risk",
    context_data={"portfolio_size": 10000, "risk_tolerance": "medium"}
)

print(f"Response: {response['content']}")
print(f"Suggestions: {response['suggestions']}")
print(f"Confidence: {response['confidence']}")
```

### Bot Supervision

```python
# Run bot supervision analysis
result = await ai_engine.supervise_bot(
    user_id="user_123",
    bot_id="bot_456",
    analysis_type="comprehensive"
)

print(f"Performance Score: {result['performance_score']}")
print(f"Recommendations: {result['recommendations']}")
print(f"Risk Assessment: {result['risk_assessment']}")
```

## 🌐 API Integration

### FastAPI Endpoints

The AI Engine provides RESTful API endpoints through FastAPI:

```python
# Enhanced AI API endpoints
from nusafxtrade.backend.app.api.v1.endpoints.ai_enhanced import router

# Include in FastAPI app
app.include_router(router, prefix="/api/v1/ai", tags=["ai"])
```

#### Available Endpoints

- `POST /generate-strategy` - Generate trading strategy
- `POST /optimize-strategy` - Optimize strategy parameters
- `POST /market-analysis` - Analyze market conditions
- `POST /chat` - Chat with AI assistant
- `POST /supervisor-analysis` - Supervise bot performance
- `GET /models-status` - Get AI models status
- `GET /task/{task_id}/status` - Get task status
- `GET /tasks` - List user tasks
- `GET /analyses` - List AI analyses
- `GET /analytics` - Get user analytics

### WebSocket Integration

```javascript
// Frontend WebSocket connection
const ws = new WebSocket('ws://localhost:8000/api/v1/ai/ws/ai?token=your_jwt_token');

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('AI Update:', data);
    
    switch (data.type) {
        case 'task_status':
            console.log('Task progress:', data.data.progress);
            break;
        case 'strategy_generation':
            console.log('Strategy update:', data.data);
            break;
        case 'market_analysis':
            console.log('Market signals:', data.data.market_signals);
            break;
    }
};

// Subscribe to updates
ws.send(JSON.stringify({
    type: 'subscribe',
    subscription_type: 'strategy_generation'
}));
```

## 🔧 Configuration

### Engine Configuration

```python
from nusafxtrade.ai_engine.ai_engine_core import EngineConfig

config = EngineConfig(
    max_concurrent_tasks=10,          # Maximum concurrent AI tasks
    default_model="anthropic/claude-3-sonnet",  # Default LLM model
    enable_caching=True,              # Enable response caching
    cache_ttl=3600,                   # Cache TTL in seconds
    max_retry_attempts=3,             # Maximum retry attempts
    timeout_seconds=300,              # Task timeout
    enable_supervisor=True,           # Enable bot supervision
    enable_realtime_monitoring=True,  # Enable real-time monitoring
    optimization_batch_size=5         # Optimization batch size
)
```

### Model Configuration

```python
# Configure different models for different tasks
MODEL_CONFIG = {
    "strategy_generation": {
        "model": "anthropic/claude-3-sonnet",
        "temperature": 0.7,
        "max_tokens": 4000
    },
    "market_analysis": {
        "model": "openai/gpt-4-turbo",
        "temperature": 0.3,
        "max_tokens": 2000
    },
    "chat_assistant": {
        "model": "anthropic/claude-3-haiku",
        "temperature": 0.8,
        "max_tokens": 1500
    }
}
```

### Storage Configuration

```python
# Supabase configuration
SUPABASE_CONFIG = {
    "url": os.getenv('SUPABASE_URL'),
    "service_key": os.getenv('SUPABASE_SERVICE_ROLE_KEY'),
    "tables": {
        "analyses": "ai_analyses",
        "strategies": "strategies", 
        "chat_sessions": "chat_sessions"
    }
}

# Local storage fallback
LOCAL_STORAGE = {
    "base_dir": "ai_storage",
    "cleanup_interval": 86400,  # 24 hours
    "max_file_size": 10 * 1024 * 1024  # 10MB
}
```

## 🧪 Testing

### Run Tests

```bash
# Run all tests
python -m pytest nusafxtrade/ai_engine/tests/ -v

# Run specific test
python -m pytest nusafxtrade/ai_engine/tests/test_ai_engine_integration.py::TestAIEngineIntegration::test_strategy_generation -v

# Run with coverage
python -m pytest nusafxtrade/ai_engine/tests/ --cov=nusafxtrade.ai_engine --cov-report=html
```

### Test Structure

```
tests/
├── test_ai_engine_integration.py    # Main integration tests
├── test_strategy_generator.py       # Strategy generator tests
├── test_parameter_optimizer.py      # Parameter optimizer tests
├── test_market_analyzer.py          # Market analyzer tests
├── test_ai_assistant.py             # AI assistant tests
├── test_supervisor_agent.py         # Supervisor agent tests
├── test_websocket_manager.py        # WebSocket tests
└── test_storage_manager.py          # Storage tests
```

## 📊 Monitoring and Analytics

### Engine Metrics

```python
# Get engine metrics
metrics = await ai_engine.get_engine_metrics()
print(f"Total tasks: {metrics.total_tasks}")
print(f"Success rate: {metrics.completed_tasks / metrics.total_tasks * 100:.1f}%")
print(f"Average response time: {metrics.average_response_time:.2f}s")
print(f"Tokens used today: {metrics.tokens_used_today}")
```

### Health Status

```python
# Get health status
health = await ai_engine.get_health_status()
print(f"Overall status: {health.status}")
print(f"Uptime: {health.uptime_seconds}s")
print(f"Component health: {health.component_health}")
print(f"Active tasks: {health.active_tasks}")
```

### User Analytics

```python
# Get user analytics
analytics = await storage_manager.get_user_metrics(
    user_id="user_123",
    days=30
)
print(f"Total analyses: {analytics.total_analyses}")
print(f"Analysis types: {analytics.analysis_types}")
print(f"Daily activity: {analytics.daily_activity}")
print(f"Estimated cost: ${analytics.cost_estimate:.2f}")
```

## 🛡️ Security Considerations

### API Key Management

- Store API keys in environment variables
- Use Supabase service role keys for backend operations
- Implement key rotation policies
- Monitor API usage and costs

### Data Privacy

- User data is encrypted in storage
- Implement GDPR compliance with data export/deletion
- Use Supabase Row Level Security (RLS)
- Log all data access for audit trails

### Rate Limiting

- Implement rate limits per user
- Monitor token usage
- Set cost limits and alerts
- Use model selection for cost optimization

## 🚀 Deployment

### Docker Deployment

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Variables

```bash
# Required
OPENROUTER_API_KEY=your_key
OPENROUTER_MODEL=anthropic/claude-3-sonnet

# Optional
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_key
REDIS_URL=redis://localhost:6379

# AI Engine
AI_ENGINE_MAX_TASKS=10
AI_ENGINE_TIMEOUT=300
AI_ENGINE_CACHE_TTL=3600
```

### Production Considerations

- Use production-grade OpenRouter models
- Implement proper logging and monitoring
- Set up automated backups
- Configure health checks and alerts
- Use load balancing for high availability
- Implement proper error handling and retries

## 📚 Advanced Features

### Custom Templates

```python
# Create custom strategy template
custom_template = """
class {{ class_name }}(IStrategy):
    # Custom strategy implementation
    # with your specific requirements
"""

# Use in strategy generation
result = await strategy_generator.generate_with_template(
    prompt=prompt,
    template=custom_template,
    custom_functions=["custom_indicator", "advanced_exit"]
)
```

### Custom Optimization Algorithms

```python
# Implement custom optimization
class CustomOptimizer:
    async def optimize(self, parameters, objectives, data):
        # Your custom optimization logic
        return optimized_parameters

# Register with engine
ai_engine.parameter_optimizer.register_algorithm(
    name="custom_ga",
    optimizer=CustomOptimizer()
)
```

### Real-time Notifications

```python
# Set up real-time notifications
from nusafxtrade.ai_engine.websocket_manager import AIWebSocketBroadcaster

broadcaster = AIWebSocketBroadcaster(connection_manager)

# Send custom notification
await broadcaster.broadcast_alert(
    user_id="user_123",
    alert_id="risk_warning",
    level="high",
    title="High Drawdown Detected",
    message="Your bot has reached 15% drawdown",
    data={"bot_id": "bot_456", "drawdown": 0.15}
)
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

### Development Setup

```bash
# Clone repository
git clone https://github.com/your-org/nusafxtrade.git
cd nusafxtrade/ai_engine

# Install development dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run tests
python -m pytest

# Run linting
black .
flake8 .
mypy .
```

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support and questions:

- Create an issue on GitHub
- Check the documentation
- Review the API examples
- Join our community Discord

## 🔄 Changelog

### v1.0.0 (Current)
- Initial AI Engine release
- Strategy generation and optimization
- Market analysis and predictions
- AI chat assistant
- Bot supervision
- WebSocket real-time updates
- Supabase integration
- Comprehensive testing suite

---

**Built with ❤️ for the crypto trading community**
