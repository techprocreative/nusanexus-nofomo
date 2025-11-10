"""
NusaNexus NoFOMO - AI Prompt Manager
Template and context management for AI engine
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel
from jinja2 import Template, Environment, BaseLoader
import structlog
from pathlib import Path
from enum import Enum

# Configure logging
logger = structlog.get_logger(__name__)


class PromptType(str, Enum):
    STRATEGY_GENERATION = "strategy_generation"
    PARAMETER_OPTIMIZATION = "parameter_optimization"
    MARKET_ANALYSIS = "market_analysis"
    PERFORMANCE_ANALYSIS = "performance_analysis"
    RISK_ASSESSMENT = "risk_assessment"
    CHAT_GENERAL = "chat_general"
    CHAT_STRATEGY = "chat_strategy"
    CHAT_MARKET = "chat_market"
    CHAT_RISK = "chat_risk"
    CHAT_EDUCATION = "chat_education"
    BACKTEST_ANALYSIS = "backtest_analysis"
    SENTIMENT_ANALYSIS = "sentiment_analysis"


class TemplateVariable(BaseModel):
    """Template variable definition"""
    name: str
    type: str  # "string", "number", "boolean", "list", "dict"
    required: bool = True
    default: Any = None
    description: str = ""
    validation: Optional[str] = None  # regex or validation function


class PromptTemplate(BaseModel):
    """Prompt template definition"""
    template_id: str
    name: str
    prompt_type: PromptType
    system_prompt: str
    user_prompt: str
    variables: List[TemplateVariable] = []
    model_config: Dict[str, Any] = {}
    metadata: Dict[str, Any] = {}
    created_at: datetime
    updated_at: datetime
    version: str = "1.0.0"
    is_active: bool = True


class PromptContext(BaseModel):
    """Context for prompt rendering"""
    user_id: str
    session_id: Optional[str] = None
    variables: Dict[str, Any] = {}
    history: List[Dict[str, Any]] = []
    metadata: Dict[str, Any] = {}


class RenderedPrompt(BaseModel):
    """Rendered prompt result"""
    template_id: str
    system_prompt: str
    user_prompt: str
    rendered_system: str
    rendered_user: str
    model_config: Dict[str, Any]
    variables_used: List[str]
    render_time: datetime
    success: bool = True
    error_message: Optional[str] = None


class PromptManager:
    """
    Centralized prompt and template management system
    """
    
    def __init__(self):
        self.templates_dir = Path('prompt_templates')
        self.templates_dir.mkdir(exist_ok=True)
        
        # Template cache needs to exist before loading anything
        self.template_cache: Dict[str, PromptTemplate] = {}
        
        # Initialize Jinja2 environment
        self.jinja_env = Environment(loader=BaseLoader())
        
        # Load built-in templates
        self._load_builtin_templates()
        
        # Load custom templates
        self._load_custom_templates()
        
    def _load_builtin_templates(self):
        """
        Load built-in prompt templates
        """
        # Strategy Generation Templates
        self._register_template(PromptTemplate(
            template_id="strategy_generation_basic",
            name="Basic Strategy Generation",
            prompt_type=PromptType.STRATEGY_GENERATION,
            system_prompt="""
            Anda adalah ahli trading algoritma dan Freqtrade strategy development.
            Buat strategi trading Python untuk Freqtrade berdasarkan permintaan user.
            
            Guidelines:
            1. Gunakan only built-in indicators yang tersedia di Freqtrade
            2. Hindari external dependencies yang tidak ada di Freqtrade
            3. Include proper error handling dan edge cases
            4. Follow Freqtrade strategy development best practices
            5. Set reasonable ROI dan stoploss values
            6. Return complete Python strategy code
            7. Include comprehensive comments dalam Bahasa Indonesia
            
            Format response dengan:
            - strategy_name: <nama strategy>
            - description: <deskripsi strategy>
            - parameters: <dict parameter dan default values>
            - indicators: <list indicator yang akan digunakan>
            - buy_conditions: <list conditions untuk buy signal>
            - sell_conditions: <list conditions untuk sell signal>
            """,
            user_prompt="""
            Buat Freqtrade strategy dengan detail berikut:
            - Request: {{ request }}
            - Trading Pair: {{ trading_pair }}
            - Timeframe: {{ timeframe }}
            - Risk Level: {{ risk_level }}
            - Trading Style: {{ style }}
            
            Gunakan timeframe {{ timeframe }} dan fokuskan pada {{ style }} trading dengan risk level {{ risk_level }}.
            """,
            variables=[
                TemplateVariable(name="request", type="string", required=True, description="User's strategy request"),
                TemplateVariable(name="trading_pair", type="string", required=True, description="Trading pair symbol"),
                TemplateVariable(name="timeframe", type="string", required=True, description="Candlestick timeframe"),
                TemplateVariable(name="risk_level", type="string", required=True, description="Risk tolerance level"),
                TemplateVariable(name="style", type="string", required=True, description="Trading style")
            ],
            model_config={"temperature": 0.7, "max_tokens": 4000},
            created_at=datetime.now(),
            updated_at=datetime.now()
        ))
        
        # Parameter Optimization Templates
        self._register_template(PromptTemplate(
            template_id="parameter_optimization",
            name="Parameter Optimization Analysis",
            prompt_type=PromptType.PARAMETER_OPTIMIZATION,
            system_prompt="""
            Anda adalah ahli optimasi parameter trading dan machine learning.
            Analisis strategi Freqtrade dan berikan saran untuk optimasi parameter.
            
            Guidelines:
            1. Analisis sensitivitas parameter terhadap performa
            2. Identifikasi parameter yang paling влияют на результат
            3. Sarankan range optimal berdasarkan strategy logic
            4. Berikan insight tentang interaksi antar parameter
            5. Pertimbangkan multi-objective optimization
            """,
            user_prompt="""
            Analisis strategi berikut untuk optimasi parameter:
            
            Strategy Code:
            ```
            {{ strategy_code }}
            ```
            
            Parameter Ranges:
            {{ parameter_ranges }}
            
            Objectives:
            {{ objectives }}
            
            Berikan analisis dalam format:
            - key_parameters: [list parameter kunci]
            - recommended_ranges: {parameter_name: {min, max}}
            - parameter_interactions: [insight tentang interaksi]
            - optimization_suggestions: [saran optimasi]
            """,
            variables=[
                TemplateVariable(name="strategy_code", type="string", required=True, description="Strategy Python code"),
                TemplateVariable(name="parameter_ranges", type="string", required=True, description="Parameter ranges in JSON"),
                TemplateVariable(name="objectives", type="string", required=True, description="Optimization objectives")
            ],
            model_config={"temperature": 0.3, "max_tokens": 2000},
            created_at=datetime.now(),
            updated_at=datetime.now()
        ))
        
        # Market Analysis Templates
        self._register_template(PromptTemplate(
            template_id="market_analysis",
            name="Market Analysis",
            prompt_type=PromptType.MARKET_ANALYSIS,
            system_prompt="""
            Anda adalah ahli analisis pasar cryptocurrency dan trading.
            Analisis data pasar dan berikan insight yang actionable.
            
            Guidelines:
            1. Gunakan analisis teknikal dan fundamental
            2. Berikan reasoning yang jelas untuk setiap insight
            3. Fokus pada time horizon {{ time_horizon }}
            4. Berikan confidence level untuk setiap prediksi
            5. Berikan risk assessment
            6. Gunakan format yang structured
            """,
            user_prompt="""
            Analisis pasar {{ symbol }} berdasarkan data berikut:
            
            Current Price: {{ current_price }}
            Price Change: {{ price_change_pct }}%
            
            Technical Indicators:
            - RSI: {{ rsi }}
            - MACD: {{ macd }}
            - MACD Signal: {{ macd_signal }}
            - Bollinger Bands Position: {{ bb_position }}
            - Stochastic K: {{ stoch_k }}
            - ADX: {{ adx }}
            - Volume Ratio: {{ volume_ratio }}
            - Volatility: {{ volatility }}
            - Price Position (52w): {{ price_position }}
            
            Analysis Type: {{ analysis_type }}
            Time Horizon: {{ time_horizon }}
            
            Berikan analisis dalam format JSON:
            {{
                "trend_analysis": {{
                    "direction": "bullish|bearish|sideways",
                    "strength": 0.0-1.0,
                    "reasoning": "penjelasan trend"
                }},
                "key_signals": [
                    {{
                        "signal": "buy|sell|hold",
                        "strength": 0.0-1.0,
                        "indicator": "nama indikator",
                        "reasoning": "penjelasan signal"
                    }}
                ],
                "price_targets": {{
                    "support": [harga support],
                    "resistance": [harga resistance],
                    "entry": "harga entry",
                    "tp1": "target profit 1",
                    "tp2": "target profit 2",
                    "sl": "stop loss"
                }},
                "market_outlook": {{
                    "next_1h": "bullish|bearish|sideways",
                    "next_4h": "bullish|bearish|sideways", 
                    "next_1d": "bullish|bearish|sideways",
                    "confidence": 0.0-1.0
                }},
                "risk_assessment": {{
                    "risk_level": "low|medium|high",
                    "volatility_outlook": "description",
                    "key_risks": ["list risiko"]
                }},
                "insights": ["list insight penting"],
                "confidence": 0.0-1.0
            }}
            """,
            variables=[
                TemplateVariable(name="symbol", type="string", required=True, description="Trading symbol"),
                TemplateVariable(name="current_price", type="number", required=True, description="Current price"),
                TemplateVariable(name="price_change_pct", type="number", required=True, description="Price change percentage"),
                TemplateVariable(name="rsi", type="number", required=True, description="RSI indicator value"),
                TemplateVariable(name="macd", type="number", required=True, description="MACD value"),
                TemplateVariable(name="macd_signal", type="number", required=True, description="MACD signal value"),
                TemplateVariable(name="bb_position", type="number", required=True, description="Bollinger Bands position"),
                TemplateVariable(name="stoch_k", type="number", required=True, description="Stochastic K value"),
                TemplateVariable(name="adx", type="number", required=True, description="ADX value"),
                TemplateVariable(name="volume_ratio", type="number", required=True, description="Volume ratio"),
                TemplateVariable(name="volatility", type="number", required=True, description="Volatility measure"),
                TemplateVariable(name="price_position", type="number", required=True, description="Price position in 52w range"),
                TemplateVariable(name="analysis_type", type="string", required=True, description="Type of analysis"),
                TemplateVariable(name="time_horizon", type="string", required=True, description="Time horizon for analysis")
            ],
            model_config={"temperature": 0.3, "max_tokens": 2000},
            created_at=datetime.now(),
            updated_at=datetime.now()
        ))
        
        # Chat Templates
        chat_templates = [
            (PromptType.CHAT_GENERAL, "General Chat", """
                Anda adalah NusaNexus NoFOMO AI Assistant - penasihat trading yang ahli dan ramah.
                
                Peran Anda:
                - Memberikan advice trading yang objektif dan balanced
                - Menjawab pertanyaan tentang strategi, risk management, dan market analysis
                - Membantu user memahami konsep trading yang kompleks
                - Memberikan insights berdasarkan data dan analysis
                
                Guidelines:
                - Selalu berikan disclaimer bahwa ini bukan financial advice
                - Fokus pada risk management dan education
                - Gunakan bahasa Indonesia yang mudah dipahami
                - Berikan examples konkret ketika memungkinkan
                - Jika tidak yakin, akui keterbatasan Anda
                
                Gaya komunikasi:
                - Profesional tapi friendly
                - Jelas dan structured
                - Educational
                - Supportive dan encouraging
            """),
            (PromptType.CHAT_STRATEGY, "Strategy Discussion", """
                Anda adalah ahli strategi trading dengan expertise dalam:
                - Technical analysis dan indicator interpretation
                - Strategy development dan optimization
                - Backtesting dan performance analysis
                - Risk management dalam strategy design
                
                Fokus pada:
                - Strategy logic dan reasoning
                - Parameter optimization
                - Market condition adaptation
                - Performance metrics interpretation
                - Strategy validation dan testing
                
                Selalu pertimbangkan:
                - Market conditions dan timeframes
                - Risk-reward ratios
                - Strategy complexity vs. effectiveness
                - Backtest limitations
            """),
            (PromptType.CHAT_RISK, "Risk Management", """
                Anda adalah risk management expert dengan fokus pada:
                - Position sizing calculations
                - Stop-loss dan take-profit strategies
                - Portfolio diversification
                - Risk-reward optimization
                - Drawdown management
                
                Prinsip:
                - Risk first, profit second
                - Never risk more than you can afford to lose
                - Diversification is key
                - Position sizing is crucial
                - Emotional control in trading
                
                Selalu rekomendasi:
                - Specific position sizes
                - Clear stop-loss levels
                - Risk-reward ratios
                - Multiple exit strategies
                - Emergency protocols
            """)
        ]
        
        for prompt_type, name, system_prompt in chat_templates:
            self._register_template(PromptTemplate(
                template_id=f"chat_{prompt_type.value}",
                name=name,
                prompt_type=prompt_type,
                system_prompt=system_prompt,
                user_prompt="{{ message }}",
                variables=[
                    TemplateVariable(name="message", type="string", required=True, description="User message")
                ],
                model_config={"temperature": 0.7, "max_tokens": 1500},
                created_at=datetime.now(),
                updated_at=datetime.now()
            ))
        
        logger.info(f"Loaded {len(self.template_cache)} built-in templates")
    
    def _load_custom_templates(self):
        """
        Load custom templates from file system
        """
        try:
            templates_file = self.templates_dir / "custom_templates.json"
            if templates_file.exists():
                with open(templates_file, 'r') as f:
                    custom_templates = json.load(f)
                
                for template_data in custom_templates:
                    template = PromptTemplate(**template_data)
                    self._register_template(template)
                
                logger.info(f"Loaded {len(custom_templates)} custom templates")
        except Exception as e:
            logger.warning(f"Failed to load custom templates: {str(e)}")
    
    def _register_template(self, template: PromptTemplate):
        """
        Register a prompt template
        """
        self.template_cache[template.template_id] = template
    
    async def render_prompt(
        self,
        template_id: str,
        context: PromptContext,
        additional_variables: Optional[Dict[str, Any]] = None
    ) -> RenderedPrompt:
        """
        Render a prompt template with context
        """
        try:
            # Get template
            template = self.template_cache.get(template_id)
            if not template:
                raise ValueError(f"Template {template_id} not found")
            
            if not template.is_active:
                raise ValueError(f"Template {template_id} is not active")
            
            # Combine variables
            variables = {**context.variables}
            if additional_variables:
                variables.update(additional_variables)
            
            # Validate required variables
            self._validate_variables(template, variables)
            
            # Create Jinja templates
            system_template = Template(template.system_prompt)
            user_template = Template(template.user_prompt)
            
            # Render prompts
            rendered_system = system_template.render(**variables)
            rendered_user = user_template.render(**variables)
            
            # Track variables used
            variables_used = []
            for var in template.variables:
                if var.name in variables:
                    variables_used.append(var.name)
            
            return RenderedPrompt(
                template_id=template_id,
                system_prompt=template.system_prompt,
                user_prompt=template.user_prompt,
                rendered_system=rendered_system,
                rendered_user=rendered_user,
                model_config=template.model_config,
                variables_used=variables_used,
                render_time=datetime.now(),
                success=True
            )
            
        except Exception as e:
            logger.error(f"Failed to render prompt {template_id}: {str(e)}")
            return RenderedPrompt(
                template_id=template_id,
                system_prompt="",
                user_prompt="",
                rendered_system="",
                rendered_user="",
                model_config={},
                variables_used=[],
                render_time=datetime.now(),
                success=False,
                error_message=str(e)
            )
    
    def _validate_variables(self, template: PromptTemplate, variables: Dict[str, Any]):
        """
        Validate template variables
        """
        for var_def in template.variables:
            if var_def.required and var_def.name not in variables:
                raise ValueError(f"Required variable '{var_def.name}' not provided")
            
            if var_def.name in variables:
                value = variables[var_def.name]
                
                # Type validation
                if var_def.type == "string" and not isinstance(value, str):
                    raise ValueError(f"Variable '{var_def.name}' must be a string")
                elif var_def.type == "number" and not isinstance(value, (int, float)):
                    raise ValueError(f"Variable '{var_def.name}' must be a number")
                elif var_def.type == "boolean" and not isinstance(value, bool):
                    raise ValueError(f"Variable '{var_def.name}' must be a boolean")
                elif var_def.type == "list" and not isinstance(value, list):
                    raise ValueError(f"Variable '{var_def.name}' must be a list")
                elif var_def.type == "dict" and not isinstance(value, dict):
                    raise ValueError(f"Variable '{var_def.name}' must be a dict")
                
                # Default value handling
                if value is None and var_def.default is not None:
                    variables[var_def.name] = var_def.default
                
                # Validation pattern
                if var_def.validation and isinstance(value, str):
                    import re
                    if not re.match(var_def.validation, value):
                        raise ValueError(f"Variable '{var_def.name}' does not match validation pattern")
    
    def get_template(self, template_id: str) -> Optional[PromptTemplate]:
        """
        Get a template by ID
        """
        return self.template_cache.get(template_id)
    
    def list_templates(
        self,
        prompt_type: Optional[PromptType] = None,
        active_only: bool = True
    ) -> List[PromptTemplate]:
        """
        List all templates
        """
        templates = list(self.template_cache.values())
        
        if prompt_type:
            templates = [t for t in templates if t.prompt_type == prompt_type]
        
        if active_only:
            templates = [t for t in templates if t.is_active]
        
        return sorted(templates, key=lambda x: (x.prompt_type.value, x.name))
    
    def create_template(
        self,
        name: str,
        prompt_type: PromptType,
        system_prompt: str,
        user_prompt: str,
        variables: Optional[List[TemplateVariable]] = None,
        model_config: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> PromptTemplate:
        """
        Create a new template
        """
        template_id = f"custom_{prompt_type.value}_{len(self.template_cache)}"
        
        template = PromptTemplate(
            template_id=template_id,
            name=name,
            prompt_type=prompt_type,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            variables=variables or [],
            model_config=model_config or {},
            metadata=metadata or {},
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        self._register_template(template)
        
        # Save to custom templates file
        self._save_custom_templates()
        
        return template
    
    def update_template(
        self,
        template_id: str,
        **updates
    ) -> Optional[PromptTemplate]:
        """
        Update an existing template
        """
        if template_id not in self.template_cache:
            return None
        
        template = self.template_cache[template_id]
        
        # Update fields
        for field, value in updates.items():
            if hasattr(template, field):
                setattr(template, field, value)
        
        template.updated_at = datetime.now()
        
        # Save if it's a custom template
        if template_id.startswith("custom_"):
            self._save_custom_templates()
        
        return template
    
    def delete_template(self, template_id: str) -> bool:
        """
        Delete a template (only custom templates)
        """
        if template_id not in self.template_cache:
            return False
        
        if not template_id.startswith("custom_"):
            raise ValueError("Cannot delete built-in templates")
        
        del self.template_cache[template_id]
        self._save_custom_templates()
        
        return True
    
    def _save_custom_templates(self):
        """
        Save custom templates to file
        """
        try:
            custom_templates = []
            for template in self.template_cache.values():
                if template.template_id.startswith("custom_"):
                    custom_templates.append(template.model_dump())
            
            templates_file = self.templates_dir / "custom_templates.json"
            with open(templates_file, 'w') as f:
                json.dump(custom_templates, f, indent=2, default=str)
                
        except Exception as e:
            logger.error(f"Failed to save custom templates: {str(e)}")
    
    def get_template_variables(self, template_id: str) -> List[TemplateVariable]:
        """
        Get template variables
        """
        template = self.get_template(template_id)
        return template.variables if template else []
    
    def create_context(
        self,
        user_id: str,
        session_id: Optional[str] = None,
        **kwargs
    ) -> PromptContext:
        """
        Create a new context
        """
        return PromptContext(
            user_id=user_id,
            session_id=session_id,
            variables=kwargs.get('variables', {}),
            history=kwargs.get('history', []),
            metadata=kwargs.get('metadata', {})
        )
    
    def add_context_variable(self, context: PromptContext, name: str, value: Any):
        """
        Add a variable to context
        """
        context.variables[name] = value
    
    def add_context_history(self, context: PromptContext, entry: Dict[str, Any]):
        """
        Add an entry to context history
        """
        context.history.append(entry)
        
        # Limit history size
        if len(context.history) > 50:
            context.history = context.history[-50:]
    
    def get_templates_by_type(self, prompt_type: PromptType) -> List[PromptTemplate]:
        """
        Get all templates of a specific type
        """
        return [t for t in self.template_cache.values() if t.prompt_type == prompt_type and t.is_active]


def main():
    """
    Test function for prompt manager
    """
    import asyncio
    
    async def test_prompt_manager():
        manager = PromptManager()
        
        # List all templates
        templates = manager.list_templates()
        print(f"Available templates: {len(templates)}")
        
        # Test template rendering
        context = manager.create_context(
            user_id="test_user",
            request="Create a RSI-based strategy",
            trading_pair="BTC/USDT",
            timeframe="1h",
            risk_level="medium",
            style="swing"
        )
        
        rendered = await manager.render_prompt("strategy_generation_basic", context)
        print(f"Rendered successfully: {rendered.success}")
        if rendered.success:
            print(f"System prompt: {rendered.rendered_system[:200]}...")
            print(f"User prompt: {rendered.rendered_user[:200]}...")
    
    asyncio.run(test_prompt_manager())


if __name__ == "__main__":
    main()
