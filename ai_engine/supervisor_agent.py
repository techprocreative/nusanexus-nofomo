"""
NusaNexus NoFOMO - AI Supervisor Agent
Bot performance monitoring and supervision system
"""

import os
import asyncio
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
from openai import OpenAI
import structlog
from pathlib import Path
from enum import Enum

# Configure logging
logger = structlog.get_logger(__name__)


class BotStatus(str, Enum):
    STOPPED = "stopped"
    RUNNING = "running"
    ERROR = "error"
    PAUSED = "paused"
    MONITORING = "monitoring"


class AlertLevel(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class SupervisionAction(str, Enum):
    NONE = "none"
    NOTIFY = "notify"
    PAUSE = "pause"
    STOP = "stop"
    ADJUST_RISK = "adjust_risk"
    RESTART = "restart"


class BotMetrics(BaseModel):
    """Bot performance metrics"""
    bot_id: str
    current_balance: float
    initial_balance: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_profit: float
    profit_percentage: float
    max_drawdown: float
    sharpe_ratio: Optional[float] = None
    profit_factor: Optional[float] = None
    avg_trade_duration: Optional[float] = None
    last_trade_time: Optional[datetime] = None
    consecutive_losses: int = 0
    current_streak: int = 0


class BotAlert(BaseModel):
    """Bot alert model"""
    alert_id: str
    bot_id: str
    level: AlertLevel
    action: SupervisionAction
    message: str
    description: str
    metrics: Dict[str, Any]
    recommended_actions: List[str]
    created_at: datetime
    is_acknowledged: bool = False
    resolved_at: Optional[datetime] = None


class SupervisionReport(BaseModel):
    """Bot supervision report"""
    report_id: str
    bot_id: str
    analysis_type: str  # "performance", "risk", "behavior"
    report_time: datetime
    period_start: datetime
    period_end: datetime
    metrics: BotMetrics
    risk_assessment: Dict[str, Any]
    recommendations: List[str]
    alerts: List[BotAlert]
    performance_score: float
    risk_score: float
    overall_health: str
    next_review_time: datetime


class SupervisorAgent:
    """
    AI-powered bot supervision and monitoring agent
    """
    
    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv('OPENROUTER_API_KEY'),
            base_url=os.getenv('OPENROUTER_BASE_URL', 'https://openrouter.ai/api/v1')
        )
        self.reports_dir = Path('supervisor_reports')
        self.reports_dir.mkdir(exist_ok=True)
        self.alerts_dir = Path('bot_alerts')
        self.alerts_dir.mkdir(exist_ok=True)
        self.monitoring_interval = 60  # seconds
        self.active_monitors = set()
        
    async def start_monitoring(self, bot_id: str):
        """
        Start monitoring a bot
        """
        if bot_id not in self.active_monitors:
            self.active_monitors.add(bot_id)
            logger.info(f"Started monitoring bot {bot_id}")
            
            # Start monitoring task
            asyncio.create_task(self._monitor_bot(bot_id))
    
    async def stop_monitoring(self, bot_id: str):
        """
        Stop monitoring a bot
        """
        if bot_id in self.active_monitors:
            self.active_monitors.remove(bot_id)
            logger.info(f"Stopped monitoring bot {bot_id}")
    
    async def analyze_bot_performance(
        self,
        bot_id: str,
        analysis_type: str = "comprehensive"
    ) -> SupervisionReport:
        """
        Perform comprehensive bot performance analysis
        """
        try:
            logger.info(f"Starting performance analysis for bot {bot_id}")
            
            # Step 1: Collect bot data
            bot_data = await self._collect_bot_data(bot_id)
            
            # Step 2: Calculate metrics
            metrics = await self._calculate_bot_metrics(bot_data)
            
            # Step 3: Risk assessment
            risk_assessment = await self._assess_risk(bot_id, metrics, bot_data)
            
            # Step 4: Generate alerts
            alerts = await self._generate_alerts(bot_id, metrics, risk_assessment)
            
            # Step 5: AI-powered analysis
            ai_analysis = await self._analyze_with_ai(
                bot_id, metrics, risk_assessment, analysis_type
            )
            
            # Step 6: Generate recommendations
            recommendations = await self._generate_recommendations(
                bot_id, metrics, risk_assessment, ai_analysis
            )
            
            # Step 7: Calculate scores
            performance_score = self._calculate_performance_score(metrics)
            risk_score = self._calculate_risk_score(risk_assessment)
            overall_health = self._determine_overall_health(performance_score, risk_score)
            
            # Create report
            report = SupervisionReport(
                report_id=f"report_{bot_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                bot_id=bot_id,
                analysis_type=analysis_type,
                report_time=datetime.now(),
                period_start=datetime.now() - timedelta(days=30),
                period_end=datetime.now(),
                metrics=metrics,
                risk_assessment=risk_assessment,
                recommendations=recommendations,
                alerts=alerts,
                performance_score=performance_score,
                risk_score=risk_score,
                overall_health=overall_health,
                next_review_time=datetime.now() + timedelta(hours=4)
            )
            
            # Save report
            await self._save_report(report)
            
            # Save alerts
            for alert in alerts:
                await self._save_alert(alert)
            
            logger.info(f"Performance analysis completed for bot {bot_id}")
            return report
            
        except Exception as e:
            logger.error(f"Bot performance analysis failed: {str(e)}")
            raise
    
    async def get_bot_alerts(
        self,
        bot_id: str,
        level: Optional[AlertLevel] = None,
        acknowledged: bool = False,
        limit: int = 50
    ) -> List[BotAlert]:
        """
        Get bot alerts
        """
        alerts = []
        
        for filepath in self.alerts_dir.glob(f"alert_{bot_id}_*.json"):
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    alert = BotAlert(**data)
                    
                    # Filter by level if specified
                    if level and alert.level != level:
                        continue
                    
                    # Filter by acknowledgment status
                    if not acknowledged and alert.is_acknowledged:
                        continue
                    
                    alerts.append(alert)
            except Exception as e:
                logger.warning(f"Failed to load alert {filepath}: {str(e)}")
        
        # Sort by creation time and return limit
        alerts.sort(key=lambda x: x.created_at, reverse=True)
        return alerts[:limit]
    
    async def acknowledge_alert(self, alert_id: str) -> bool:
        """
        Acknowledge an alert
        """
        try:
            # Find alert file
            for filepath in self.alerts_dir.glob("alert_*.json"):
                if alert_id in filepath.name:
                    with open(filepath, 'r') as f:
                        data = json.load(f)
                    
                    data['is_acknowledged'] = True
                    
                    with open(filepath, 'w') as f:
                        json.dump(data, f, indent=2, default=str)
                    
                    return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to acknowledge alert {alert_id}: {str(e)}")
            return False
    
    async def get_supervision_history(
        self,
        bot_id: str,
        limit: int = 20
    ) -> List[SupervisionReport]:
        """
        Get supervision history for a bot
        """
        reports = []
        
        for filepath in self.reports_dir.glob(f"report_{bot_id}_*.json"):
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    reports.append(SupervisionReport(**data))
            except Exception as e:
                logger.warning(f"Failed to load report {filepath}: {str(e)}")
        
        # Sort by report time and return limit
        reports.sort(key=lambda x: x.report_time, reverse=True)
        return reports[:limit]
    
    async def _monitor_bot(self, bot_id: str):
        """
        Continuous monitoring task for a bot
        """
        while bot_id in self.active_monitors:
            try:
                # Perform real-time monitoring
                report = await self.analyze_bot_performance(bot_id, "realtime")
                
                # Check for critical alerts
                critical_alerts = [alert for alert in report.alerts if alert.level == AlertLevel.CRITICAL]
                if critical_alerts:
                    await self._handle_critical_alerts(bot_id, critical_alerts)
                
                # Sleep before next check
                await asyncio.sleep(self.monitoring_interval)
                
            except Exception as e:
                logger.error(f"Monitoring error for bot {bot_id}: {str(e)}")
                await asyncio.sleep(30)  # Wait 30 seconds before retry
    
    async def _collect_bot_data(self, bot_id: str) -> Dict[str, Any]:
        """
        Collect bot trading data
        """
        # Mock data - in production, this would fetch from database
        return {
            "bot_id": bot_id,
            "status": BotStatus.RUNNING,
            "initial_balance": 10000.0,
            "current_balance": 10850.50,
            "trades": [
                {
                    "id": "trade_1",
                    "side": "buy",
                    "amount": 100.0,
                    "price": 50000.0,
                    "timestamp": datetime.now() - timedelta(hours=2),
                    "profit": 25.50,
                    "profit_pct": 0.51
                },
                {
                    "id": "trade_2",
                    "side": "sell",
                    "amount": 50.0,
                    "price": 51000.0,
                    "timestamp": datetime.now() - timedelta(hours=1),
                    "profit": -12.30,
                    "profit_pct": -0.25
                }
            ],
            "settings": {
                "max_drawdown": 0.15,
                "stop_loss": 0.02,
                "take_profit": 0.04,
                "max_position_size": 0.1
            }
        }
    
    async def _calculate_bot_metrics(self, bot_data: Dict[str, Any]) -> BotMetrics:
        """
        Calculate bot performance metrics
        """
        trades = bot_data.get('trades', [])
        
        if not trades:
            return BotMetrics(
                bot_id=bot_data['bot_id'],
                current_balance=bot_data['current_balance'],
                initial_balance=bot_data['initial_balance'],
                total_trades=0,
                winning_trades=0,
                losing_trades=0,
                win_rate=0.0,
                total_profit=0.0,
                profit_percentage=0.0,
                max_drawdown=0.0
            )
        
        # Calculate basic metrics
        total_trades = len(trades)
        winning_trades = sum(1 for trade in trades if trade.get('profit', 0) > 0)
        losing_trades = total_trades - winning_trades
        win_rate = winning_trades / total_trades if total_trades > 0 else 0.0
        
        total_profit = sum(trade.get('profit', 0) for trade in trades)
        profit_percentage = (total_profit / bot_data['initial_balance']) * 100
        
        # Calculate maximum drawdown
        balance_progression = [bot_data['initial_balance']]
        current_balance = bot_data['initial_balance']
        
        for trade in trades:
            current_balance += trade.get('profit', 0)
            balance_progression.append(current_balance)
        
        max_drawdown = 0.0
        peak = balance_progression[0]
        for balance in balance_progression:
            if balance > peak:
                peak = balance
            drawdown = (peak - balance) / peak
            max_drawdown = max(max_drawdown, drawdown)
        
        # Calculate consecutive losses
        consecutive_losses = 0
        current_streak = 0
        for trade in reversed(trades):
            if trade.get('profit', 0) < 0:
                consecutive_losses += 1
                current_streak += 1
            else:
                break
        
        return BotMetrics(
            bot_id=bot_data['bot_id'],
            current_balance=bot_data['current_balance'],
            initial_balance=bot_data['initial_balance'],
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            total_profit=total_profit,
            profit_percentage=profit_percentage,
            max_drawdown=max_drawdown,
            last_trade_time=max(trade.get('timestamp', datetime.min) for trade in trades),
            consecutive_losses=consecutive_losses,
            current_streak=current_streak
        )
    
    async def _assess_risk(
        self,
        bot_id: str,
        metrics: BotMetrics,
        bot_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Assess bot risk profile
        """
        risk_assessment = {
            "overall_risk_level": "medium",
            "risk_factors": [],
            "drawdown_risk": "low",
            "volatility_risk": "medium",
            "concentration_risk": "low",
            "operational_risk": "low"
        }
        
        # Drawdown assessment
        if metrics.max_drawdown > 0.2:
            risk_assessment["drawdown_risk"] = "high"
            risk_assessment["risk_factors"].append("High maximum drawdown detected")
        elif metrics.max_drawdown > 0.1:
            risk_assessment["drawdown_risk"] = "medium"
            risk_assessment["risk_factors"].append("Moderate drawdown levels")
        
        # Consecutive losses assessment
        if metrics.consecutive_losses > 5:
            risk_assessment["risk_factors"].append("Long losing streak detected")
        
        # Win rate assessment
        if metrics.win_rate < 0.3:
            risk_assessment["risk_factors"].append("Low win rate indicates strategy issues")
        elif metrics.win_rate > 0.8:
            risk_assessment["risk_factors"].append("Very high win rate - potential overfitting")
        
        # Determine overall risk level
        high_risk_factors = len([f for f in risk_assessment["risk_factors"] if "high" in f.lower()])
        if high_risk_factors > 0:
            risk_assessment["overall_risk_level"] = "high"
        elif len(risk_assessment["risk_factors"]) > 2:
            risk_assessment["overall_risk_level"] = "medium"
        else:
            risk_assessment["overall_risk_level"] = "low"
        
        return risk_assessment
    
    async def _generate_alerts(
        self,
        bot_id: str,
        metrics: BotMetrics,
        risk_assessment: Dict[str, Any]
    ) -> List[BotAlert]:
        """
        Generate alerts based on metrics and risk assessment
        """
        alerts = []
        
        # Profit/Loss alerts
        if metrics.profit_percentage < -10:
            alerts.append(BotAlert(
                alert_id=f"alert_{bot_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_loss",
                bot_id=bot_id,
                level=AlertLevel.WARNING,
                action=SupervisionAction.ADJUST_RISK,
                message="Significant losses detected",
                description=f"Bot has lost {abs(metrics.profit_percentage):.1f}% of initial balance",
                metrics={"profit_percentage": metrics.profit_percentage, "total_loss": metrics.total_profit},
                recommended_actions=["Reduce position size", "Review strategy parameters", "Consider stopping bot"],
                created_at=datetime.now()
            ))
        
        # Drawdown alerts
        if metrics.max_drawdown > 0.15:
            alerts.append(BotAlert(
                alert_id=f"alert_{bot_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_drawdown",
                bot_id=bot_id,
                level=AlertLevel.CRITICAL,
                action=SupervisionAction.PAUSE,
                message="Excessive drawdown detected",
                description=f"Maximum drawdown reached {metrics.max_drawdown:.1%}",
                metrics={"max_drawdown": metrics.max_drawdown},
                recommended_actions=["Pause bot immediately", "Review risk management", "Adjust parameters"],
                created_at=datetime.now()
            ))
        
        # Consecutive losses alert
        if metrics.consecutive_losses > 5:
            alerts.append(BotAlert(
                alert_id=f"alert_{bot_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_streak",
                bot_id=bot_id,
                level=AlertLevel.WARNING,
                action=SupervisionAction.NOTIFY,
                message="Long losing streak",
                description=f"Bot has {metrics.consecutive_losses} consecutive losing trades",
                metrics={"consecutive_losses": metrics.consecutive_losses},
                recommended_actions=["Monitor closely", "Review market conditions", "Check strategy validity"],
                created_at=datetime.now()
            ))
        
        # Low win rate alert
        if metrics.win_rate < 0.25 and metrics.total_trades > 10:
            alerts.append(BotAlert(
                alert_id=f"alert_{bot_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_winrate",
                bot_id=bot_id,
                level=AlertLevel.WARNING,
                action=SupervisionAction.ADJUST_RISK,
                message="Low win rate detected",
                description=f"Win rate is {metrics.win_rate:.1%} with {metrics.total_trades} trades",
                metrics={"win_rate": metrics.win_rate, "total_trades": metrics.total_trades},
                recommended_actions=["Review entry conditions", "Optimize parameters", "Consider strategy change"],
                created_at=datetime.now()
            ))
        
        return alerts
    
    async def _analyze_with_ai(
        self,
        bot_id: str,
        metrics: BotMetrics,
        risk_assessment: Dict[str, Any],
        analysis_type: str
    ) -> Dict[str, Any]:
        """
        Use AI to analyze bot performance
        """
        system_prompt = """
        Anda adalah ahli analisis performa trading bot dan risk management.
        Analisis metrik bot dan berikan insight yang actionable.
        
        Guidelines:
        - Fokus pada performance patterns dan anomalies
        - Berikan assessment objektif
        - Identifikasi areas for improvement
        - Berikan recommendations yang specific
        - Pertimbangkan risk management
        """
        
        user_prompt = f"""
        Analisis performa bot trading berikut:
        
        Bot ID: {bot_id}
        Analysis Type: {analysis_type}
        
        Metrics:
        - Total Trades: {metrics.total_trades}
        - Win Rate: {metrics.win_rate:.2%}
        - Profit: {metrics.total_profit:.2f} ({metrics.profit_percentage:.2f}%)
        - Max Drawdown: {metrics.max_drawdown:.2%}
        - Current Balance: ${metrics.current_balance:.2f}
        - Consecutive Losses: {metrics.consecutive_losses}
        
        Risk Assessment:
        {json.dumps(risk_assessment, indent=2)}
        
        Berikan analisis dalam format JSON:
        {{
            "performance_analysis": {{
                "overall_rating": "excellent|good|fair|poor",
                "strengths": ["list kekuatan"],
                "weaknesses": ["list kelemahan"],
                "key_insights": ["list insight penting"]
            }},
            "pattern_recognition": {{
                "trading_patterns": ["identifikasi pattern"],
                "anomalies": ["identifikasi anomaly"],
                "trends": ["identifikasi trend"]
            }},
            "recommendations": {{
                "immediate_actions": ["aksi segera"],
                "optimization_suggestions": ["saran optimasi"],
                "risk_adjustments": ["penyesuaian risiko"]
            }},
            "confidence": 0.0-1.0
        }}
        """
        
        try:
            response = self.client.chat.completions.create(
                model=os.getenv('OPENROUTER_MODEL', 'anthropic/claude-3-sonnet'),
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            content = response.choices[0].message.content
            if '```json' in content:
                start = content.find('```json') + 7
                end = content.find('```', start)
                json_content = content[start:end].strip()
                return json.loads(json_content)
            
            return {"raw_response": content}
            
        except Exception as e:
            logger.error(f"AI analysis failed: {str(e)}")
            return {"error": str(e)}
    
    async def _generate_recommendations(
        self,
        bot_id: str,
        metrics: BotMetrics,
        risk_assessment: Dict[str, Any],
        ai_analysis: Dict[str, Any]
    ) -> List[str]:
        """
        Generate recommendations based on analysis
        """
        recommendations = []
        
        # Add AI recommendations
        rec_data = ai_analysis.get('recommendations', {})
        recommendations.extend(rec_data.get('immediate_actions', []))
        recommendations.extend(rec_data.get('optimization_suggestions', []))
        recommendations.extend(rec_data.get('risk_adjustments', []))
        
        # Add metric-based recommendations
        if metrics.win_rate < 0.4:
            recommendations.append("Consider tightening entry conditions to improve win rate")
        
        if metrics.max_drawdown > 0.1:
            recommendations.append("Reduce position sizes to lower drawdown risk")
        
        if metrics.consecutive_losses > 3:
            recommendations.append("Monitor market conditions - extended losing streaks detected")
        
        # Add risk-based recommendations
        if risk_assessment["overall_risk_level"] == "high":
            recommendations.append("Immediate risk reduction required - consider stopping the bot")
        elif risk_assessment["overall_risk_level"] == "medium":
            recommendations.append("Review and adjust risk parameters")
        
        return recommendations[:10]  # Limit to 10 recommendations
    
    def _calculate_performance_score(self, metrics: BotMetrics) -> float:
        """
        Calculate bot performance score (0-1)
        """
        score = 0.5  # Base score
        
        # Profit component (40% weight)
        if metrics.profit_percentage > 0:
            profit_score = min(1.0, metrics.profit_percentage / 20)  # 20% = perfect
        else:
            profit_score = 0.0
        score += profit_score * 0.4
        
        # Win rate component (30% weight)
        win_rate_score = metrics.win_rate
        score += win_rate_score * 0.3
        
        # Drawdown component (20% weight)
        if metrics.max_drawdown < 0.05:
            drawdown_score = 1.0
        elif metrics.max_drawdown < 0.1:
            drawdown_score = 0.8
        elif metrics.max_drawdown < 0.2:
            drawdown_score = 0.5
        else:
            drawdown_score = 0.2
        score += drawdown_score * 0.2
        
        # Consistency component (10% weight)
        consistency_score = 1.0 if metrics.consecutive_losses < 3 else max(0.3, 1.0 - metrics.consecutive_losses * 0.1)
        score += consistency_score * 0.1
        
        return min(1.0, max(0.0, score))
    
    def _calculate_risk_score(self, risk_assessment: Dict[str, Any]) -> float:
        """
        Calculate bot risk score (0-1, higher is safer)
        """
        risk_level = risk_assessment.get("overall_risk_level", "medium")
        
        if risk_level == "low":
            return 0.9
        elif risk_level == "medium":
            return 0.6
        else:  # high
            return 0.3
    
    def _determine_overall_health(
        self,
        performance_score: float,
        risk_score: float
    ) -> str:
        """
        Determine overall bot health
        """
        combined_score = (performance_score + risk_score) / 2
        
        if combined_score >= 0.8:
            return "excellent"
        elif combined_score >= 0.6:
            return "good"
        elif combined_score >= 0.4:
            return "fair"
        else:
            return "poor"
    
    async def _handle_critical_alerts(self, bot_id: str, alerts: List[BotAlert]):
        """
        Handle critical alerts
        """
        for alert in alerts:
            if alert.action == SupervisionAction.STOP:
                logger.critical(f"CRITICAL: Stopping bot {bot_id} due to {alert.message}")
                # In production, this would send stop signal to bot
            elif alert.action == SupervisionAction.PAUSE:
                logger.warning(f"WARNING: Pausing bot {bot_id} due to {alert.message}")
                # In production, this would send pause signal to bot
    
    async def _save_report(self, report: SupervisionReport):
        """
        Save supervision report
        """
        try:
            filepath = self.reports_dir / f"{report.report_id}.json"
            with open(filepath, 'w') as f:
                json.dump(report.model_dump(), f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save report {report.report_id}: {str(e)}")
    
    async def _save_alert(self, alert: BotAlert):
        """
        Save alert
        """
        try:
            filepath = self.alerts_dir / f"{alert.alert_id}.json"
            with open(filepath, 'w') as f:
                json.dump(alert.model_dump(), f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save alert {alert.alert_id}: {str(e)}")


def main():
    """
    Test function for supervisor agent
    """
    async def test_supervisor():
        supervisor = SupervisorAgent()
        
        # Test performance analysis
        report = await supervisor.analyze_bot_performance(
            bot_id="test_bot_001",
            analysis_type="comprehensive"
        )
        
        print(f"Report ID: {report.report_id}")
        print(f"Bot ID: {report.bot_id}")
        print(f"Performance Score: {report.performance_score:.2f}")
        print(f"Risk Score: {report.risk_score:.2f}")
        print(f"Overall Health: {report.overall_health}")
        print(f"Alerts: {len(report.alerts)}")
        print(f"Recommendations: {report.recommendations}")
    
    asyncio.run(test_supervisor())


if __name__ == "__main__":
    main()
