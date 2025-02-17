"""
Environment Forge - Creates and manages development environment profiles.
Handles service configurations and tool permissions.
"""
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional
from pathlib import Path
import json

@dataclass
class ToolConfig:
    """Tool configuration."""
    name: str
    description: str
    permissions: List[str]
    settings: Dict[str, any] = field(default_factory=dict)

@dataclass
class ServiceConfig:
    """Service configuration."""
    image: Optional[str] = None
    environment: Dict[str, str] = field(default_factory=dict)
    ports: Dict[str, int] = field(default_factory=dict)
    healthcheck_timeout: int = 30
    healthcheck_interval: int = 1
    container_name: Optional[str] = None
    volumes: Optional[Dict[str, str]] = None
    tools: List[ToolConfig] = field(default_factory=list)
    settings: Dict[str, any] = field(default_factory=dict)

@dataclass
class EnvironmentProfile:
    """Environment configuration profile."""
    name: str
    description: str
    services: Dict[str, ServiceConfig]
    auto_start: List[str] = field(default_factory=list)
    auto_cleanup: bool = True
    log_retention_days: int = 7

class EnvironmentForge:
    """Creates and manages environment profiles."""
    
    def __init__(self):
        self.forge_dir = Path.home() / ".config" / "nova-aegis"
        self.forge_dir.mkdir(parents=True, exist_ok=True)
        self.profiles_file = self.forge_dir / "environments.json"
        self.active_profile = "default"
        self._forge_profiles()

    def _forge_profiles(self):
        """Load or create environment profiles."""
        if not self.profiles_file.exists():
            # Create default profile with browser tool
            browser_tool = ToolConfig(
                name="browser",
                description="Web browser automation",
                permissions=["navigate", "click", "type", "extract"],
                settings={
                    "headless": True,
                    "timeout": 30
                }
            )
            
            default_service = ServiceConfig(
                tools=[browser_tool],
                settings={}
            )
            
            self.profiles = {
                "default": EnvironmentProfile(
                    name="default",
                    description="Default environment",
                    services={"browser": default_service}
                )
            }
            self._save_profiles()
        else:
            with open(self.profiles_file) as f:
                data = json.load(f)
                self.profiles = {
                    name: EnvironmentProfile(
                        name=profile_data["name"],
                        description=profile_data["description"],
                        services={
                            svc_name: ServiceConfig(**svc_data)
                            for svc_name, svc_data in profile_data["services"].items()
                        },
                        auto_start=profile_data.get("auto_start", []),
                        auto_cleanup=profile_data.get("auto_cleanup", True),
                        log_retention_days=profile_data.get("log_retention_days", 7)
                    )
                    for name, profile_data in data.items()
                }

    def _save_profiles(self):
        """Save environment profiles."""
        with open(self.profiles_file, "w") as f:
            json.dump(
                {name: asdict(profile) for name, profile in self.profiles.items()},
                f,
                indent=2
            )

    def get_profile(self, name: Optional[str] = None) -> EnvironmentProfile:
        """Get environment profile."""
        name = name or self.active_profile
        return self.profiles[name]

    def set_active_profile(self, name: str):
        """Set active profile."""
        if name not in self.profiles:
            raise ValueError(f"Profile {name} does not exist")
        self.active_profile = name

    def create_profile(self, name: str, description: str, services: Dict[str, ServiceConfig]) -> EnvironmentProfile:
        """Create new profile."""
        if name in self.profiles:
            raise ValueError(f"Profile {name} already exists")
            
        profile = EnvironmentProfile(
            name=name,
            description=description,
            services=services
        )
        self.profiles[name] = profile
        self._save_profiles()
        return profile

    def update_profile(self, name: str, services: Dict[str, ServiceConfig]):
        """Update profile services."""
        if name not in self.profiles:
            raise ValueError(f"Profile {name} does not exist")
            
        profile = self.profiles[name]
        profile.services.update(services)
        self._save_profiles()

    def delete_profile(self, name: str):
        """Delete profile."""
        if name == "default":
            raise ValueError("Cannot delete default profile")
        if name not in self.profiles:
            raise ValueError(f"Profile {name} does not exist")
            
        del self.profiles[name]
        if self.active_profile == name:
            self.active_profile = "default"
        self._save_profiles()

    def list_profiles(self) -> List[str]:
        """List available profiles."""
        return list(self.profiles.keys())