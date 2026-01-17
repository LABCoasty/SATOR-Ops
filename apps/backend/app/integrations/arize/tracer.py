"""
Arize Tracer Implementation

Observability tracing for agent tool calls.
"""

import time
from datetime import datetime
from dataclasses import dataclass, field
from functools import wraps
from typing import Any, Callable
from enum import Enum

from config import config


class SpanStatus(str, Enum):
    """Status of a trace span"""
    RUNNING = "running"
    SUCCESS = "success"
    ERROR = "error"


@dataclass
class TraceSpan:
    """A trace span for an operation"""
    span_id: str
    name: str
    start_time: datetime
    end_time: datetime | None = None
    status: SpanStatus = SpanStatus.RUNNING
    attributes: dict = field(default_factory=dict)
    error_message: str | None = None
    duration_ms: float | None = None
    
    def end(self, status: SpanStatus = SpanStatus.SUCCESS, error: str | None = None):
        """End the span"""
        self.end_time = datetime.utcnow()
        self.status = status
        self.error_message = error
        self.duration_ms = (self.end_time - self.start_time).total_seconds() * 1000


class ArizeTracer:
    """
    Observability tracer for agent tool calls using Arize.
    
    Captures: tool name, parameters, response time, success/failure,
    and any refusals.
    
    This is an optional integration that no-ops when disabled.
    """
    
    def __init__(self, enabled: bool | None = None):
        self._enabled = enabled if enabled is not None else config.enable_arize
        self._spans: list[TraceSpan] = []
        self._span_counter = 0
        
        # Arize client would be initialized here in production
        self._client = None
        if self._enabled and config.arize_api_key:
            # In production: self._client = arize.Client(...)
            pass
    
    @property
    def enabled(self) -> bool:
        return self._enabled
    
    def _generate_span_id(self) -> str:
        """Generate a unique span ID"""
        self._span_counter += 1
        return f"span_{self._span_counter:06d}"
    
    def start_span(
        self, 
        name: str, 
        attributes: dict | None = None
    ) -> TraceSpan:
        """Start a new trace span"""
        span = TraceSpan(
            span_id=self._generate_span_id(),
            name=name,
            start_time=datetime.utcnow(),
            attributes=attributes or {},
        )
        
        if self._enabled:
            self._spans.append(span)
        
        return span
    
    def trace_tool_call(self, tool_name: str):
        """
        Decorator for tracing tool calls.
        
        Usage:
            @tracer.trace_tool_call("my_tool")
            async def my_tool(params):
                ...
        """
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                if not self._enabled:
                    return await func(*args, **kwargs)
                
                span = self.start_span(
                    name=f"tool:{tool_name}",
                    attributes={
                        "tool_name": tool_name,
                        "args": str(args)[:200],
                        "kwargs": str(kwargs)[:200],
                    }
                )
                
                try:
                    result = await func(*args, **kwargs)
                    span.end(status=SpanStatus.SUCCESS)
                    span.attributes["result_type"] = type(result).__name__
                    
                    # Send to Arize in production
                    await self._send_span(span)
                    
                    return result
                    
                except Exception as e:
                    span.end(status=SpanStatus.ERROR, error=str(e))
                    await self._send_span(span)
                    raise
            
            return wrapper
        return decorator
    
    async def _send_span(self, span: TraceSpan) -> None:
        """Send a span to Arize"""
        if not self._enabled or not self._client:
            return
        
        # In production, this would use the Arize client:
        # self._client.log_span(
        #     span_id=span.span_id,
        #     name=span.name,
        #     start_time=span.start_time,
        #     end_time=span.end_time,
        #     status=span.status.value,
        #     attributes=span.attributes,
        # )
        pass
    
    def log_refusal(
        self, 
        tool_name: str, 
        reason: str,
        context: dict | None = None
    ) -> None:
        """Log when an agent tool call is refused"""
        if not self._enabled:
            return
        
        span = self.start_span(
            name=f"refusal:{tool_name}",
            attributes={
                "tool_name": tool_name,
                "refusal_reason": reason,
                "context": context or {},
            }
        )
        span.end(status=SpanStatus.ERROR, error=f"Refused: {reason}")
    
    def get_spans(self, limit: int = 100) -> list[dict]:
        """Get recent spans for debugging"""
        return [
            {
                "span_id": s.span_id,
                "name": s.name,
                "start_time": s.start_time.isoformat(),
                "end_time": s.end_time.isoformat() if s.end_time else None,
                "status": s.status.value,
                "duration_ms": s.duration_ms,
                "attributes": s.attributes,
            }
            for s in self._spans[-limit:]
        ]
    
    def clear_spans(self) -> None:
        """Clear stored spans"""
        self._spans.clear()


# Global tracer instance
_tracer: ArizeTracer | None = None


def get_tracer() -> ArizeTracer:
    """Get or create the global tracer"""
    global _tracer
    if _tracer is None:
        _tracer = ArizeTracer()
    return _tracer
