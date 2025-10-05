"""
AI Service Client for On-Demand Content Generation
Manages AI model loading, caching, and intelligent content generation
"""

import time
import threading
import json
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, Tuple
from dataclasses import dataclass
import logging
import queue

from .model_manager import ModelManager, ModelConfig
from .templates import NOTIFICATION_TEMPLATES

@dataclass
class AIRequest:
    """Represents an AI generation request"""
    request_id: str
    request_type: str  # 'notification', 'response', 'analysis'
    context: Dict[str, Any]
    priority: str = 'normal'  # 'low', 'normal', 'high'
    user_preference: str = 'medium'
    created_at: float = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()

@dataclass
class AIResponse:
    """Represents an AI generation response"""
    request_id: str
    content: str
    confidence: float
    generation_time: float
    model_used: str
    cached: bool = False

class AIServiceClient:
    """
    On-demand AI service client for content generation with resource management
    """
    
    def __init__(self):
        self.model_manager = None
        
        # Request queue and processing
        self.request_queue = queue.PriorityQueue()
        self.processing_thread = None
        self.shutdown_event = threading.Event()
        
        # Performance tracking
        self.stats = {
            'requests_processed': 0,
            'avg_generation_time': 0.0,
            'model_loads': 0,
            'total_processing_time': 0.0
        }
        
        # Content templates for quick generation
        self.templates = NOTIFICATION_TEMPLATES
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Start processing thread
        self._start_processing_thread()
    
    
    def _start_processing_thread(self):
        """Start the background AI processing thread"""
        self.processing_thread = threading.Thread(target=self._process_requests, daemon=True)
        self.processing_thread.start()
        self.logger.info("AI service processing thread started")
    
    def _process_requests(self):
        """Background thread for processing AI requests"""
        while not self.shutdown_event.is_set():
            try:
                # Get next request (blocks with timeout)
                try:
                    priority, request = self.request_queue.get(timeout=1.0)
                except queue.Empty:
                    continue
                
                # Process the request
                response = self._process_single_request(request)
                
                self.request_queue.task_done()
                
            except Exception as e:
                self.logger.error(f"Error processing AI request: {e}")
    
    def _process_single_request(self, request: AIRequest) -> Optional[AIResponse]:
        """Process a single AI request"""
        start_time = time.time()
        
        try:
            # Generate content
            content = None
            confidence = 0.0
            model_used = "template"
            
            # Try template-based generation first (fast)
            if request.priority == 'low' or not self._should_use_ai_model(request):
                content = self._generate_template_content(request)
                confidence = 0.6
            
            # Use AI model for higher quality (slower)
            if not content or (request.priority == 'high' and confidence < 0.8):
                ai_content = self._generate_ai_content(request)
                if ai_content:
                    content = ai_content
                    confidence = 0.9
                    model_used = self._get_current_model_name()
            
            # Fallback to template if AI failed
            if not content:
                content = self._generate_template_content(request)
                confidence = 0.5
            
            generation_time = time.time() - start_time
            
            # Update stats
            self.stats['requests_processed'] += 1
            self.stats['total_processing_time'] += generation_time
            self.stats['avg_generation_time'] = (
                self.stats['total_processing_time'] / self.stats['requests_processed']
            )
            
            return AIResponse(
                request_id=request.request_id,
                content=content,
                confidence=confidence,
                generation_time=generation_time,
                model_used=model_used
            )
            
        except Exception as e:
            self.logger.error(f"Error processing request {request.request_id}: {e}")
            return None
    
    def _should_use_ai_model(self, request: AIRequest) -> bool:
        """Determine if we should use AI model vs templates"""
        # Use AI for high priority requests
        if request.priority == 'high':
            return True
        
        # Use AI for complex contexts
        if len(str(request.context)) > 500:
            return True
        
        # Use AI for personalized user preferences
        if request.user_preference in ['high', 'personalized']:
            return True
        
        # Use templates for simple, low-priority requests
        return False
    
    def _generate_template_content(self, request: AIRequest) -> Optional[str]:
        """Generate content using templates (fast)"""
        try:
            request_type = request.request_type
            context = request.context
            
            if request_type == 'notification':
                trigger_type = context.get('trigger_type', 'general')
                
                if trigger_type == 'calendar':
                    return self._generate_calendar_template(context)
                elif trigger_type == 'goal':
                    return self._generate_goal_template(context)
                elif trigger_type == 'pattern':
                    return self._generate_pattern_template(context)
                elif trigger_type == 'learning':
                    return self._generate_learning_template(context)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error generating template content: {e}")
            return None
    
    def _generate_calendar_template(self, context: Dict) -> Optional[str]:
        """Generate calendar notification using templates"""
        event = context.get('event', {})
        minutes_until = context.get('minutes_until', 0)
        
        if not event:
            return None
        
        # Format time until
        if minutes_until < 60:
            time_until = f"{minutes_until} minutes"
        else:
            hours = minutes_until // 60
            mins = minutes_until % 60
            if mins == 0:
                time_until = f"{hours} hour{'s' if hours != 1 else ''}"
            else:
                time_until = f"{hours}h {mins}m"
        
        # Choose appropriate template
        if minutes_until <= 30:
            templates = self.templates['calendar']['meeting_soon']
        else:
            templates = self.templates['calendar']['meeting_prep']
        
        import random
        template = random.choice(templates)
        
        return template.format(
            event_title=event.get('summary', 'Meeting'),
            time_until=time_until,
            attendees=f"{event.get('attendee_count', 0)} people" if event.get('attendee_count', 0) > 0 else "others"
        )
    
    def _generate_goal_template(self, context: Dict) -> Optional[str]:
        """Generate goal notification using templates"""
        goal = context.get('goal', {})
        days_stale = context.get('days_stale', 0)
        
        if not goal:
            return None
        
        import random
        
        # Check if it's a deadline reminder or stale reminder
        if 'days_until_deadline' in context:
            templates = self.templates['goal']['deadline_approaching']
            template = random.choice(templates)
            return template.format(
                goal_title=goal.get('title', 'Goal'),
                days_left=context['days_until_deadline'],
                progress=goal.get('progress', 0)
            )
        else:
            templates = self.templates['goal']['stale_reminder']
            template = random.choice(templates)
            return template.format(
                goal_title=goal.get('title', 'Goal'),
                days=int(days_stale)
            )
    
    def _generate_pattern_template(self, context: Dict) -> Optional[str]:
        """Generate pattern-based notification using templates"""
        activity_level = context.get('activity_level', 0)
        interests = context.get('interests', [])
        
        import random
        
        current_time = datetime.now().strftime('%I:%M %p')
        
        if interests:
            templates = self.templates['pattern']['interest_match']
            template = random.choice(templates)
            interest = random.choice(interests) if isinstance(interests, list) else interests
            return template.format(
                interest=interest,
                activity="focused work",
                time=current_time
            )
        else:
            templates = self.templates['pattern']['productive_time']
            template = random.choice(templates)
            return template.format(
                time=current_time,
                activity="important tasks"
            )
    
    def _generate_learning_template(self, context: Dict) -> Optional[str]:
        """Generate learning-based notification using templates"""
        insight_count = context.get('insight_count', 0)
        
        import random
        templates = self.templates['learning']['insights_ready']
        template = random.choice(templates)
        
        return template.format(insight_count=insight_count)
    
    def _generate_ai_content(self, request: AIRequest) -> Optional[str]:
        """Generate content using AI model (slower but higher quality)"""
        try:
            # Ensure model is loaded
            if not self._ensure_model_loaded():
                return None
            
            # Build prompt based on request type
            prompt = self._build_ai_prompt(request)
            if not prompt:
                return None
            
            # Generate content using model
            messages = [
                {"role": "system", "content": self._get_system_prompt(request)},
                {"role": "user", "content": prompt}
            ]
            
            response = self.model_manager.generate_response(
                messages,
                max_tokens=150,  # Keep notifications concise
                temperature=0.7
            )
            
            return response.strip() if response else None
            
        except Exception as e:
            self.logger.error(f"Error generating AI content: {e}")
            return None
    
    def _ensure_model_loaded(self) -> bool:
        """Ensure AI model is loaded and ready"""
        try:
            if self.model_manager is None:
                self.logger.info("Loading AI model for content generation")
                self.model_manager = ModelManager()
                self.stats['model_loads'] += 1
                return True
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error loading AI model: {e}")
            return False
    
    def _get_current_model_name(self) -> str:
        """Get the name of the currently loaded model"""
        if self.model_manager:
            config = self.model_manager.get_current_model()
            return config.name
        return "none"
    
    def _build_ai_prompt(self, request: AIRequest) -> Optional[str]:
        """Build AI prompt based on request context"""
        context = request.context
        request_type = request.request_type
        
        if request_type == 'notification':
            trigger_type = context.get('trigger_type', 'general')
            
            if trigger_type == 'calendar':
                event = context.get('event', {})
                minutes_until = context.get('minutes_until', 0)
                return f"Create a helpful notification about the upcoming event '{event.get('summary', 'Meeting')}' in {minutes_until} minutes. Be concise and actionable."
            
            elif trigger_type == 'goal':
                goal = context.get('goal', {})
                days_stale = context.get('days_stale', 0)
                return f"Create an encouraging reminder about the goal '{goal.get('title', 'Goal')}' which hasn't been updated in {days_stale} days. Be motivating but not pushy."
            
            elif trigger_type == 'pattern':
                return "Create a gentle suggestion based on the user's activity patterns. Be helpful and respectful of their time."
            
            elif trigger_type == 'learning':
                insight_count = context.get('insight_count', 0)
                return f"Create a notification offering to share {insight_count} insights learned about the user's preferences. Be curious and helpful."
        
        return None
    
    def _get_system_prompt(self, request: AIRequest) -> str:
        """Get system prompt for AI generation"""
        base_prompt = """You are a helpful AI assistant creating proactive notifications. Your notifications should be:
- Concise (under 100 characters when possible)
- Helpful and actionable
- Respectful of the user's time and attention
- Personalized when appropriate
- Never pushy or demanding"""
        
        if request.user_preference == 'high':
            base_prompt += "\n- More detailed and informative"
        elif request.user_preference == 'low':
            base_prompt += "\n- Very brief and minimal"
        
        return base_prompt
    
    
    # Public API methods
    
    def generate_notification_content(self, trigger_type: str, context: Dict, 
                                    user_preference: str = 'medium', 
                                    priority: str = 'normal') -> Optional[str]:
        """
        Generate notification content (synchronous for immediate use)
        """
        request = AIRequest(
            request_id=f"notif_{int(time.time())}",
            request_type='notification',
            context={'trigger_type': trigger_type, **context},
            priority=priority,
            user_preference=user_preference
        )
        
        # For immediate use, process synchronously
        response = self._process_single_request(request)
        return response.content if response else None
    
    def generate_response_content(self, user_message: str, context: Dict,
                                user_preference: str = 'medium') -> Optional[str]:
        """
        Generate conversational response content
        """
        request = AIRequest(
            request_id=f"resp_{int(time.time())}",
            request_type='response',
            context={'user_message': user_message, **context},
            priority='normal',
            user_preference=user_preference
        )
        
        response = self._process_single_request(request)
        return response.content if response else None
    
    def precompute_common_responses(self):
        """Precompute common notification types - simplified without caching"""
        # This method is now mainly for warming up the model
        if not self._ensure_model_loaded():
            return
        
        self.logger.info("AI model warmed up and ready")
    
    def get_service_stats(self) -> Dict[str, Any]:
        """Get AI service statistics"""
        stats = self.stats.copy()
        stats.update({
            'model_loaded': self.model_manager is not None,
            'current_model': self._get_current_model_name(),
            'queue_size': self.request_queue.qsize()
        })
        return stats
    
    def cleanup(self):
        """Cleanup AI service resources"""
        self.logger.info("Shutting down AI service")
        self.shutdown_event.set()
        
        if self.processing_thread and self.processing_thread.is_alive():
            self.processing_thread.join(timeout=10)
        
        if self.model_manager:
            self.model_manager = None
        
        self.logger.info("AI service cleaned up")

# Example usage
def main():
    """Test the AI service client"""
    import time
    
    # Create AI service
    ai_service = AIServiceClient()
    
    # Test notification generation
    test_contexts = [
        ('calendar', {'event': {'summary': 'Team Meeting'}, 'minutes_until': 45}),
        ('goal', {'goal': {'title': 'Finish thesis'}, 'days_stale': 5}),
        ('pattern', {'activity_level': 8, 'interests': ['research', 'writing']}),
        ('learning', {'insight_count': 4, 'confidence': 0.85})
    ]
    
    print("Testing AI notification generation:")
    print("=" * 50)
    
    for trigger_type, context in test_contexts:
        start_time = time.time()
        
        content = ai_service.generate_notification_content(
            trigger_type=trigger_type,
            context=context,
            user_preference='medium',
            priority='normal'
        )
        
        generation_time = time.time() - start_time
        
        print(f"\nTrigger: {trigger_type}")
        print(f"Content: {content}")
        print(f"Time: {generation_time:.3f}s")
    
    # Show stats
    print("\n" + "=" * 50)
    print("Service Statistics:")
    stats = ai_service.get_service_stats()
    for key, value in stats.items():
        print(f"{key}: {value}")
    
    # Cleanup
    ai_service.cleanup()

if __name__ == '__main__':
    main()

