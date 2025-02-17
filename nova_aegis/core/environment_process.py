"""
Environment process state machine for NovaAegis.
Tracks and manages the lifecycle of development environments.
"""
from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, List, Optional

class EnvironmentState(Enum):
    """States in the environment lifecycle."""
    UNINITIALIZED = auto()
    INITIALIZING = auto()
    READY = auto()
    STARTING_SERVICES = auto()
    RUNNING = auto()
    STOPPING_SERVICES = auto()
    ERROR = auto()
    TERMINATED = auto()

@dataclass
class StateTransition:
    """Records a state change in the environment."""
    from_state: EnvironmentState
    to_state: EnvironmentState
    timestamp: float
    reason: str
    error: Optional[Exception] = None

class EnvironmentProcess:
    """
    Tracks the lifecycle of a development environment.
    
    This is the core abstraction for environment state management,
    ensuring we can always determine what state the environment is in
    and what operations are valid.
    """
    
    def __init__(self, profile_name: str):
        self.profile_name = profile_name
        self.state = EnvironmentState.UNINITIALIZED
        self.history: List[StateTransition] = []
        self.errors: List[Exception] = []
        self.service_states: Dict[str, bool] = {}  # service_name -> is_healthy
        
    def transition_to(self, new_state: EnvironmentState, reason: str, error: Optional[Exception] = None):
        """Record a state transition."""
        from time import time
        
        transition = StateTransition(
            from_state=self.state,
            to_state=new_state,
            timestamp=time(),
            reason=reason,
            error=error
        )
        
        self.history.append(transition)
        self.state = new_state
        
        if error:
            self.errors.append(error)
            
    def can_transition_to(self, target_state: EnvironmentState) -> bool:
        """Check if a state transition is valid."""
        # Define valid transitions
        valid_transitions = {
            EnvironmentState.UNINITIALIZED: {
                EnvironmentState.INITIALIZING,
                EnvironmentState.ERROR
            },
            EnvironmentState.INITIALIZING: {
                EnvironmentState.READY,
                EnvironmentState.ERROR
            },
            EnvironmentState.READY: {
                EnvironmentState.STARTING_SERVICES,
                EnvironmentState.ERROR,
                EnvironmentState.TERMINATED
            },
            EnvironmentState.STARTING_SERVICES: {
                EnvironmentState.RUNNING,
                EnvironmentState.ERROR
            },
            EnvironmentState.RUNNING: {
                EnvironmentState.STOPPING_SERVICES,
                EnvironmentState.ERROR
            },
            EnvironmentState.STOPPING_SERVICES: {
                EnvironmentState.READY,
                EnvironmentState.ERROR,
                EnvironmentState.TERMINATED
            },
            EnvironmentState.ERROR: {
                EnvironmentState.READY,
                EnvironmentState.TERMINATED
            },
            EnvironmentState.TERMINATED: set()  # Terminal state
        }
        
        return target_state in valid_transitions[self.state]
        
    def update_service_state(self, service_name: str, is_healthy: bool):
        """Update the health status of a service."""
        self.service_states[service_name] = is_healthy
        
    def all_services_healthy(self) -> bool:
        """Check if all services are healthy."""
        return all(self.service_states.values())
        
    def get_unhealthy_services(self) -> List[str]:
        """Get list of unhealthy services."""
        return [name for name, healthy in self.service_states.items() 
                if not healthy]
                
    def get_latest_error(self) -> Optional[Exception]:
        """Get the most recent error if any."""
        return self.errors[-1] if self.errors else None
        
    def get_state_duration(self) -> float:
        """Get how long we've been in the current state."""
        from time import time
        
        if not self.history:
            return 0
            
        return time() - self.history[-1].timestamp
        
    def get_total_runtime(self) -> float:
        """Get total time since initialization."""
        from time import time
        
        if not self.history:
            return 0
            
        return time() - self.history[0].timestamp
        
    def __str__(self) -> str:
        """Get human readable status."""
        status = [
            f"Environment: {self.profile_name}",
            f"State: {self.state.name}",
            f"Duration: {self.get_state_duration():.1f}s",
            f"Total Runtime: {self.get_total_runtime():.1f}s",
            "Services:"
        ]
        
        for name, healthy in self.service_states.items():
            status.append(f"  {name}: {'✓' if healthy else '✗'}")
            
        if self.errors:
            status.append("Latest Error:")
            status.append(f"  {str(self.errors[-1])}")
            
        return "\n".join(status)