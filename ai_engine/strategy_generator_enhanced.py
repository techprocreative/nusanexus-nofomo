"""
NusaNexus NoFOMO - Enhanced AI Strategy Generator
Advanced strategy generation with Prompt Manager integration
"""

import os
import asyncio
from typing import Dict, Any, Optional, List
from openai import OpenAI
from pydantic import BaseModel
from datetime import datetime
from pathlib import Path
import json
import structlog
import re
from jinja2 import Template

# Import our components
from .prompt_manager import PromptManager
from .parameter_optimizer import ParameterRange, OptimizationObjective

# Configure logging
logger = structlog.get_logger(__name__)


class StrategyPrompt(BaseModel):
    prompt: str
    trading_pair: str
    timeframe: str
    risk_level: str
    style: str
    max_parameters: int = 10
    include_indicators: List[str] = []
    exclude_indicators: List[str] = []
    strategy_complexity: str = "medium"  # simple, medium, complex
    backtest_period: int = 90  # days
    optimization_goals: List[str] = ["profit", "win_rate", "sharpe_ratio"]


class StrategyTemplate:
    """
    Enhanced template for Freqtrade strategy generation
    """
    STRATEGY_TEMPLATE = '''
# NusaNexus NoFOMO - AI Generated Strategy
# Generated on {{ generated_at }}
# Prompt: {{ prompt }}

from freqtrade.strategy.interface import IStrategy
from freqtrade.strategy import merge_informative_pair
from freqtrade.exchange import timeframe_to_seconds
from freqtrade.strategy import CategoricalParameter, DecimalParameter, IntParameter

import pandas as pd
import numpy as np
import ta
from functools import reduce

class {{ class_name }}(IStrategy):
    """
    {{ description }}
    
    AI-Generated Strategy for {{ trading_pair }}
    Risk Level: {{ risk_level }}
    Timeframe: {{ timeframe }}
    
    Strategy Parameters:
    {% for param, config in parameters.items() -%}
    - {{ param }}: {{ config.get('description', 'Strategy parameter') }} (default: {{ config.get('default', 'N/A') }})
    {% endfor -%}
    """
    
    # Strategy metadata
    INTERFACE_VERSION = 3
    
    # ROI table - AI optimized
    minimal_roi = {
        "0": 0.10,
        "20": 0.05,
        "40": 0.03,
        "60": 0.02,
        "120": 0.01,
        "180": 0,
        "240": -0.01,
        "300": -0.02,
        "360": -0.03,
        "420": -0.05,
        "480": -0.10,
        "540": -0.15
    }
    
    # Stoploss - Risk adaptive
    stoploss = {{ stop_loss|default(-0.02) }}
    
    # Trailing stop
    trailing_stop = {{ trailing_stop|default(True) }}
    trailing_stop_positive = {{ trailing_positive|default(0.01) }}
    trailing_stop_positive_offset = {{ trailing_offset|default(0.02) }}
    trailing_only_offset_is_reached = {{ trailing_only|default(True) }}
    
    # Timeframe
    timeframe = "{{ timeframe }}"
    timeframe_min = timeframe_to_seconds(timeframe)
    
    # Process only the last 200 candles
    process_only_new_candles = True
    startup_candle_count = {{ startup_candles|default(200) }}
    
    # Informative pairs
    informative_pairs = [
        # Add informative pairs based on strategy needs
    ]
    
    # Multi-pair strategy
    can_short = {{ can_short|default(False) }}
    
    {% if parameters %}
    # AI-Generated Strategy Parameters
    {% for param, config in parameters.items() -%}
    {{ param }} = {{ config.get('param_class', 'IntParameter') }}(
        {% if config.get('default') is not none -%}
        default={{ config.get('default') }},
        {%- endif -%}
        {% if config.get('low') is not none -%}
        low={{ config.get('low') }},
        {%- endif -%}
        {% if config.get('high') is not none -%}
        high={{ config.get('high') }},
        {%- endif -%}
        {% if config.get('step') is not none -%}
        step={{ config.get('step') }},
        {%- endif -%}
        {% if config.get('space') -%}
        space="{{ config.get('space') }}",
        {%- endif -%}
        {% if config.get('category') -%}
        category="{{ config.get('category') }}",
        {%- endif -%}
        optimize=True
    )
    {% endfor -%}
    {% endif %}
    
    def informative_pairs(self):
        """
        Define additional informative pairs
        """
        return self.informative_pairs
    
    def populate_indicators(self, dataframe, metadata):
        """
        Populate indicators for the strategy
        {% for indicator in indicators %}
        # {{ indicator.name }}
        {{ indicator.code }}
        {% endfor %}
        """
        
        {% for indicator in indicators %}
        try:
            {{ indicator.code }}
        except Exception as e:
            logger.warning(f"Failed to calculate {{ indicator.name }}: {e}")
        {% endfor %}
        
        return dataframe
    
    def populate_buy_trend(self, dataframe, metadata):
        """
        Define buy conditions
        """
        dataframe.loc[
            ({% for condition in buy_conditions -%}
            ({{ condition }}){% if not loop.last %} & {% endif -%}
            {% endfor %}),
            'buy'
        ] = 1
        
        return dataframe
    
    def populate_sell_trend(self, dataframe, metadata):
        """
        Define sell conditions
        """
        dataframe.loc[
            ({% for condition in sell_conditions -%}
            ({{ condition }}){% if not loop.last %} & {% endif -%}
            {% endfor %}),
            'sell'
        ] = 1
        
        return dataframe
    
    def check_buy_timeout(self, pair, trade, **kwargs) -> bool:
        """
        Timeout buy orders
        """
        return False
    
    def check_sell_timeout(self, pair, trade, **kwargs) -> bool:
        """
        Timeout sell orders
        """
        return False
    
    def bot_start(self, **kwargs) -> None:
        """
        Strategy initialization
        """
        logger.info(f"Starting {{ class_name }} strategy")
        logger.info(f"Trading pair: {{ trading_pair }}")
        logger.info(f"Risk level: {{ risk_level }}")
    
    def bot_loop_start(self, **kwargs) -> None:
        """
        Called at the start of every iteration
        """
        pass
    
    def custom_stake_amount(
        self, pair: str, current_time: datetime, current_rate: float,
        proposed_stake: float, min_stake: float, max_stake: float,
        **kwargs
    ) -> float:
        """
        Custom stake amount calculation
        """
        return proposed_stake
    
    def confirm_trade_entry(
        self, pair: str, order_type: str, amount: float, rate: float,
        time_in_force: str, current_time: datetime, **kwargs
    ) -> bool:
        """
        Confirm trade entry
        """
        return True
    
    def confirm_trade_exit(
        self, pair: str, trade, order_type: str, amount: float,
        rate: float, time_in_force: str, exit_reason: str, **kwargs
    ) -> bool:
        """
        Confirm trade exit
        """
        return True
'''


class EnhancedAIStrategyGenerator:
    """
    Enhanced AI Strategy Generator dengan comprehensive features
    """
    
    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv('OPENROUTER_API_KEY'),
            base_url=os.getenv('OPENROUTER_BASE_URL', 'https://openrouter.ai/api/v1')
        )
        
        # Initialize Prompt Manager
        self.prompt_manager = PromptManager()
        
        # Get strategy generation template
        self.strategy_template_obj = StrategyTemplate()
        self.generated_strategies_dir = Path('generated_strategies')
        self.generated_strategies_dir.mkdir(exist_ok=True)
        
        # Strategy template
        self.strategy_template = self.strategy_template_obj.STRATEGY_TEMPLATE
        
        # Strategy quality patterns
        self.quality_patterns = {
            'required_imports': ['import pandas', 'import numpy', 'class.*\\(IStrategy\\)'],
            'good_practices': ['dataframe\\["[^"]+"\\]', 'logger\\.'],
            'risk_management': ['stoploss', 'roi', 'trailing_stop'],
            'error_handling': ['try:', 'except', 'if.*is None', 'if.*empty']
        }
    
    async def generate_strategy(self, prompt: StrategyPrompt) -> Dict[str, Any]:
        """
        Generate trading strategy dengan enhanced AI analysis
        """
        try:
            logger.info(f"Starting enhanced strategy generation for {prompt.trading_pair}")
            
            # Step 1: Create context for prompt manager
            context = self.prompt_manager.create_context(
                user_id="system",
                variables={
                    "request": prompt.prompt,
                    "trading_pair": prompt.trading_pair,
                    "timeframe": prompt.timeframe,
                    "risk_level": prompt.risk_level,
                    "style": prompt.style,
                    "max_parameters": prompt.max_parameters,
                    "include_indicators": prompt.include_indicators,
                    "exclude_indicators": prompt.exclude_indicators,
                    "strategy_complexity": prompt.strategy_complexity,
                    "backtest_period": prompt.backtest_period,
                    "optimization_goals": prompt.optimization_goals
                }
            )
            
            # Step 2: Render strategy generation prompt
            rendered_prompt = await self.prompt_manager.render_prompt(
                "strategy_generation_basic", context
            )
            
            if not rendered_prompt.success:
                raise ValueError(f"Failed to render prompt: {rendered_prompt.error_message}")
            
            # Step 3: Call LLM API with enhanced settings
            response = self.client.chat.completions.create(
                model=os.getenv('OPENROUTER_MODEL', 'anthropic/claude-3-sonnet'),
                messages=[
                    {"role": "system", "content": rendered_prompt.rendered_system},
                    {"role": "user", "content": rendered_prompt.rendered_user}
                ],
                temperature=0.7,
                max_tokens=4000,
                top_p=0.9,
                frequency_penalty=0.1,
                presence_penalty=0.1
            )
            
            # Step 4: Parse and enhance response
            strategy_data = self._parse_strategy_response(response.choices[0].message.content)
            
            # Step 5: Generate enhanced strategy code
            strategy_code = self._generate_strategy_code(strategy_data, prompt)
            
            # Step 6: Generate parameter ranges for optimization
            parameter_ranges = self._generate_parameter_ranges(strategy_data.get('parameters', {}))
            
            # Step 7: Calculate comprehensive quality metrics
            quality_assessment = self._calculate_comprehensive_quality(strategy_data, strategy_code)
            
            # Step 8: Generate backtest and optimization recommendations
            recommendations = self._generate_comprehensive_recommendations(prompt, strategy_data)
            
            # Compile enhanced result
            result = {
                'strategy_name': strategy_data.get('strategy_name', 'EnhancedAIStrategy'),
                'description': strategy_data.get('description', 'Enhanced AI Generated Strategy'),
                'content': strategy_code,
                'parameters': strategy_data.get('parameters', {}),
                'parameter_ranges': [pr.model_dump() for pr in parameter_ranges],
                'indicators': strategy_data.get('indicators', []),
                'buy_conditions': strategy_data.get('buy_conditions', []),
                'sell_conditions': strategy_data.get('sell_conditions', []),
                'quality_assessment': quality_assessment,
                'recommendations': recommendations,
                'optimization_plan': self._create_optimization_plan(strategy_data, prompt),
                'backtest_plan': self._create_backtest_plan(prompt, strategy_data),
                'risk_management': self._generate_risk_management(prompt, strategy_data),
                'generated_at': datetime.now().isoformat(),
                'model_used': os.getenv('OPENROUTER_MODEL', 'anthropic/claude-3-sonnet'),
                'tokens_used': response.usage.total_tokens if response.usage else 0,
                'render_template_used': rendered_prompt.template_id,
                'strategy_metadata': {
                    'complexity_score': self._calculate_complexity_score(strategy_data),
                    'market_fit': self._assess_market_fit(prompt, strategy_data),
                    'implementation_readiness': quality_assessment.get('implementation_score', 0.5)
                }
            }
            
            logger.info("Enhanced strategy generation completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Enhanced strategy generation failed: {str(e)}")
            raise
    
    def _parse_strategy_response(self, response_text: str) -> Dict[str, Any]:
        """
        Enhanced parsing with better error handling and validation
        """
        try:
            # Try to extract JSON from response
            if '```json' in response_text:
                start = response_text.find('```json') + 7
                end = response_text.find('```', start)
                json_content = response_text[start:end].strip()
                return json.loads(json_content)
            
            # Try to find structured data patterns
            strategy_data = self._extract_structured_data(response_text)
            if strategy_data:
                return strategy_data
            
            # Fallback to intelligent parsing
            return self._intelligent_parsing(response_text)
            
        except Exception as e:
            logger.warning(f"Failed to parse AI response with JSON: {str(e)}")
            return self._create_enhanced_default_strategy()
    
    def _extract_structured_data(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Extract structured data from response text
        """
        strategy_data = {}
        
        # Extract strategy name
        name_match = re.search(r'strategy_name["\s:]+([^"\n,}]+)', text, re.IGNORECASE)
        if name_match:
            strategy_data['strategy_name'] = name_match.group(1).strip()
        
        # Extract description
        desc_match = re.search(r'description["\s:]+([^"\n,}]+)', text, re.IGNORECASE)
        if desc_match:
            strategy_data['description'] = desc_match.group(1).strip()
        
        # Extract buy conditions
        buy_section = re.search(r'buy_conditions["\s:]*\[(.*?)\]', text, re.DOTALL | re.IGNORECASE)
        if buy_section:
            conditions = re.findall(r'"([^"]+)"', buy_section.group(1))
            strategy_data['buy_conditions'] = conditions
        
        # Extract sell conditions
        sell_section = re.search(r'sell_conditions["\s:]*\[(.*?)\]', text, re.DOTALL | re.IGNORECASE)
        if sell_section:
            conditions = re.findall(r'"([^"]+)"', sell_section.group(1))
            strategy_data['sell_conditions'] = conditions
        
        # If we found some data, return it
        if len(strategy_data) >= 2:
            return strategy_data
        
        return None
    
    def _intelligent_parsing(self, response_text: str) -> Dict[str, Any]:
        """
        Intelligent parsing with fallback strategies
        """
        # Try to identify sections
        sections = {
            'strategy_name': None,
            'description': None,
            'parameters': {},
            'indicators': [],
            'buy_conditions': [],
            'sell_conditions': []
        }
        
        lines = response_text.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Identify sections
            if any(keyword in line.lower() for keyword in ['strategy_name', 'nama strategy']):
                current_section = 'strategy_name'
                sections['strategy_name'] = line.split(':', 1)[-1].strip()
            elif any(keyword in line.lower() for keyword in ['description', 'deskripsi']):
                current_section = 'description'
                sections['description'] = line.split(':', 1)[-1].strip()
            elif any(keyword in line.lower() for keyword in ['buy_conditions', 'buy signal']):
                current_section = 'buy_conditions'
            elif any(keyword in line.lower() for keyword in ['sell_conditions', 'sell signal']):
                current_section = 'sell_conditions'
            elif any(keyword in line.lower() for keyword in ['parameters', 'parameter']):
                current_section = 'parameters'
            elif line.startswith('-') or line.startswith('*') or line.startswith('•'):
                content = line.lstrip('-*•').strip()
                if current_section == 'buy_conditions':
                    sections['buy_conditions'].append(content)
                elif current_section == 'sell_conditions':
                    sections['sell_conditions'].append(content)
                elif current_section == 'parameters':
                    # Parse parameter
                    if ':' in content:
                        parts = content.split(':', 1)
                        if len(parts) == 2:
                            param_name = parts[0].strip()
                            param_value = parts[1].strip()
                            sections['parameters'][param_name] = param_value
        
        return sections if any(sections.values()) else self._create_enhanced_default_strategy()
    
    def _create_enhanced_default_strategy(self) -> Dict[str, Any]:
        """
        Create enhanced default strategy with comprehensive features
        """
        return {
            'strategy_name': 'EnhancedRSIEMAStrategy',
            'description': 'Enhanced AI Strategy combining RSI and EMA for optimal entry/exit timing',
            'parameters': {
                'rsi_period': {'default': 14, 'low': 10, 'high': 30, 'step': 2, 'description': 'RSI calculation period', 'param_class': 'IntParameter'},
                'rsi_overbought': {'default': 70, 'low': 60, 'high': 80, 'step': 2, 'description': 'RSI overbought threshold', 'param_class': 'IntParameter'},
                'rsi_oversold': {'default': 30, 'low': 20, 'high': 40, 'step': 2, 'description': 'RSI oversold threshold', 'param_class': 'IntParameter'},
                'ema_fast': {'default': 12, 'low': 8, 'high': 20, 'step': 1, 'description': 'Fast EMA period', 'param_class': 'IntParameter'},
                'ema_slow': {'default': 26, 'low': 20, 'high': 35, 'step': 1, 'description': 'Slow EMA period', 'param_class': 'IntParameter'},
                'bb_period': {'default': 20, 'low': 15, 'high': 25, 'step': 1, 'description': 'Bollinger Bands period', 'param_class': 'IntParameter'},
                'bb_std': {'default': 2.0, 'low': 1.5, 'high': 2.5, 'step': 0.1, 'description': 'Bollinger Bands standard deviation', 'param_class': 'DecimalParameter'}
            },
            'indicators': [
                {
                    'name': 'RSI',
                    'code': 'dataframe["rsi"] = ta.RSI(dataframe["close"], window=self.rsi_period)',
                    'type': 'momentum',
                    'description': 'Relative Strength Index for momentum analysis'
                },
                {
                    'name': 'EMA Fast',
                    'code': 'dataframe["ema_fast"] = ta.EMA(dataframe["close"], window=self.ema_fast)',
                    'type': 'trend',
                    'description': 'Fast Exponential Moving Average'
                },
                {
                    'name': 'EMA Slow',
                    'code': 'dataframe["ema_slow"] = ta.EMA(dataframe["close"], window=self.ema_slow)',
                    'type': 'trend',
                    'description': 'Slow Exponential Moving Average'
                },
                {
                    'name': 'Bollinger Bands',
                    'code': 'bb = ta.BBANDS(dataframe["close"], window=self.bb_period, window_dev=self.bb_std); dataframe["bb_lower"] = bb["lowerband"]; dataframe["bb_middle"] = bb["middleband"]; dataframe["bb_upper"] = bb["upperband"]',
                    'type': 'volatility',
                    'description': 'Bollinger Bands for volatility analysis'
                },
                {
                    'name': 'Volume',
                    'code': 'dataframe["volume_sma"] = dataframe["volume"].rolling(window=20).mean()',
                    'type': 'volume',
                    'description': 'Volume moving average for confirmation'
                }
            ],
            'buy_conditions': [
                'dataframe["rsi"] < self.rsi_oversold',
                'dataframe["ema_fast"] > dataframe["ema_slow"]',
                'dataframe["close"] > dataframe["bb_middle"]',
                'dataframe["volume"] > dataframe["volume_sma"] * 1.2',
                'dataframe["close"] < dataframe["bb_upper"]'
            ],
            'sell_conditions': [
                'dataframe["rsi"] > self.rsi_overbought',
                'dataframe["ema_fast"] < dataframe["ema_slow"]',
                'dataframe["close"] < dataframe["bb_middle"]'
            ],
            'optimization_suggestions': [
                'Optimize RSI parameters for better timing precision',
                'Test different EMA combinations for trend detection',
                'Consider adding volume confirmation for signal strength',
                'Implement dynamic stop-loss based on volatility',
                'Add timeframe-specific parameter optimization'
            ],
            'risk_assessment': {
                'risk_level': 'medium',
                'max_drawdown_estimate': '8-12%',
                'recommended_position_size': '2-4%',
                'stop_loss_suggestion': '2-3%',
                'take_profit_ratio': '1:1.5 to 1:2',
                'market_conditions': 'Trending and ranging markets'
            }
        }
    
    def _generate_strategy_code(self, strategy_data: Dict[str, Any], prompt: StrategyPrompt) -> str:
        """
        Generate comprehensive Python strategy code
        """
        # Clean class name
        class_name = strategy_data.get('strategy_name', 'EnhancedAIStrategy').replace(' ', '').replace('-', '')
        
        # Get indicators and conditions
        indicators = strategy_data.get('indicators', [])
        buy_conditions = strategy_data.get('buy_conditions', [])
        sell_conditions = strategy_data.get('sell_conditions', [])
        
        # Render template
        template = Template(self.strategy_template)
        strategy_code = template.render(
            class_name=class_name,
            description=strategy_data.get('description', 'Enhanced AI Generated Strategy'),
            parameters=strategy_data.get('parameters', {}),
            timeframe=prompt.timeframe,
            trading_pair=prompt.trading_pair,
            risk_level=prompt.risk_level,
            indicators=indicators,
            buy_conditions=buy_conditions,
            sell_conditions=sell_conditions,
            generated_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            prompt=prompt.prompt,
            stop_loss=-0.02,
            trailing_stop=True,
            trailing_positive=0.01,
            trailing_offset=0.02,
            trailing_only=True,
            startup_candles=200,
            can_short=False
        )
        
        return strategy_code
    
    def _generate_parameter_ranges(self, parameters: Dict[str, Any]) -> List[ParameterRange]:
        """
        Generate parameter ranges for optimization
        """
        ranges = []
        
        for param_name, param_config in parameters.items():
            if isinstance(param_config, dict):
                param_type = param_config.get('type', 'int')
                default = param_config.get('default', 1)
                min_val = param_config.get('low', param_config.get('min', default * 0.7 if isinstance(default, (int, float)) else 1))
                max_val = param_config.get('high', param_config.get('max', default * 1.3 if isinstance(default, (int, float)) else default * 2))
                
                if param_type == 'int' or 'IntParameter' in param_config.get('param_class', ''):
                    step = max(1, int((max_val - min_val) / 10))
                    ranges.append(ParameterRange(
                        name=param_name,
                        param_type='int',
                        min_value=min_val,
                        max_value=max_val,
                        step=step
                    ))
                else:  # float or DecimalParameter
                    step = (max_val - min_val) / 10
                    ranges.append(ParameterRange(
                        name=param_name,
                        param_type='float',
                        min_value=min_val,
                        max_value=max_val,
                        step=step
                    ))
        
        return ranges
    
    def _calculate_comprehensive_quality(self, strategy_data: Dict[str, Any], strategy_code: str) -> Dict[str, float]:
        """
        Calculate comprehensive strategy quality metrics
        """
        quality = {
            'code_quality': 0.5,
            'logic_coherence': 0.5,
            'risk_management': 0.5,
            'optimization_potential': 0.5,
            'implementation_readiness': 0.5,
            'market_adaptability': 0.5
        }
        
        # Code quality assessment
        required_elements = ['import pandas', 'import numpy', 'class.*\\(IStrategy\\)', 'def populate']
        for pattern in required_elements:
            if re.search(pattern, strategy_code):
                quality['code_quality'] += 0.1
        
        # Logic coherence
        if strategy_data.get('buy_conditions') and strategy_data.get('sell_conditions'):
            if len(strategy_data['buy_conditions']) >= 1 and len(strategy_data['sell_conditions']) >= 1:
                quality['logic_coherence'] += 0.3
        
        # Risk management
        if 'stoploss' in strategy_code.lower() and 'roi' in strategy_code.lower():
            quality['risk_management'] += 0.3
        
        # Optimization potential
        param_count = len(strategy_data.get('parameters', {}))
        if 3 <= param_count <= 8:  # Sweet spot for optimization
            quality['optimization_potential'] += 0.3
        
        # Implementation readiness
        if strategy_data.get('indicators') and len(strategy_data['indicators']) >= 2:
            quality['implementation_readiness'] += 0.2
        
        return {k: min(1.0, v) for k, v in quality.items()}
    
    def _calculate_complexity_score(self, strategy_data: Dict[str, Any]) -> float:
        """
        Calculate strategy complexity score
        """
        complexity_factors = {
            'indicators': len(strategy_data.get('indicators', [])),
            'conditions': len(strategy_data.get('buy_conditions', [])) + len(strategy_data.get('sell_conditions', [])),
            'parameters': len(strategy_data.get('parameters', {}))
        }
        
        # Normalize factors
        indicator_score = min(1.0, complexity_factors['indicators'] / 5)
        condition_score = min(1.0, complexity_factors['conditions'] / 8)
        parameter_score = min(1.0, complexity_factors['parameters'] / 10)
        
        # Weighted average
        complexity = (indicator_score * 0.4 + condition_score * 0.4 + parameter_score * 0.2)
        return complexity
    
    def _assess_market_fit(self, prompt: StrategyPrompt, strategy_data: Dict[str, Any]) -> str:
        """
        Assess how well the strategy fits the market conditions
        """
        # Simple heuristic-based assessment
        has_trend_indicators = any('ema' in str(ind).lower() or 'sma' in str(ind).lower() 
                                 for ind in strategy_data.get('indicators', []))
        has_momentum_indicators = any('rsi' in str(ind).lower() or 'macd' in str(ind).lower() 
                                    for ind in strategy_data.get('indicators', []))
        
        if prompt.style == 'scalping' and has_momentum_indicators:
            return 'excellent'
        elif prompt.style == 'swing' and has_trend_indicators:
            return 'good'
        elif prompt.style == 'trend' and has_trend_indicators:
            return 'excellent'
        else:
            return 'moderate'
    
    def _generate_comprehensive_recommendations(self, prompt: StrategyPrompt, strategy_data: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Generate comprehensive recommendations for strategy improvement
        """
        recommendations = {
            'backtest': [],
            'optimization': [],
            'risk_management': [],
            'implementation': [],
            'monitoring': []
        }
        
        # Backtest recommendations
        recommendations['backtest'].extend([
            f"Backtest on {prompt.trading_pair} for {prompt.backtest_period} days",
            f"Validate on {prompt.timeframe} timeframe",
            f"Test with {prompt.risk_level} risk level"
        ])
        
        # Strategy-specific recommendations
        if 'rsi' in str(strategy_data).lower():
            recommendations['optimization'].append("Optimize RSI parameters for better entry timing")
        
        if 'ema' in str(strategy_data).lower():
            recommendations['optimization'].append("Test different EMA combinations for trend detection")
        
        if 'volume' not in str(strategy_data).lower():
            recommendations['implementation'].append("Consider adding volume confirmation for signals")
        
        # Risk management recommendations
        recommendations['risk_management'].extend([
            "Implement dynamic position sizing based on volatility",
            "Add maximum drawdown protection",
            "Consider multiple timeframes for confirmation"
        ])
        
        # Monitoring recommendations
        recommendations['monitoring'].extend([
            "Monitor strategy performance across different market conditions",
            "Set up alerts for significant performance changes",
            "Track parameter sensitivity over time"
        ])
        
        return recommendations
    
    def _create_optimization_plan(self, strategy_data: Dict[str, Any], prompt: StrategyPrompt) -> Dict[str, Any]:
        """
        Create detailed optimization plan
        """
        return {
            'optimization_goals': prompt.optimization_goals,
            'parameter_ranges': self._generate_parameter_ranges(strategy_data.get('parameters', {})),
            'optimization_method': 'bayesian',
            'max_iterations': 100,
            'cross_validation': True,
            'multi_timeframe_validation': True,
            'out_of_sample_testing': True
        }
    
    def _create_backtest_plan(self, prompt: StrategyPrompt, strategy_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create comprehensive backtest plan
        """
        return {
            'test_period': f"{prompt.backtest_period} days",
            'timeframes': [prompt.timeframe, '4h', '1d'],
            'trading_pairs': [prompt.trading_pair],
            'performance_metrics': [
                'total_return',
                'sharpe_ratio',
                'max_drawdown',
                'win_rate',
                'profit_factor'
            ],
            'validation_split': {
                'in_sample': 0.7,
                'out_of_sample': 0.3
            },
            'stress_testing': True,
            'monte_carlo': True
        }
    
    def _generate_risk_management(self, prompt: StrategyPrompt, strategy_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate risk management recommendations
        """
        base_risk = {
            'max_position_size': 0.05 if prompt.risk_level == 'high' else 0.03 if prompt.risk_level == 'medium' else 0.02,
            'stop_loss': 0.02 if prompt.risk_level == 'high' else 0.03 if prompt.risk_level == 'medium' else 0.05,
            'max_daily_loss': 0.10 if prompt.risk_level == 'high' else 0.07 if prompt.risk_level == 'medium' else 0.05,
            'max_drawdown_limit': 0.20 if prompt.risk_level == 'high' else 0.15 if prompt.risk_level == 'medium' else 0.10
        }
        
        return base_risk
    
    async def optimize_strategy_parameters(
        self,
        strategy_data: Dict[str, Any],
        optimization_goals: List[str],
        max_iterations: int = 100
    ) -> Dict[str, Any]:
        """
        Generate optimization recommendations for strategy
        """
        from .parameter_optimizer import AIParameterOptimizer
        
        optimizer = AIParameterOptimizer()
        
        # Create optimization objectives
        objectives = []
        for goal in optimization_goals:
            if goal == "profit":
                objectives.append(OptimizationObjective(
                    metric="total_return", direction="maximize", weight=0.4
                ))
            elif goal == "win_rate":
                objectives.append(OptimizationObjective(
                    metric="win_rate", direction="maximize", weight=0.3
                ))
            elif goal == "sharpe_ratio":
                objectives.append(OptimizationObjective(
                    metric="sharpe_ratio", direction="maximize", weight=0.3
                ))
        
        # Generate parameter ranges
        parameter_ranges = self._generate_parameter_ranges(strategy_data.get('parameters', {}))
        
        if not parameter_ranges:
            return {"error": "No parameters available for optimization"}
        
        try:
            result = await optimizer.optimize_parameters(
                strategy_code=strategy_data.get('content', ''),
                parameter_ranges=parameter_ranges,
                objectives=objectives,
                max_iterations=max_iterations,
                optimization_type="guided"
            )
            
            return {
                'optimization_id': result.optimization_id,
                'best_parameters': result.best_parameters,
                'improvement_percentage': result.improvement_percentage,
                'confidence_interval': result.confidence_interval,
                'recommendations': result.ai_recommendations,
                'execution_time': result.execution_time
            }
            
        except Exception as e:
            logger.error(f"Parameter optimization failed: {str(e)}")
            return {"error": str(e)}
    
    def save_strategy(self, strategy_data: Dict[str, Any]) -> str:
        """
        Save generated strategy and metadata to files
        """
        # Save strategy code
        filename = f"{strategy_data['strategy_name'].lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
        filepath = self.generated_strategies_dir / filename
        
        with open(filepath, 'w') as f:
            f.write(strategy_data['content'])
        
        # Save comprehensive metadata
        metadata_file = self.generated_strategies_dir / f"{filename}_metadata.json"
        metadata = {
            'strategy_name': strategy_data['strategy_name'],
            'description': strategy_data['description'],
            'parameters': strategy_data['parameters'],
            'quality_assessment': strategy_data['quality_assessment'],
            'recommendations': strategy_data['recommendations'],
            'optimization_plan': strategy_data['optimization_plan'],
            'backtest_plan': strategy_data['backtest_plan'],
            'risk_management': strategy_data['risk_management'],
            'generated_at': strategy_data['generated_at'],
            'model_used': strategy_data['model_used'],
            'tokens_used': strategy_data['tokens_used'],
            'strategy_metadata': strategy_data['strategy_metadata']
        }
        
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2, default=str)
        
        # Create README for strategy
        readme_file = self.generated_strategies_dir / f"{filename}_README.md"
        self._create_strategy_readme(strategy_data, readme_file)
        
        logger.info(f"Strategy saved to {filepath}")
        return str(filepath)
    
    def _create_strategy_readme(self, strategy_data: Dict[str, Any], readme_path: Path):
        """
        Create comprehensive README for the strategy
        """
        readme_content = f"""# {strategy_data['strategy_name']}

## Description
{strategy_data['description']}

## Strategy Overview
- **Generated**: {strategy_data['generated_at']}
- **Model Used**: {strategy_data['model_used']}
- **Tokens Used**: {strategy_data['tokens_used']}

## Parameters
{self._format_parameters_for_readme(strategy_data['parameters'])}

## Quality Assessment
- **Code Quality**: {strategy_data['quality_assessment'].get('code_quality', 0):.1%}
- **Logic Coherence**: {strategy_data['quality_assessment'].get('logic_coherence', 0):.1%}
- **Risk Management**: {strategy_data['quality_assessment'].get('risk_management', 0):.1%}
- **Implementation Readiness**: {strategy_data['quality_assessment'].get('implementation_readiness', 0):.1%}

## Backtest Plan
- **Test Period**: {strategy_data['backtest_plan']['test_period']}
- **Timeframes**: {', '.join(strategy_data['backtest_plan']['timeframes'])}
- **Metrics**: {', '.join(strategy_data['backtest_plan']['performance_metrics'])}

## Optimization Plan
- **Goals**: {', '.join(strategy_data['optimization_plan']['optimization_goals'])}
- **Method**: {strategy_data['optimization_plan']['optimization_method']}
- **Max Iterations**: {strategy_data['optimization_plan']['max_iterations']}

## Risk Management
- **Max Position Size**: {strategy_data['risk_management']['max_position_size']:.1%}
- **Stop Loss**: {strategy_data['risk_management']['stop_loss']:.1%}
- **Max Daily Loss**: {strategy_data['risk_management']['max_daily_loss']:.1%}
- **Max Drawdown Limit**: {strategy_data['risk_management']['max_drawdown_limit']:.1%}

## Recommendations
{self._format_recommendations_for_readme(strategy_data['recommendations'])}

## Usage
1. Copy the strategy file to your Freqtrade strategies directory
2. Run backtest with recommended settings
3. Optimize parameters using the provided optimization plan
4. Monitor performance according to risk management guidelines

## Disclaimer
This strategy is AI-generated and should be thoroughly tested before live trading. Past performance does not guarantee future results.
"""
        
        with open(readme_path, 'w') as f:
            f.write(readme_content)
    
    def _format_parameters_for_readme(self, parameters: Dict[str, Any]) -> str:
        """
        Format parameters for README
        """
        lines = []
        for param_name, param_config in parameters.items():
            default = param_config.get('default', 'N/A')
            description = param_config.get('description', 'Strategy parameter')
            lines.append(f"- **{param_name}**: {description} (default: {default})")
        return '\n'.join(lines)
    
    def _format_recommendations_for_readme(self, recommendations: Dict[str, List[str]]) -> str:
        """
        Format recommendations for README
        """
        lines = []
        for category, recs in recommendations.items():
            lines.append(f"### {category.title()}")
            for rec in recs:
                lines.append(f"- {rec}")
            lines.append("")
        return '\n'.join(lines)


def main():
    """
    Test function for enhanced strategy generator
    """
    async def test_generator():
        generator = EnhancedAIStrategyGenerator()
        
        prompt = StrategyPrompt(
            prompt="Create a momentum-based strategy using RSI and volume confirmation",
            trading_pair="BTC/USDT",
            timeframe="1h",
            risk_level="medium",
            style="swing",
            max_parameters=8,
            optimization_goals=["profit", "sharpe_ratio"]
        )
        
        strategy = await generator.generate_strategy(prompt)
        print(f"Generated strategy: {strategy['strategy_name']}")
        print(f"Quality score: {strategy['quality_assessment']['implementation_readiness']:.1%}")
        print(f"Parameters: {len(strategy['parameters'])}")
        print(f"File saved: {generator.save_strategy(strategy)}")
    
    asyncio.run(test_generator())


if __name__ == "__main__":
    main()
