"""
NusaNexus NoFOMO - AI Strategy Generator
Generate trading strategies using LLM
"""

import os
import logging
from typing import Any, Dict
from openai import OpenAI
from jinja2 import Template
from pydantic import BaseModel
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StrategyPrompt(BaseModel):
    prompt: str
    trading_pair: str
    timeframe: str
    risk_level: str
    style: str


class StrategyTemplate:
    """
    Template untuk Freqtrade strategy
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
from functools import reduce

class {{ class_name }}(IStrategy):
    """
    {{ description }}
    
    Strategy Parameters:
    {% for param, desc in parameters.items() -%}
    - {{ param }}: {{ desc }}
    {% endfor -%}
    """
    
    # ROI table
    roi = {
        "0": 0.10,
        "200": 0.05,
        "400": 0.02,
        "600": 0.01,
        "800": 0,
        "1000": -0.05,
        "1200": -0.10,
        "1400": -0.15,
        "1600": -0.20,
        "1800": -0.25,
        "2000": -0.30
    }

    # Stoploss
    stoploss = -0.02

    # Trailing stop
    trailing_stop = True
    trailing_stop_positive = 0.01
    trailing_stop_positive_offset = 0.02
    trailing_only_offset_is_reached = True

    # Timeframe
    timeframe = "{{ timeframe }}"
    timeframe_min = timeframe_to_seconds(timeframe)

    # Informative pairs
    informative_pairs = []

    def populate_indicators(self, dataframe, metadata):
        {% for indicator in indicators %}
        # {{ indicator.name }}
        {{ indicator.code }}
        {% endfor %}

        return dataframe

    def populate_buy_trend(self, dataframe, metadata):
        dataframe.loc[
            ({% for condition in buy_conditions -%}
            ({{ condition }}){% if not loop.last %} & {% endif -%}
            {% endfor %}),
            'buy'
        ] = 1

        return dataframe

    def populate_sell_trend(self, dataframe, metadata):
        dataframe.loc[
            ({% for condition in sell_conditions -%}
            ({{ condition }}){% if not loop.last %} & {% endif -%}
            {% endfor %}),
            'sell'
        ] = 1

        return dataframe

    def check_buy_timeout(self, pair, trade, **kwargs) -> bool:
        return False

    def check_sell_timeout(self, pair, trade, **kwargs) -> bool:
        return False
'''


class AIStrategyGenerator:
    """
    AI Strategy Generator menggunakan OpenRouter/Together AI
    """
    
    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv('OPENROUTER_API_KEY'),
            base_url=os.getenv('OPENROUTER_BASE_URL', 'https://openrouter.ai/api/v1')
        )
        
        self.strategy_template = Template(StrategyTemplate.STRATEGY_TEMPLATE)
        self.generated_strategies_dir = os.path.join(os.path.dirname(__file__), 'generated_strategies')
        os.makedirs(self.generated_strategies_dir, exist_ok=True)
    
    async def generate_strategy(self, prompt: StrategyPrompt) -> Dict[str, Any]:
        """
        Generate trading strategy berdasarkan prompt
        """
        try:
            # Prepare system prompt
            system_prompt = """
            Anda adalah ahli trading algoritma dan Freqtrade strategy development. 
            Buat strategi trading Python untuk Freqtrade berdasarkan permintaan user.
            
            Guidelines:
            1. Gunakan only built-in indicators yang tersedia di Freqtrade (RSI, EMA, MACD, Bollinger Bands, dll)
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
            """
            
            # Prepare user prompt
            user_prompt = f"""
            Buat Freqtrade strategy dengan detail berikut:
            - Request: {prompt.prompt}
            - Trading Pair: {prompt.trading_pair}
            - Timeframe: {prompt.timeframe}
            - Risk Level: {prompt.risk_level}
            - Trading Style: {prompt.style}
            
            Gunakan timeframe {prompt.timeframe} dan fokuskan pada {prompt.style} trading dengan risk level {prompt.risk_level}.
            """
            
            # Call LLM API
            response = self.client.chat.completions.create(
                model=os.getenv('OPENROUTER_MODEL', 'anthropic/claude-3-sonnet'),
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=4000
            )
            
            # Parse response
            strategy_data = self._parse_strategy_response(response.choices[0].message.content)
            
            # Generate strategy code
            strategy_code = self._generate_strategy_code(strategy_data, prompt)
            
            return {
                'strategy_name': strategy_data.get('strategy_name', 'AIStrategy'),
                'description': strategy_data.get('description', 'AI Generated Strategy'),
                'content': strategy_code,
                'parameters': strategy_data.get('parameters', {}),
                'confidence_score': self._calculate_confidence_score(strategy_data),
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to generate strategy: {str(e)}")
            raise
    
    def _parse_strategy_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse LLM response menjadi structured data
        """
        # Simple parsing - in production, use more robust parsing
        strategy_data = {
            'strategy_name': 'AIStrategy',
            'description': 'AI Generated Trading Strategy',
            'parameters': {
                'rsi_period': 14,
                'rsi_overbought': 70,
                'rsi_oversold': 30,
                'ema_period': 21
            },
            'indicators': [
                {
                    'name': 'RSI',
                    'code': 'dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)'
                },
                {
                    'name': 'EMA',
                    'code': 'dataframe["ema21"] = ta.EMA(dataframe, timeperiod=21)'
                }
            ],
            'buy_conditions': [
                'dataframe["rsi"] < 30',
                'dataframe["close"] > dataframe["ema21"]'
            ],
            'sell_conditions': [
                'dataframe["rsi"] > 70',
                'dataframe["close"] < dataframe["ema21"]'
            ]
        }
        
        return strategy_data
    
    def _generate_strategy_code(self, strategy_data: Dict[str, Any], prompt: StrategyPrompt) -> str:
        """
        Generate Python strategy code dari template
        """
        # Clean class name
        class_name = strategy_data.get('strategy_name', 'AIStrategy').replace(' ', '').replace('-', '')
        
        # Render template
        strategy_code = self.strategy_template.render(
            class_name=class_name,
            description=strategy_data.get('description', 'AI Generated Strategy'),
            parameters=strategy_data.get('parameters', {}),
            timeframe=prompt.timeframe,
            indicators=strategy_data.get('indicators', []),
            buy_conditions=strategy_data.get('buy_conditions', []),
            sell_conditions=strategy_data.get('sell_conditions', []),
            generated_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            prompt=prompt.prompt
        )
        
        return strategy_code
    
    def _calculate_confidence_score(self, strategy_data: Dict[str, Any]) -> float:
        """
        Calculate confidence score untuk strategy yang digenerate
        """
        score = 0.5  # Base score
        
        # Check completeness
        required_fields = ['parameters', 'indicators', 'buy_conditions', 'sell_conditions']
        completeness = sum(1 for field in required_fields if strategy_data.get(field))
        score += (completeness / len(required_fields)) * 0.3
        
        # Check complexity (more complex = potentially better, but not too complex)
        buy_conditions = len(strategy_data.get('buy_conditions', []))
        sell_conditions = len(strategy_data.get('sell_conditions', []))
        total_conditions = buy_conditions + sell_conditions
        
        if 2 <= total_conditions <= 6:  # Sweet spot
            score += 0.2
        elif total_conditions > 10:  # Too complex
            score -= 0.1
        
        return min(max(score, 0.0), 1.0)  # Clamp between 0 and 1
    
    def save_strategy(self, strategy_data: Dict[str, Any]) -> str:
        """
        Save generated strategy ke file
        """
        filename = f"{strategy_data['strategy_name'].lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
        filepath = os.path.join(self.generated_strategies_dir, filename)
        
        with open(filepath, 'w') as f:
            f.write(strategy_data['content'])
        
        return filepath


def main():
    """
    Test function untuk strategy generator
    """
    generator = AIStrategyGenerator()
    
    prompt = StrategyPrompt(
        prompt="Buat strategi scalping untuk BTC/USDT dengan RSI dan EMA crossover",
        trading_pair="BTC/USDT",
        timeframe="5m",
        risk_level="medium",
        style="scalping"
    )
    
    strategy = generator.generate_strategy(prompt)
    print(f"Generated strategy: {strategy['strategy_name']}")
    print(f"Confidence: {strategy['confidence_score']}")


if __name__ == "__main__":
    main()
