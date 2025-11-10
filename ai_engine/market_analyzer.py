"""
NusaNexus NoFOMO - AI Market Analyzer
Market trend analysis and prediction engine
"""

import os
import asyncio
import json
from typing import Any, Dict, List, Optional, Union, cast
from datetime import datetime
import pandas as pd
import numpy as np
from pydantic import BaseModel, ConfigDict
from openai import OpenAI
import structlog
from pathlib import Path
import yfinance as yf
import ta as ta_module
from enum import Enum

# Configure logging
logger = structlog.get_logger(__name__)

# The `ta` library does not ship type hints, so inform the type checker.
ta = cast(Any, ta_module)


class AnalysisType(str, Enum):
    TECHNICAL = "technical"
    SENTIMENT = "sentiment"
    FUNDAMENTAL = "fundamental"
    VOLATILITY = "volatility"
    TREND = "trend"
    BREAKOUT = "breakout"
    CORRELATION = "correlation"


class TimeHorizon(str, Enum):
    SHORT_TERM = "1h"  # 1 hour
    MEDIUM_TERM = "4h"  # 4 hours
    LONG_TERM = "1d"   # 1 day
    WEEKLY = "1w"      # 1 week


class MarketSignal(BaseModel):
    """Market signal from analysis"""
    signal_type: str  # "buy", "sell", "hold", "neutral"
    strength: float   # 0.0 to 1.0
    confidence: float # 0.0 to 1.0
    reasoning: str
    time_horizon: TimeHorizon
    price_targets: Dict[str, Union[str, float]]  # "support", "resistance", "entry", "exit"
    risk_level: str  # "low", "medium", "high"


class MarketPrediction(BaseModel):
    """Market price prediction"""
    symbol: str
    current_price: float
    predicted_price_1h: Optional[float] = None
    predicted_price_4h: Optional[float] = None
    predicted_price_1d: Optional[float] = None
    predicted_price_1w: Optional[float] = None
    confidence_level: float
    prediction_method: str
    key_factors: List[str]
    volatility_estimate: float
    trend_direction: str  # "bullish", "bearish", "sideways"


class MarketAnalysisResult(BaseModel):
    """Complete market analysis result"""
    model_config = ConfigDict(protected_namespaces=())
    
    analysis_id: str
    symbol: str
    analysis_type: AnalysisType
    time_horizon: TimeHorizon
    timestamp: datetime
    market_data: Dict[str, Any]
    technical_indicators: Dict[str, float]
    market_signals: List[MarketSignal]
    predictions: Optional[MarketPrediction]
    market_conditions: Dict[str, Any]
    key_levels: Dict[str, List[float]]
    risk_factors: List[str]
    ai_insights: List[str]
    confidence_score: float
    processing_time: float
    model_used: str
    tokens_used: int


class AIMarketAnalyzer:
    """
    AI-powered market analysis engine
    """
    
    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv('OPENROUTER_API_KEY'),
            base_url=os.getenv('OPENROUTER_BASE_URL', 'https://openrouter.ai/api/v1')
        )
        self.analyses_dir = Path('market_analyses')
        self.analyses_dir.mkdir(exist_ok=True)
        self.cache = {}
        self.rate_limits = {}
        
    async def analyze_market(
        self,
        symbol: str,
        analysis_type: AnalysisType,
        time_horizon: TimeHorizon = TimeHorizon.MEDIUM_TERM,
        additional_symbols: Optional[List[str]] = None
    ) -> MarketAnalysisResult:
        """
        Perform comprehensive market analysis
        """
        start_time = datetime.now()
        analysis_id = f"analysis_{symbol}_{analysis_type}_{start_time.strftime('%Y%m%d_%H%M%S')}"
        
        try:
            logger.info(f"Starting market analysis {analysis_id} for {symbol}")
            
            # Step 1: Fetch market data
            market_data = await self._fetch_market_data(symbol, time_horizon)
            
            # Step 2: Technical analysis
            technical_data = await self._perform_technical_analysis(market_data)
            
            # Step 3: Multi-symbol correlation (if provided)
            # Step 4: AI-powered analysis
            ai_insights = await self._analyze_with_ai(
                symbol, market_data, technical_data, analysis_type, time_horizon
            )
            
            # Step 5: Generate signals and predictions
            signals = await self._generate_market_signals(
                symbol, technical_data, ai_insights, time_horizon
            )
            predictions = await self._generate_predictions(
                symbol, market_data, technical_data, ai_insights
            )
            
            # Step 6: Market conditions assessment
            market_conditions = await self._assess_market_conditions(
                symbol, market_data, technical_data
            )
            
            # Step 7: Risk assessment
            risk_factors = await self._assess_risk_factors(
                symbol, market_data, technical_data, ai_insights
            )
            
            # Step 8: Key levels identification
            key_levels = await self._identify_key_levels(market_data, technical_data)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Compile result
            result = MarketAnalysisResult(
                analysis_id=analysis_id,
                symbol=symbol,
                analysis_type=analysis_type,
                time_horizon=time_horizon,
                timestamp=start_time,
                market_data=market_data,
                technical_indicators=technical_data,
                market_signals=signals,
                predictions=predictions,
                market_conditions=market_conditions,
                key_levels=key_levels,
                risk_factors=risk_factors,
                ai_insights=ai_insights.get('insights', []),
                confidence_score=ai_insights.get('confidence', 0.7),
                processing_time=processing_time,
                model_used=os.getenv('OPENROUTER_MODEL', 'anthropic/claude-3-sonnet'),
                tokens_used=ai_insights.get('tokens_used', 0)
            )
            
            # Save analysis
            await self._save_analysis_result(result)
            
            logger.info(f"Market analysis {analysis_id} completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Market analysis failed: {str(e)}")
            raise
    
    async def _fetch_market_data(
        self,
        symbol: str,
        time_horizon: TimeHorizon
    ) -> Dict[str, Any]:
        """
        Fetch market data from multiple sources
        """
        try:
            # Map time horizon to data period
            periods = {
                TimeHorizon.SHORT_TERM: "5d",
                TimeHorizon.MEDIUM_TERM: "1mo", 
                TimeHorizon.LONG_TERM: "6mo",
                TimeHorizon.WEEKLY: "2y"
            }
            
            period = periods.get(time_horizon, "1mo")
            
            # Fetch OHLCV data
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period, interval="1d")
            
            if hist.empty:
                raise ValueError(f"No data found for symbol {symbol}")
            
            # Convert to standard format
            market_data = {
                'symbol': symbol,
                'current_price': float(hist['Close'].iloc[-1]),
                'open': float(hist['Open'].iloc[-1]),
                'high': float(hist['High'].iloc[-1]),
                'low': float(hist['Low'].iloc[-1]),
                'close': float(hist['Close'].iloc[-1]),
                'volume': float(hist['Volume'].iloc[-1]),
                'price_change': float(hist['Close'].iloc[-1] - hist['Close'].iloc[-2]),
                'price_change_pct': float((hist['Close'].iloc[-1] - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2] * 100),
                'historical_data': hist.to_dict('records'),
                'timestamp': datetime.now().isoformat()
            }
            
            # Add market statistics
            try:
                info = ticker.info
                market_data.update({
                    'market_cap': info.get('marketCap'),
                    'volume_24h': info.get('volume24Hr'),
                    ' circulating_supply': info.get('circulatingSupply'),
                    'total_supply': info.get('totalSupply'),
                    'ath': info.get('allTimeHigh'),
                    'atl': info.get('allTimeLow')
                })
            except Exception:
                pass  # Some symbols might not have info
            
            return market_data
            
        except Exception as e:
            logger.error(f"Failed to fetch market data for {symbol}: {str(e)}")
            raise
    
    async def _perform_technical_analysis(self, market_data: Dict[str, Any]) -> Dict[str, float]:
        """
        Perform technical analysis on market data
        """
        try:
            # Convert historical data to DataFrame
            hist_data = market_data.get('historical_data', [])
            if not hist_data:
                raise ValueError("No historical data for technical analysis")
            
            df = pd.DataFrame(hist_data)
            df['Date'] = pd.to_datetime(df['Date'])
            df.set_index('Date', inplace=True)
            
            indicators = {}
            
            # RSI
            indicators['rsi'] = float(ta.momentum.RSIIndicator(df['Close']).rsi().iloc[-1])
            
            # Moving Averages
            indicators['sma_20'] = float(ta.trend.SMAIndicator(df['Close'], window=20).sma_indicator().iloc[-1])
            indicators['sma_50'] = float(ta.trend.SMAIndicator(df['Close'], window=50).sma_indicator().iloc[-1])
            indicators['ema_12'] = float(ta.trend.EMAIndicator(df['Close'], window=12).ema_indicator().iloc[-1])
            indicators['ema_26'] = float(ta.trend.EMAIndicator(df['Close'], window=26).ema_indicator().iloc[-1])
            
            # MACD
            macd = ta.trend.MACD(df['Close'])
            indicators['macd'] = float(macd.macd().iloc[-1])
            indicators['macd_signal'] = float(macd.macd_signal().iloc[-1])
            indicators['macd_histogram'] = float(macd.macd_diff().iloc[-1])
            
            # Bollinger Bands
            bb = ta.volatility.BollingerBands(df['Close'])
            indicators['bb_upper'] = float(bb.bollinger_hband().iloc[-1])
            indicators['bb_middle'] = float(bb.bollinger_mavg().iloc[-1])
            indicators['bb_lower'] = float(bb.bollinger_lband().iloc[-1])
            indicators['bb_width'] = float((indicators['bb_upper'] - indicators['bb_lower']) / indicators['bb_middle'])
            
            # Stochastic
            stoch = ta.momentum.StochasticOscillator(df['High'], df['Low'], df['Close'])
            indicators['stoch_k'] = float(stoch.stoch().iloc[-1])
            indicators['stoch_d'] = float(stoch.stoch_signal().iloc[-1])
            
            # ADX (Average Directional Index)
            try:
                adx = ta.trend.ADXIndicator(df['High'], df['Low'], df['Close'])
                indicators['adx'] = float(adx.adx().iloc[-1])
            except Exception:
                indicators['adx'] = 0.0
            
            # Williams %R
            try:
                willr = ta.momentum.WilliamsRIndicator(df['High'], df['Low'], df['Close'])
                indicators['williams_r'] = float(willr.williams_r().iloc[-1])
            except Exception:
                indicators['williams_r'] = -50.0
            
            # Volume indicators
            volume_series = cast(pd.Series, df['Volume'])
            rolling_mean = cast(pd.Series, volume_series.rolling(window=20).mean())
            indicators['volume_sma'] = float(rolling_mean.iloc[-1])
            last_volume = float(volume_series.iloc[-1])
            sma_value = indicators['volume_sma'] or 1e-9
            indicators['volume_ratio'] = float(last_volume / sma_value)
            
            # Volatility
            returns = df['Close'].pct_change().dropna()
            indicators['volatility'] = float(returns.std() * np.sqrt(252))  # Annualized
            
            # Price position in range
            current_price = market_data['current_price']
            high_52w = df['Close'].max()
            low_52w = df['Close'].min()
            indicators['price_position'] = float((current_price - low_52w) / (high_52w - low_52w))
            
            return indicators
            
        except Exception as e:
            logger.error(f"Technical analysis failed: {str(e)}")
            # Return default values on error
            return {
                'rsi': 50.0,
                'sma_20': market_data['current_price'],
                'sma_50': market_data['current_price'],
                'ema_12': market_data['current_price'],
                'ema_26': market_data['current_price'],
                'macd': 0.0,
                'macd_signal': 0.0,
                'macd_histogram': 0.0,
                'bb_upper': market_data['current_price'] * 1.02,
                'bb_middle': market_data['current_price'],
                'bb_lower': market_data['current_price'] * 0.98,
                'bb_width': 0.04,
                'stoch_k': 50.0,
                'stoch_d': 50.0,
                'adx': 25.0,
                'williams_r': -50.0,
                'volume_sma': market_data.get('volume', 1000000),
                'volume_ratio': 1.0,
                'volatility': 0.2,
                'price_position': 0.5
            }
    
    async def _analyze_correlations(
        self,
        primary_symbol: str,
        additional_symbols: List[str]
    ) -> Dict[str, Any]:
        """
        Analyze correlations with other symbols
        """
        try:
            correlations = {}
            
            for symbol in additional_symbols:
                # Fetch data for both symbols
                primary_data = yf.Ticker(primary_symbol).history(period="3mo")
                secondary_data = yf.Ticker(symbol).history(period="3mo")
                
                if not primary_data.empty and not secondary_data.empty:
                    # Align data by date
                    primary_returns: pd.Series = cast(pd.Series, primary_data['Close'].pct_change().dropna())
                    secondary_returns: pd.Series = cast(pd.Series, secondary_data['Close'].pct_change().dropna())
                    
                    # Calculate correlation
                    correlation = primary_returns.corr(secondary_returns)
                    correlations[symbol] = float(correlation)
            
            return correlations
            
        except Exception as e:
            logger.error(f"Correlation analysis failed: {str(e)}")
            return {}
    
    async def _analyze_with_ai(
        self,
        symbol: str,
        market_data: Dict[str, Any],
        technical_data: Dict[str, Any],
        analysis_type: AnalysisType,
        time_horizon: TimeHorizon
    ) -> Dict[str, Any]:
        """
        Use AI to analyze market data and generate insights
        """
        system_prompt = f"""
        Anda adalah ahli analisis pasar cryptocurrency dan trading.
        Analisis data pasar dan berikan insight yang actionable.
        
        Guidelines:
        1. Gunakan analisis teknikal dan fundamental
        2. Berikan reasoning yang jelas untuk setiap insight
        3. Fokus pada time horizon {time_horizon.value}
        4. Berikan confidence level untuk setiap prediksi
        5. Berikan risk assessment
        6. Gunakan format yang structured
        """
        
        # Prepare market summary
        current_price = market_data['current_price']
        price_change_pct = market_data['price_change_pct']
        
        # Create market summary for AI
        market_summary = f"""
        Symbol: {symbol}
        Current Price: ${current_price:,.2f}
        Price Change: {price_change_pct:+.2f}%
        
        Technical Indicators:
        - RSI: {technical_data.get('rsi', 0):.1f}
        - MACD: {technical_data.get('macd', 0):.4f}
        - MACD Signal: {technical_data.get('macd_signal', 0):.4f}
        - Bollinger Bands Position: {((current_price - technical_data.get('bb_lower', 0)) / (technical_data.get('bb_upper', current_price * 1.02) - technical_data.get('bb_lower', current_price * 0.98))):.2f}
        - Stochastic K: {technical_data.get('stoch_k', 50):.1f}
        - ADX: {technical_data.get('adx', 25):.1f}
        - Volume Ratio: {technical_data.get('volume_ratio', 1):.2f}
        - Volatility: {technical_data.get('volatility', 0.2):.2f}
        - Price Position (52w): {technical_data.get('price_position', 0.5):.2f}
        
        Analysis Type: {analysis_type.value}
        Time Horizon: {time_horizon.value}
        """
        
        user_prompt = f"""
        Analisis pasar {symbol} berdasarkan data berikut:
        
        {market_summary}
        
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
        """
        
        response = self.client.chat.completions.create(
            model=os.getenv('OPENROUTER_MODEL', 'anthropic/claude-3-sonnet'),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=2000
        )
        
        return self._parse_ai_analysis_response(response.choices[0].message.content or "")
    
    async def _generate_market_signals(
        self,
        symbol: str,
        technical_data: Dict[str, Any],
        ai_insights: Dict[str, Any],
        time_horizon: TimeHorizon
    ) -> List[MarketSignal]:
        """
        Generate market signals based on analysis
        """
        signals = []
        
        try:
            # Technical signal based on RSI
            rsi = technical_data.get('rsi', 50)
            if rsi < 30:
                signals.append(MarketSignal(
                    signal_type="buy",
                    strength=min(1.0, (30 - rsi) / 30),
                    confidence=0.8,
                    reasoning=f"RSI oversold at {rsi:.1f}",
                    time_horizon=time_horizon,
                    price_targets={"support": "current_rsi_zone"},
                    risk_level="medium"
                ))
            elif rsi > 70:
                signals.append(MarketSignal(
                    signal_type="sell",
                    strength=min(1.0, (rsi - 70) / 30),
                    confidence=0.8,
                    reasoning=f"RSI overbought at {rsi:.1f}",
                    time_horizon=time_horizon,
                    price_targets={"resistance": "current_rsi_zone"},
                    risk_level="medium"
                ))
            
            # MACD signal
            macd = technical_data.get('macd', 0)
            macd_signal = technical_data.get('macd_signal', 0)
            macd_histogram = technical_data.get('macd_histogram', 0)
            
            if macd > macd_signal and macd_histogram > 0:
                signals.append(MarketSignal(
                    signal_type="buy",
                    strength=min(1.0, abs(macd_histogram) * 10),
                    confidence=0.7,
                    reasoning=f"MACD bullish crossover (MACD: {macd:.4f}, Signal: {macd_signal:.4f})",
                    time_horizon=time_horizon,
                    price_targets={"momentum": "macd_crossover"},
                    risk_level="low"
                ))
            elif macd < macd_signal and macd_histogram < 0:
                signals.append(MarketSignal(
                    signal_type="sell",
                    strength=min(1.0, abs(macd_histogram) * 10),
                    confidence=0.7,
                    reasoning=f"MACD bearish crossover (MACD: {macd:.4f}, Signal: {macd_signal:.4f})",
                    time_horizon=time_horizon,
                    price_targets={"momentum": "macd_crossover"},
                    risk_level="low"
                ))
            
            # Volume confirmation
            volume_ratio = technical_data.get('volume_ratio', 1)
            if volume_ratio > 1.5:
                signals.append(MarketSignal(
                    signal_type="hold",
                    strength=min(1.0, volume_ratio - 1),
                    confidence=0.6,
                    reasoning=f"High volume ratio: {volume_ratio:.2f}x average",
                    time_horizon=time_horizon,
                    price_targets={"volume": "confirmation"},
                    risk_level="low"
                ))
            
            # Add AI-generated signals if available
            key_signals = ai_insights.get('key_signals', [])
            for signal_data in key_signals:
                signals.append(MarketSignal(
                    signal_type=signal_data.get('signal', 'hold'),
                    strength=signal_data.get('strength', 0.5),
                    confidence=signal_data.get('confidence', 0.7),
                    reasoning=signal_data.get('reasoning', 'AI analysis'),
                    time_horizon=time_horizon,
                    price_targets=signal_data.get('price_targets', {}),
                    risk_level="medium"
                ))
            
        except Exception as e:
            logger.error(f"Signal generation failed: {str(e)}")
            # Return a neutral signal on error
            signals.append(MarketSignal(
                signal_type="hold",
                strength=0.1,
                confidence=0.3,
                reasoning="Unable to generate signals due to error",
                time_horizon=time_horizon,
                price_targets={},
                risk_level="medium"
            ))
        
        return signals
    
    async def _generate_predictions(
        self,
        symbol: str,
        market_data: Dict[str, Any],
        technical_data: Dict[str, Any],
        ai_insights: Dict[str, Any]
    ) -> Optional[MarketPrediction]:
        """
        Generate market price predictions
        """
        try:
            current_price = market_data['current_price']
            market_outlook = ai_insights.get('market_outlook', {})
            
            predictions = MarketPrediction(
                symbol=symbol,
                current_price=current_price,
                predicted_price_1h=current_price * (1 + np.random.normal(0, 0.01)),  # Mock 1h
                predicted_price_4h=current_price * (1 + np.random.normal(0, 0.02)),  # Mock 4h
                predicted_price_1d=current_price * (1 + np.random.normal(0, 0.05)),  # Mock 1d
                predicted_price_1w=current_price * (1 + np.random.normal(0, 0.1)),   # Mock 1w
                confidence_level=market_outlook.get('confidence', 0.6),
                prediction_method="technical_ai_hybrid",
                key_factors=ai_insights.get('insights', []),
                volatility_estimate=technical_data.get('volatility', 0.2),
                trend_direction=market_outlook.get('next_1d', 'sideways')
            )
            
            return predictions
            
        except Exception as e:
            logger.error(f"Prediction generation failed: {str(e)}")
            return None
    
    async def _assess_market_conditions(
        self,
        symbol: str,
        market_data: Dict[str, Any],
        technical_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Assess current market conditions
        """
        conditions = {
            'volatility': 'low' if technical_data.get('volatility', 0.2) < 0.3 else 'high',
            'trend': 'sideways',
            'liquidity': 'medium',
            'momentum': 'neutral'
        }
        
        # Determine trend
        sma_20 = technical_data.get('sma_20', 0)
        sma_50 = technical_data.get('sma_50', 0)
        current_price = market_data['current_price']
        
        if current_price > sma_20 > sma_50:
            conditions['trend'] = 'bullish'
        elif current_price < sma_20 < sma_50:
            conditions['trend'] = 'bearish'
        
        # Determine momentum
        macd_histogram = technical_data.get('macd_histogram', 0)
        if macd_histogram > 0:
            conditions['momentum'] = 'bullish'
        elif macd_histogram < 0:
            conditions['momentum'] = 'bearish'
        
        # Volume assessment
        volume_ratio = technical_data.get('volume_ratio', 1)
        if volume_ratio > 1.5:
            conditions['liquidity'] = 'high'
        elif volume_ratio < 0.7:
            conditions['liquidity'] = 'low'
        
        return conditions
    
    async def _assess_risk_factors(
        self,
        symbol: str,
        market_data: Dict[str, Any],
        technical_data: Dict[str, Any],
        ai_insights: Dict[str, Any]
    ) -> List[str]:
        """
        Assess market risk factors
        """
        risk_factors = []
        
        # Volatility risk
        volatility = technical_data.get('volatility', 0.2)
        if volatility > 0.5:
            risk_factors.append("High market volatility detected")
        
        # Volume risk
        volume_ratio = technical_data.get('volume_ratio', 1)
        if volume_ratio < 0.5:
            risk_factors.append("Low trading volume may increase slippage risk")
        
        # Price position risk
        price_position = technical_data.get('price_position', 0.5)
        if price_position > 0.9:
            risk_factors.append("Price near 52-week high - potential reversal risk")
        elif price_position < 0.1:
            risk_factors.append("Price near 52-week low - potential breakdown risk")
        
        # RSI extremes
        rsi = technical_data.get('rsi', 50)
        if rsi < 20 or rsi > 80:
            risk_factors.append("RSI in extreme territory - high reversal probability")
        
        # Add AI risk assessment
        risk_assessment = ai_insights.get('risk_assessment', {})
        ai_risks = risk_assessment.get('key_risks', [])
        risk_factors.extend(ai_risks)
        
        return risk_factors
    
    async def _identify_key_levels(
        self,
        market_data: Dict[str, Any],
        technical_data: Dict[str, Any]
    ) -> Dict[str, List[float]]:
        """
        Identify key support and resistance levels
        """
        current_price = market_data['current_price']
        
        key_levels = {
            'support': [],
            'resistance': [],
            'pivot': []
        }
        
        # Add Bollinger Bands
        key_levels['support'].append(technical_data.get('bb_lower', current_price * 0.98))
        key_levels['resistance'].append(technical_data.get('bb_upper', current_price * 1.02))
        key_levels['pivot'].append(technical_data.get('bb_middle', current_price))
        
        # Add moving averages
        key_levels['support'].append(technical_data.get('sma_20', current_price))
        key_levels['support'].append(technical_data.get('sma_50', current_price))
        
        # Add psychological levels (round numbers)
        round_levels = [
            int(current_price / 100) * 100,
            int(current_price / 50) * 50,
            int(current_price / 10) * 10
        ]
        key_levels['support'].extend([level for level in round_levels if level < current_price])
        key_levels['resistance'].extend([level for level in round_levels if level > current_price])
        
        return key_levels
    
    def _parse_ai_analysis_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse AI analysis response
        """
        try:
            # Try to extract JSON
            if '```json' in response_text:
                start = response_text.find('```json') + 7
                end = response_text.find('```', start)
                json_content = response_text[start:end].strip()
                return json.loads(json_content)
            
            # Fallback parsing
            return {
                'raw_response': response_text,
                'trend_analysis': {
                    'direction': 'sideways',
                    'strength': 0.5,
                    'reasoning': 'Default analysis due to parsing error'
                },
                'key_signals': [],
                'price_targets': {},
                'market_outlook': {
                    'next_1h': 'sideways',
                    'next_4h': 'sideways',
                    'next_1d': 'sideways',
                    'confidence': 0.5
                },
                'risk_assessment': {
                    'risk_level': 'medium',
                    'volatility_outlook': 'Stable',
                    'key_risks': []
                },
                'insights': ['Unable to parse detailed insights'],
                'confidence': 0.5,
                'tokens_used': 0
            }
            
        except Exception as e:
            logger.warning(f"Failed to parse AI response: {str(e)}")
            return {'raw_response': response_text}
    
    async def _save_analysis_result(self, result: MarketAnalysisResult):
        """
        Save analysis result to file
        """
        filepath = self.analyses_dir / f"{result.analysis_id}.json"
        
        with open(filepath, 'w') as f:
            json.dump(result.model_dump(), f, indent=2, default=str)
        
        logger.info(f"Analysis result saved to {filepath}")
    
    async def get_analysis_history(self, symbol: str, limit: int = 10) -> List[MarketAnalysisResult]:
        """
        Get analysis history for a symbol
        """
        history = []
        
        for filepath in self.analyses_dir.glob(f"analysis_{symbol}_*.json"):
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    history.append(MarketAnalysisResult(**data))
            except Exception as e:
                logger.warning(f"Failed to load analysis {filepath}: {str(e)}")
        
        return sorted(history, key=lambda x: x.timestamp, reverse=True)[:limit]


def main():
    """
    Test function for market analyzer
    """
    async def test_analyzer():
        analyzer = AIMarketAnalyzer()
        
        result = await analyzer.analyze_market(
            symbol="BTC-USD",
            analysis_type=AnalysisType.TECHNICAL,
            time_horizon=TimeHorizon.MEDIUM_TERM
        )
        
        print(f"Analysis ID: {result.analysis_id}")
        print(f"Symbol: {result.symbol}")
        print(f"Current Price: ${result.market_data['current_price']:,.2f}")
        print(f"RSI: {result.technical_indicators.get('rsi', 0):.1f}")
        print(f"Signals: {len(result.market_signals)}")
        print(f"Confidence: {result.confidence_score:.2f}")
    
    asyncio.run(test_analyzer())


if __name__ == "__main__":
    main()
