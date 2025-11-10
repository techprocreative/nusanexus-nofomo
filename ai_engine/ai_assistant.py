"""
NusaNexus NoFOMO - AI Assistant
Chat interface and intelligent insights for trading
"""

import os
import asyncio
import json
from typing import Any, Dict, List, Optional, cast
from datetime import datetime, timedelta
import uuid
from pydantic import BaseModel, Field
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam
import structlog
from pathlib import Path
from enum import Enum

# Configure logging
logger = structlog.get_logger(__name__)


class ChatContextType(str, Enum):
    GENERAL = "general"
    STRATEGY = "strategy"
    MARKET = "market"
    RISK = "risk"
    PERFORMANCE = "performance"
    EDUCATION = "education"


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatMessage(BaseModel):
    """Chat message model"""
    id: str
    role: MessageRole
    content: str
    timestamp: datetime
    context_type: ChatContextType
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ChatSession(BaseModel):
    """Chat session model"""
    session_id: str
    user_id: str
    title: str
    context_type: ChatContextType
    messages: List[ChatMessage] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    is_active: bool = True
    summary: Optional[str] = None


class AIResponse(BaseModel):
    """AI response model"""
    message_id: str
    content: str
    confidence: float
    suggestions: List[str] = Field(default_factory=list)
    insights: List[str] = Field(default_factory=list)
    actions: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AIInsight(BaseModel):
    """AI insight model"""
    id: str
    user_id: str
    insight_type: str
    title: str
    description: str
    priority: int = 1  # 1-5, 5 being highest
    category: str
    related_data: Dict[str, Any] = {}
    is_read: bool = False
    created_at: datetime
    expires_at: Optional[datetime] = None


class AIAssistant:
    """
    AI-powered trading assistant with chat interface
    """
    
    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv('OPENROUTER_API_KEY'),
            base_url=os.getenv('OPENROUTER_BASE_URL', 'https://openrouter.ai/api/v1')
        )
        self.sessions_dir = Path('chat_sessions')
        self.sessions_dir.mkdir(exist_ok=True)
        self.insights_dir = Path('insights')
        self.insights_dir.mkdir(exist_ok=True)
        
        # Initialize system prompts for different contexts
        self.system_prompts = {
            ChatContextType.GENERAL: self._get_general_prompt(),
            ChatContextType.STRATEGY: self._get_strategy_prompt(),
            ChatContextType.MARKET: self._get_market_prompt(),
            ChatContextType.RISK: self._get_risk_prompt(),
            ChatContextType.PERFORMANCE: self._get_performance_prompt(),
            ChatContextType.EDUCATION: self._get_education_prompt()
        }
    
    async def chat(
        self,
        user_id: str,
        message: str,
        context_type: ChatContextType = ChatContextType.GENERAL,
        session_id: Optional[str] = None,
        context_data: Optional[Dict[str, Any]] = None
    ) -> AIResponse:
        """
        Handle chat interaction with AI assistant
        """
        try:
            # Get or create session
            session: Optional[ChatSession]
            if session_id:
                session = await self._load_session(session_id)
                if session is None:
                    session = await self._create_session(user_id, context_type, message)
            else:
                session = await self._create_session(user_id, context_type, message)
            
            # At this point session is guaranteed
            assert session is not None

            # Add user message to session
            user_message = ChatMessage(
                id=str(uuid.uuid4()),
                role=MessageRole.USER,
                content=message,
                timestamp=datetime.now(),
                context_type=context_type,
                metadata=context_data or {}
            )
            session.messages.append(user_message)
            
            # Generate AI response
            ai_response = await self._generate_response(
                session, context_data or {}
            )
            
            # Add AI response to session
            assistant_message = ChatMessage(
                id=str(uuid.uuid4()),
                role=MessageRole.ASSISTANT,
                content=ai_response.content,
                timestamp=datetime.now(),
                context_type=context_type,
                metadata=ai_response.metadata
            )
            session.messages.append(assistant_message)
            session.updated_at = datetime.now()
            
            # Update session title if it's the first exchange
            if len(session.messages) <= 2:
                session.title = self._generate_session_title(message)
            
            # Generate insights if applicable
            await self._generate_insights(session, user_id)
            
            # Save session
            await self._save_session(session)
            
            return ai_response
            
        except Exception as e:
            logger.error(f"Chat failed: {str(e)}")
            # Return fallback response
            return AIResponse(
                message_id=str(uuid.uuid4()),
                content="I apologize, but I'm having trouble processing your request right now. Please try again in a moment.",
                confidence=0.1,
                suggestions=["Try rephrasing your question", "Check your internet connection"],
                metadata={"error": str(e)}
            )
    
    async def get_session(self, session_id: str) -> Optional[ChatSession]:
        """
        Get chat session by ID
        """
        return await self._load_session(session_id)
    
    async def list_sessions(
        self,
        user_id: str,
        context_type: Optional[ChatContextType] = None,
        limit: int = 20
    ) -> List[ChatSession]:
        """
        List chat sessions for a user
        """
        sessions = []
        
        for filepath in self.sessions_dir.glob(f"session_{user_id}_*.json"):
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    session = ChatSession(**data)
                    
                    # Filter by context type if specified
                    if context_type is None or session.context_type == context_type:
                        sessions.append(session)
            except Exception as e:
                logger.warning(f"Failed to load session {filepath}: {str(e)}")
        
        # Sort by updated_at and return limit
        sessions.sort(key=lambda x: x.updated_at, reverse=True)
        return sessions[:limit]
    
    async def delete_session(self, session_id: str) -> bool:
        """
        Delete a chat session
        """
        try:
            filepath = self.sessions_dir / f"{session_id}.json"
            if filepath.exists():
                filepath.unlink()
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {str(e)}")
            return False
    
    async def get_insights(
        self,
        user_id: str,
        insight_type: Optional[str] = None,
        unread_only: bool = False,
        limit: int = 10
    ) -> List[AIInsight]:
        """
        Get AI insights for a user
        """
        insights = []
        
        for filepath in self.insights_dir.glob(f"insight_{user_id}_*.json"):
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    insight = AIInsight(**data)
                    
                    # Filter by type if specified
                    if insight_type and insight.insight_type != insight_type:
                        continue
                    
                    # Filter unread if requested
                    if unread_only and insight.is_read:
                        continue
                    
                    insights.append(insight)
            except Exception as e:
                logger.warning(f"Failed to load insight {filepath}: {str(e)}")
        
        # Sort by priority and created_at
        insights.sort(key=lambda x: (x.priority, x.created_at), reverse=True)
        return insights[:limit]
    
    async def mark_insight_read(self, insight_id: str) -> bool:
        """
        Mark an insight as read
        """
        try:
            # Find insight file
            for filepath in self.insights_dir.glob("insight_*.json"):
                if insight_id in filepath.name:
                    with open(filepath, 'r') as f:
                        data = json.load(f)
                    
                    data['is_read'] = True
                    
                    with open(filepath, 'w') as f:
                        json.dump(data, f, indent=2, default=str)
                    
                    return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to mark insight {insight_id} as read: {str(e)}")
            return False
    
    async def _generate_response(
        self,
        session: ChatSession,
        context_data: Dict[str, Any]
    ) -> AIResponse:
        """
        Generate AI response based on session context
        """
        # Prepare conversation history
        messages: List[ChatCompletionMessageParam] = [
            self._chat_param("system", self.system_prompts[session.context_type])
        ]
        
        # Add recent conversation history (last 10 messages)
        recent_messages = session.messages[-10:]
        for msg in recent_messages:
            role = "user" if msg.role == MessageRole.USER else "assistant"
            messages.append(self._chat_param(role, msg.content))
        
        # Add context data if available
        if context_data:
            context_info = json.dumps(context_data, indent=2)
            messages.append(self._chat_param("system", f"Context Data: {context_info}"))
        
        # Generate response
        response = self.client.chat.completions.create(
            model=os.getenv('OPENROUTER_MODEL', 'anthropic/claude-3-sonnet'),
            messages=messages,
            temperature=0.7,
            max_tokens=1500
        )
        
        content = response.choices[0].message.content or ""
        
        # Parse response for suggestions and actions
        suggestions = self._extract_suggestions(content)
        insights = self._extract_insights(content)
        actions = self._extract_actions(content)
        
        usage = response.usage
        tokens_used = usage.total_tokens if usage and usage.total_tokens is not None else 0

        return AIResponse(
            message_id=str(uuid.uuid4()),
            content=content,
            confidence=0.8,  # Could be calculated based on response quality
            suggestions=suggestions,
            insights=insights,
            actions=actions,
            metadata={
                "model_used": os.getenv('OPENROUTER_MODEL', 'anthropic/claude-3-sonnet'),
                "tokens_used": tokens_used,
                "context_type": session.context_type
            }
        )
    
    async def _create_session(
        self,
        user_id: str,
        context_type: ChatContextType,
        first_message: str
    ) -> ChatSession:
        """
        Create a new chat session
        """
        session_id = f"session_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        return ChatSession(
            session_id=session_id,
            user_id=user_id,
            title=self._generate_session_title(first_message),
            context_type=context_type,
            messages=[],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    async def _load_session(self, session_id: str) -> Optional[ChatSession]:
        """
        Load session from file
        """
        try:
            filepath = self.sessions_dir / f"{session_id}.json"
            if filepath.exists():
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    return ChatSession(**data)
        except Exception as e:
            logger.error(f"Failed to load session {session_id}: {str(e)}")
        return None
    
    async def _save_session(self, session: ChatSession):
        """
        Save session to file
        """
        try:
            filepath = self.sessions_dir / f"{session.session_id}.json"
            with open(filepath, 'w') as f:
                json.dump(session.model_dump(), f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save session {session.session_id}: {str(e)}")
    
    async def _generate_insights(self, session: ChatSession, user_id: str):
        """
        Generate AI insights based on conversation
        """
        try:
            # Only generate insights for strategy and performance contexts
            if session.context_type not in [ChatContextType.STRATEGY, ChatContextType.PERFORMANCE]:
                return
            
            # Extract key points from conversation
            conversation_text = "\n".join([msg.content for msg in session.messages])
            
            if len(conversation_text) < 100:  # Too short for insights
                return
            
            # Generate insight
            insight = await self._analyze_conversation_for_insights(
                conversation_text, session.context_type, user_id
            )
            
            if insight:
                await self._save_insight(insight)
            
        except Exception as e:
            logger.error(f"Failed to generate insights: {str(e)}")
    
    async def _analyze_conversation_for_insights(
        self,
        conversation_text: str,
        context_type: ChatContextType,
        user_id: str
    ) -> Optional[AIInsight]:
        """
        Analyze conversation and extract insights
        """
        system_prompt = """
        Anda adalah analis AI yang specialize dalam mengekstrak insights penting dari conversation trading.
        Identifikasi patterns, opportunities, dan recommendations dari conversation.
        """
        
        user_prompt = f"""
        Analisis conversation berikut dan identifikasi insights penting:
        
        Context: {context_type.value}
        Conversation:
        {conversation_text}
        
        Berikan insight dalam format JSON:
        {{
            "insight_type": "pattern|opportunity|warning|recommendation",
            "title": "Judul insight yang menarik",
            "description": "Penjelasan detail insight",
            "priority": 1-5,
            "category": "kategori insight"
        }}
        """
        
        try:
            response = self.client.chat.completions.create(
                model=os.getenv('OPENROUTER_MODEL', 'anthropic/claude-3-sonnet'),
                messages=[
                    self._chat_param("system", system_prompt),
                    self._chat_param("user", user_prompt)
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            # Parse response
            content = response.choices[0].message.content or ""
            if '```json' in content:
                start = content.find('```json') + 7
                end = content.find('```', start)
                json_content = content[start:end].strip()
                insight_data = json.loads(json_content)
                
                return AIInsight(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    insight_type=insight_data.get('insight_type', 'general'),
                    title=insight_data.get('title', 'Trading Insight'),
                    description=insight_data.get('description', ''),
                    priority=insight_data.get('priority', 3),
                    category=insight_data.get('category', 'general'),
                    created_at=datetime.now(),
                    expires_at=datetime.now() + timedelta(days=7)  # Expires in 7 days
                )
        except Exception as e:
            logger.error(f"Failed to parse insight response: {str(e)}")
        
        return None
    
    async def _save_insight(self, insight: AIInsight):
        """
        Save insight to file
        """
        try:
            filepath = self.insights_dir / f"insight_{insight.user_id}_{insight.id}.json"
            with open(filepath, 'w') as f:
                json.dump(insight.model_dump(), f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save insight {insight.id}: {str(e)}")
    
    def _generate_session_title(self, first_message: str) -> str:
        """
        Generate a title for the chat session
        """
        # Simple title generation - take first few words
        words = first_message.strip().split()[:5]
        title = " ".join(words)
        
        # Clean up title
        if len(title) > 50:
            title = title[:47] + "..."
        
        return title or "New Chat"
    
    def _extract_suggestions(self, content: Optional[str]) -> List[str]:
        """
        Extract suggestions from AI response
        """
        if not content:
            return []
        suggestions = []
        
        # Look for suggestion patterns
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith(('•', '-', '*', '→')) or 'suggestion' in line.lower():
                cleaned = line.lstrip('•-*→').strip()
                if cleaned and len(cleaned) > 10:  # Reasonable suggestion length
                    suggestions.append(cleaned)
        
        return suggestions[:5]  # Limit to 5 suggestions
    
    def _extract_insights(self, content: Optional[str]) -> List[str]:
        """
        Extract insights from AI response
        """
        if not content:
            return []
        insights = []
        
        # Look for insight patterns
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if any(keyword in line.lower() for keyword in ['insight', 'key point', 'important', 'note']):
                cleaned = line.replace('•', '').replace('-', '').strip()
                if cleaned and len(cleaned) > 15:
                    insights.append(cleaned)
        
        return insights[:3]  # Limit to 3 insights
    
    def _extract_actions(self, content: Optional[str]) -> List[Dict[str, Any]]:
        """
        Extract actionable items from AI response
        """
        if not content:
            return []
        actions = []
        
        # Look for action patterns
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if any(keyword in line.lower() for keyword in ['action', 'next step', 'do this', 'try this']):
                actions.append({
                    "description": line,
                    "type": "suggested_action",
                    "priority": "medium"
                })
        
        return actions[:3]  # Limit to 3 actions
    
    def _chat_param(self, role: str, content: str) -> ChatCompletionMessageParam:
        """
        Helper to build typed chat completion message params.
        """
        return cast(ChatCompletionMessageParam, {"role": role, "content": content})
    
    def _get_general_prompt(self) -> str:
        """
        Get system prompt for general chat
        """
        return """
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
        """
    
    def _get_strategy_prompt(self) -> str:
        """
        Get system prompt for strategy discussions
        """
        return """
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
        """
    
    def _get_market_prompt(self) -> str:
        """
        Get system prompt for market analysis
        """
        return """
        Anda adalah analis pasar cryptocurrency dengan expertise dalam:
        - Technical analysis dan chart patterns
        - Market sentiment analysis
        - Price action dan volume analysis
        - Support/resistance identification
        - Trend analysis dan momentum
        
        Kemampuan:
        - Interpretasi technical indicators
        - Market structure analysis
        - Risk assessment
        - Entry/exit timing recommendations
        - Market timing strategies
        
        Selalu berikan:
        - Multiple timeframe analysis
        - Risk management considerations
        - Market context dan conditions
        - Confidence levels untuk predictions
        """
    
    def _get_risk_prompt(self) -> str:
        """
        Get system prompt for risk management
        """
        return """
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
        """
    
    def _get_performance_prompt(self) -> str:
        """
        Get system prompt for performance analysis
        """
        return """
        Anda adalah performance analyst dengan expertise dalam:
        - Trading metrics interpretation
        - Strategy performance evaluation
        - Profit/loss analysis
        - Risk-adjusted returns
        - Comparative analysis
        
        Metrik yang analisis:
        - Win rate dan profit factor
        - Maximum drawdown
        - Sharpe ratio dan risk-adjusted returns
        - Average trade duration
        - Performance consistency
        
        Focus pada:
        - Identifying what works dan what doesn't
        - Performance attribution
        - Improvement opportunities
        - Benchmark comparisons
        - Sustainable performance factors
        """
    
    def _get_education_prompt(self) -> str:
        """
        Get system prompt for educational content
        """
        return """
        Anda adalah educational content creator untuk trading, dengan kemampuan:
        - Menjelaskan konsep kompleks dengan sederhana
        - Memberikan examples praktis
        - Creating learning paths
        - Interactive teaching methods
        - Progressive skill building
        
        Teaching style:
        - Start with basics, build complexity
        - Use analogies dan real-world examples
        - Encourage questions dan exploration
        - Provide actionable takeaways
        - Focus on understanding over memorization
        
        Selalu:
        - Check understanding level
        - Provide multiple examples
        - Suggest practice exercises
        - Connect concepts to real application
        - Encourage continued learning
        """


def main():
    """
    Test function for AI assistant
    """
    async def test_assistant():
        assistant = AIAssistant()
        
        # Test general chat
        response = await assistant.chat(
            user_id="test_user",
            message="What are the best risk management practices for crypto trading?",
            context_type=ChatContextType.RISK
        )
        
        print(f"Response: {response.content}")
        print(f"Suggestions: {response.suggestions}")
        print(f"Confidence: {response.confidence}")
    
    asyncio.run(test_assistant())


if __name__ == "__main__":
    main()
