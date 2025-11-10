"""
NusaNexus NoFOMO - AI Parameter Optimizer
AI-powered hyperparameter optimization for trading strategies
"""

import os
import asyncio
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import numpy as np
import pandas as pd
from pydantic import BaseModel, ConfigDict
from openai import OpenAI
import structlog
from pathlib import Path
from sklearn.model_selection import ParameterGrid

# Configure logging
logger = structlog.get_logger(__name__)


class OptimizationObjective(BaseModel):
    """Define optimization objectives"""
    metric: str  # "profit_factor", "sharpe_ratio", "total_return", "win_rate"
    direction: str  # "maximize" or "minimize"
    weight: float = 1.0  # Weight for multi-objective optimization
    threshold: Optional[float] = None  # Minimum acceptable value


class ParameterRange(BaseModel):
    """Define parameter ranges for optimization"""
    name: str
    param_type: str  # "int", "float", "categorical"
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    step: Optional[float] = None
    choices: Optional[List[Any]] = None


class OptimizationResult(BaseModel):
    """Results of parameter optimization"""
    model_config = ConfigDict(protected_namespaces=())
    
    optimization_id: str
    best_parameters: Dict[str, Any]
    best_score: float
    improvement_percentage: float
    confidence_interval: Dict[str, float]
    optimization_history: List[Dict[str, Any]]
    ai_recommendations: List[str]
    convergence_data: Dict[str, Any]
    execution_time: float
    model_used: str
    tokens_used: int


class AIParameterOptimizer:
    """
    AI-powered parameter optimizer using OpenRouter
    """
    
    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv('OPENROUTER_API_KEY'),
            base_url=os.getenv('OPENROUTER_BASE_URL', 'https://openrouter.ai/api/v1')
        )
        self.optimizations_dir = Path('optimizations')
        self.optimizations_dir.mkdir(exist_ok=True)
        self.cache = {}
        
    async def optimize_parameters(
        self,
        strategy_code: str,
        parameter_ranges: List[ParameterRange],
        objectives: List[OptimizationObjective],
        data: Optional[pd.DataFrame] = None,
        max_iterations: int = 100,
        optimization_type: str = "bayesian"
    ) -> OptimizationResult:
        """
        Optimize strategy parameters using AI and mathematical optimization
        """
        start_time = datetime.now()
        optimization_id = f"opt_{start_time.strftime('%Y%m%d_%H%M%S')}"
        
        try:
            logger.info(f"Starting parameter optimization {optimization_id}")
            
            # Step 1: AI-guided parameter analysis
            ai_suggestions = await self._analyze_parameters_with_ai(
                strategy_code, parameter_ranges, objectives
            )
            
            # Step 2: Generate initial parameter grid
            initial_grid = self._generate_parameter_grid(parameter_ranges, max_iterations)
            
            # Step 3: Multi-objective optimization
            if optimization_type == "bayesian":
                results = await self._bayesian_optimization(
                    initial_grid, objectives, max_iterations
                )
            elif optimization_type == "genetic":
                results = await self._genetic_optimization(
                    initial_grid, objectives, max_iterations
                )
            else:  # grid search with AI guidance
                results = await self._guided_grid_search(
                    initial_grid, objectives, ai_suggestions
                )
            
            # Step 4: AI analysis of results
            ai_analysis = await self._analyze_results_with_ai(
                results, objectives, strategy_code
            )
            
            # Step 5: Calculate improvement and confidence
            best_result = max(results, key=lambda x: x['score'])
            improvement = self._calculate_improvement(best_result, results)
            confidence_interval = self._calculate_confidence_interval(results)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Step 6: Save results
            optimization_result = OptimizationResult(
                optimization_id=optimization_id,
                best_parameters=best_result['parameters'],
                best_score=best_result['score'],
                improvement_percentage=improvement,
                confidence_interval=confidence_interval,
                optimization_history=results,
                ai_recommendations=ai_analysis['recommendations'],
                convergence_data=ai_analysis['convergence_data'],
                execution_time=execution_time,
                model_used=os.getenv('OPENROUTER_MODEL', 'anthropic/claude-3-sonnet'),
                tokens_used=ai_analysis.get('tokens_used', 0)
            )
            
            await self._save_optimization_result(optimization_result)
            
            logger.info(f"Optimization {optimization_id} completed successfully")
            return optimization_result
            
        except Exception as e:
            logger.error(f"Parameter optimization failed: {str(e)}")
            raise
    
    async def _analyze_parameters_with_ai(
        self,
        strategy_code: str,
        parameter_ranges: List[ParameterRange],
        objectives: List[OptimizationObjective]
    ) -> Dict[str, Any]:
        """
        Use AI to analyze strategy and suggest optimal parameter ranges
        """
        system_prompt = """
        Anda adalah ahli optimasi parameter trading dan machine learning.
        Analisis strategi Freqtrade dan berikan saran untuk optimasi parameter.
        
        Guidelines:
        1. Analisis sensitivitas parameter terhadap performa
        2. Identifikasi parameter yang paling влияют на результат
        3. Sarankan range optimal berdasarkan strategy logic
        4. Berikan insight tentang interaksi antar parameter
        5. Pertimbangkan multi-objective optimization
        """
        
        user_prompt = f"""
        Analisis strategi berikut untuk optimasi parameter:
        
        Strategy Code:
        ```
        {strategy_code}
        ```
        
        Parameter Ranges:
        {json.dumps([pr.model_dump() for pr in parameter_ranges], indent=2)}
        
        Objectives:
        {json.dumps([obj.model_dump() for obj in objectives], indent=2)}
        
        Berikan analisis dalam format:
        - key_parameters: [list parameter kunci]
        - recommended_ranges: {{parameter_name: {min, max}}}
        - parameter_interactions: [insight tentang interaksi]
        - optimization_suggestions: [saran optimasi]
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
        
        return self._parse_ai_response(response.choices[0].message.content or "")
    
    def _generate_parameter_grid(
        self,
        parameter_ranges: List[ParameterRange],
        max_combinations: int
    ) -> List[Dict[str, Any]]:
        """
        Generate parameter grid based on ranges
        """
        param_dict = {}
        
        for param in parameter_ranges:
            if param.param_type == "int":
                if param.min_value is None or param.max_value is None:
                    raise ValueError(f"Integer parameter '{param.name}' requires min and max values")
                min_value = int(param.min_value)
                max_value = int(param.max_value)
                if param.step:
                    step = max(1, int(param.step))
                    values = list(range(min_value, max_value + 1, step))
                else:
                    values = [min_value, max_value]
            elif param.param_type == "float":
                if param.min_value is None or param.max_value is None:
                    raise ValueError(f"Float parameter '{param.name}' requires min and max values")
                min_value = float(param.min_value)
                max_value = float(param.max_value)
                if param.step:
                    step = float(param.step)
                    values = list(np.arange(min_value, max_value + step, step))
                else:
                    values = [min_value, max_value]
            else:  # categorical
                values = param.choices or [param.min_value, param.max_value]
            
            param_dict[param.name] = values
        
        # Generate grid and limit size
        grid = list(ParameterGrid(param_dict))
        if len(grid) > max_combinations:
            # Sample uniformly from grid
            indices = np.linspace(0, len(grid)-1, max_combinations, dtype=int)
            grid = [grid[i] for i in indices]
        
        return grid
    
    async def _bayesian_optimization(
        self,
        initial_grid: List[Dict[str, Any]],
        objectives: List[OptimizationObjective],
        max_iterations: int
    ) -> List[Dict[str, Any]]:
        """
        Bayesian optimization with AI guidance
        """
        results = []
        
        # Evaluate initial points
        for i, params in enumerate(initial_grid[:20]):  # Start with 20 points
            score = await self._evaluate_parameters(params, objectives)
            results.append({
                'parameters': params,
                'score': score,
                'iteration': i
            })
        
        # Bayesian optimization loop
        for i in range(20, max_iterations):
            # Use AI to suggest next parameters
            suggested_params = await self._suggest_next_parameters(
                results, objectives
            )
            
            if suggested_params:
                score = await self._evaluate_parameters(suggested_params, objectives)
                results.append({
                    'parameters': suggested_params,
                    'score': score,
                    'iteration': i
                })
            
            # Early stopping if convergence
            if self._check_convergence(results):
                break
        
        return results
    
    async def _genetic_optimization(
        self,
        initial_grid: List[Dict[str, Any]],
        objectives: List[OptimizationObjective],
        max_iterations: int
    ) -> List[Dict[str, Any]]:
        """
        Genetic algorithm optimization with AI guidance
        """
        population_size = min(50, len(initial_grid))
        population = initial_grid[:population_size]
        results = []
        
        for generation in range(max_iterations // population_size):
            # Evaluate population
            scored_population = []
            for params in population:
                score = await self._evaluate_parameters(params, objectives)
                scored_population.append((params, score))
            
            # Sort by score
            scored_population.sort(key=lambda x: x[1], reverse=True)
            
            # Store best results
            for params, score in scored_population[:10]:
                results.append({
                    'parameters': params,
                    'score': score,
                    'generation': generation
                })
            
            # Create next generation
            if generation < (max_iterations // population_size) - 1:
                population = self._create_next_generation(
                    scored_population, population_size
                )
        
        return results
    
    async def _guided_grid_search(
        self,
        initial_grid: List[Dict[str, Any]],
        objectives: List[OptimizationObjective],
        ai_suggestions: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Grid search with AI-guided parameter prioritization
        """
        results = []
        
        # Sort parameters by AI importance
        key_params = ai_suggestions.get('key_parameters', [])
        param_priority = {param: i for i, param in enumerate(key_params)}
        
        # Sort grid by priority
        sorted_grid = sorted(
            initial_grid,
            key=lambda x: sum(
                param_priority.get(p, 999) * (1 if p in x else 0)
                for p in key_params
            )
        )
        
        # Evaluate top candidates first
        for i, params in enumerate(sorted_grid[:100]):  # Limit to top 100
            score = await self._evaluate_parameters(params, objectives)
            results.append({
                'parameters': params,
                'score': score,
                'priority_rank': i
            })
        
        return results
    
    async def _evaluate_parameters(
        self,
        parameters: Dict[str, Any],
        objectives: List[OptimizationObjective]
    ) -> float:
        """
        Evaluate parameter set against objectives
        """
        # Mock evaluation - in production, this would run backtest
        base_score = 1.0
        
        # Simulate parameter impact
        for param, value in parameters.items():
            if 'rsi' in param.lower():
                if 10 <= value <= 20:
                    base_score += 0.2
                elif value > 25:
                    base_score -= 0.1
            elif 'ema' in param.lower():
                if 15 <= value <= 30:
                    base_score += 0.15
            elif 'stop' in param.lower():
                if 0.01 <= abs(value) <= 0.05:
                    base_score += 0.1
        
        # Add some randomness to simulate market variance
        noise = np.random.normal(0, 0.05)
        final_score = base_score + noise
        
        return max(0, final_score)  # Ensure non-negative
    
    async def _suggest_next_parameters(
        self,
        results: List[Dict[str, Any]],
        objectives: List[OptimizationObjective]
    ) -> Optional[Dict[str, Any]]:
        """
        Use AI to suggest next parameters based on results
        """
        # Analyze best results so far
        best_results = sorted(results, key=lambda x: x['score'], reverse=True)[:10]
        
        if len(best_results) < 3:
            return None
        
        # Simple heuristic-based suggestion
        # In production, this would use more sophisticated Bayesian methods
        
        # Get parameter ranges from best results
        param_suggestions = {}
        all_params = set()
        for result in best_results:
            all_params.update(result['parameters'].keys())
        
        for param in all_params:
            values = [r['parameters'][param] for r in best_results if param in r['parameters']]
            if values:
                # Suggest value near the best performing ones
                avg_value = np.mean(values)
                std_value = np.std(values)
                suggestion = np.random.normal(avg_value, std_value * 0.5)
                param_suggestions[param] = suggestion
        
        return param_suggestions if param_suggestions else None
    
    def _create_next_generation(
        self,
        scored_population: List[Tuple[Dict[str, Any], float]],
        population_size: int
    ) -> List[Dict[str, Any]]:
        """
        Create next generation using genetic algorithm
        """
        next_generation = []
        
        # Keep top performers (elitism)
        elite_count = max(1, population_size // 10)
        for i in range(elite_count):
            next_generation.append(scored_population[i][0].copy())
        
        # Generate offspring
        while len(next_generation) < population_size:
            # Tournament selection
            parent1 = self._tournament_selection(scored_population)
            parent2 = self._tournament_selection(scored_population)
            
            # Crossover
            child = self._crossover(parent1, parent2)
            
            # Mutation
            child = self._mutate(child)
            
            next_generation.append(child)
        
        return next_generation
    
    def _tournament_selection(
        self,
        population: List[Tuple[Dict[str, Any], float]],
        tournament_size: int = 3
    ) -> Dict[str, Any]:
        """
        Tournament selection for genetic algorithm
        """
        import random
        tournament = random.sample(population, min(tournament_size, len(population)))
        return max(tournament, key=lambda x: x[1])[0]
    
    def _crossover(
        self,
        parent1: Dict[str, Any],
        parent2: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Crossover two parameter sets
        """
        import random
        
        child = {}
        for param in set(parent1.keys()) | set(parent2.keys()):
            if random.random() < 0.5:
                child[param] = parent1.get(param, parent2.get(param))
            else:
                child[param] = parent2.get(param, parent1.get(param))
        
        return child
    
    def _mutate(
        self,
        params: Dict[str, Any],
        mutation_rate: float = 0.1
    ) -> Dict[str, Any]:
        """
        Mutate parameters
        """
        import random
        
        mutated = params.copy()
        for param, value in mutated.items():
            if random.random() < mutation_rate:
                if isinstance(value, (int, float)):
                    # Add small random perturbation
                    if isinstance(value, int):
                        mutated[param] = value + random.randint(-2, 2)
                    else:
                        mutated[param] = value * random.uniform(0.8, 1.2)
        
        return mutated
    
    async def _analyze_results_with_ai(
        self,
        results: List[Dict[str, Any]],
        objectives: List[OptimizationObjective],
        strategy_code: str
    ) -> Dict[str, Any]:
        """
        Use AI to analyze optimization results
        """
        system_prompt = """
        Anda adalah ahli analisis performa trading dan optimasi parameter.
        Analisis hasil optimasi dan berikan rekomendasi.
        """
        
        # Prepare results summary
        best_results = sorted(results, key=lambda x: x['score'], reverse=True)[:5]
        result_summary = {
            'total_evaluations': len(results),
            'best_score': max(r['score'] for r in results),
            'score_distribution': {
                'mean': np.mean([r['score'] for r in results]),
                'std': np.std([r['score'] for r in results]),
                'min': min(r['score'] for r in results),
                'max': max(r['score'] for r in results)
            },
            'top_5_parameters': best_results
        }
        
        user_prompt = f"""
        Analisis hasil optimasi parameter berikut:
        
        Summary: {json.dumps(result_summary, indent=2)}
        
        Objectives: {json.dumps([obj.model_dump() for obj in objectives], indent=2)}
        
        Berikan analisis dan rekomendasi dalam format:
        - recommendations: [list rekomendasi]
        - convergence_analysis: [analisis konvergensi]
        - risk_assessment: [penilaian risiko]
        - next_steps: [langkah selanjutnya]
        """
        
        response = self.client.chat.completions.create(
            model=os.getenv('OPENROUTER_MODEL', 'anthropic/claude-3-sonnet'),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=1500
        )
        
        return self._parse_ai_response(response.choices[0].message.content)
    
    def _parse_ai_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse AI response to structured data
        """
        # Simple parsing - in production, use more robust parsing
        try:
            # Try to extract JSON-like content
            if '```json' in response_text:
                start = response_text.find('```json') + 7
                end = response_text.find('```', start)
                json_content = response_text[start:end].strip()
                return json.loads(json_content)
            
            # Fallback: extract key-value pairs
            result = {}
            lines = response_text.split('\n')
            current_key = None
            current_value = []
            
            for line in lines:
                line = line.strip()
                if ':' in line and not line.startswith(' '):
                    if current_key and current_value:
                        result[current_key] = '\n'.join(current_value)
                    parts = line.split(':', 1)
                    current_key = parts[0].strip().lower().replace(' ', '_')
                    current_value = [parts[1].strip()] if len(parts) > 1 else []
                elif line.startswith('- '):
                    current_value.append(line[2:])
            
            if current_key and current_value:
                result[current_key] = '\n'.join(current_value)
            
            return result
            
        except Exception as e:
            logger.warning(f"Failed to parse AI response: {str(e)}")
            return {"raw_response": response_text}
    
    def _calculate_improvement(self, best_result: Dict[str, Any], all_results: List[Dict[str, Any]]) -> float:
        """
        Calculate improvement percentage
        """
        scores = [r['score'] for r in all_results]
        baseline = np.percentile(scores, 25)  # 25th percentile as baseline
        improvement = (best_result['score'] - baseline) / baseline * 100
        return max(0, improvement)
    
    def _calculate_confidence_interval(self, results: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Calculate confidence interval for results
        """
        scores = [r['score'] for r in results]
        mean_score = np.mean(scores)
        std_score = np.std(scores)
        
        return {
            "mean": mean_score,
            "std": std_score,
            "min_95": mean_score - 1.96 * std_score,
            "max_95": mean_score + 1.96 * std_score
        }
    
    def _check_convergence(self, results: List[Dict[str, Any]], window: int = 10) -> bool:
        """
        Check if optimization has converged
        """
        if len(results) < window:
            return False
        
        recent_scores = [r['score'] for r in results[-window:]]
        score_variance = np.var(recent_scores)
        
        return score_variance < 0.01  # Threshold for convergence
    
    async def _save_optimization_result(self, result: OptimizationResult):
        """
        Save optimization result to file
        """
        filepath = self.optimizations_dir / f"{result.optimization_id}.json"
        
        with open(filepath, 'w') as f:
            json.dump(result.model_dump(), f, indent=2, default=str)
        
        logger.info(f"Optimization result saved to {filepath}")
    
    async def get_optimization_history(self, strategy_id: str) -> List[OptimizationResult]:
        """
        Get optimization history for a strategy
        """
        history = []
        
        for filepath in self.optimizations_dir.glob("*.json"):
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    if strategy_id in data.get('optimization_id', ''):
                        history.append(OptimizationResult(**data))
            except Exception as e:
                logger.warning(f"Failed to load optimization {filepath}: {str(e)}")
        
        return sorted(history, key=lambda x: x.execution_time, reverse=True)


def main():
    """
    Test function for parameter optimizer
    """
    async def test_optimizer():
        optimizer = AIParameterOptimizer()
        
        # Define parameter ranges
        parameter_ranges = [
            ParameterRange(name="rsi_period", param_type="int", min_value=10, max_value=30, step=2),
            ParameterRange(name="rsi_overbought", param_type="int", min_value=60, max_value=80, step=2),
            ParameterRange(name="rsi_oversold", param_type="int", min_value=20, max_value=40, step=2),
            ParameterRange(name="ema_period", param_type="int", min_value=15, max_value=35, step=2)
        ]
        
        # Define objectives
        objectives = [
            OptimizationObjective(metric="sharpe_ratio", direction="maximize", weight=0.6),
            OptimizationObjective(metric="max_drawdown", direction="minimize", weight=0.4)
        ]
        
        # Run optimization
        result = await optimizer.optimize_parameters(
            strategy_code="# Test strategy",
            parameter_ranges=parameter_ranges,
            objectives=objectives,
            max_iterations=50,
            optimization_type="guided"
        )
        
        print(f"Optimization ID: {result.optimization_id}")
        print(f"Best Score: {result.best_score:.3f}")
        print(f"Improvement: {result.improvement_percentage:.1f}%")
        print(f"Best Parameters: {result.best_parameters}")
    
    asyncio.run(test_optimizer())


if __name__ == "__main__":
    main()
