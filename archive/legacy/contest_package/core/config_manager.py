#!/usr/bin/env python3
"""
Centralized Configuration Manager for Manga Generation Pipeline
Phase 18: Handles settings.yaml and .env integration
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, Union
from dotenv import load_dotenv

class ConfigManager:
    """Centralized configuration manager for the manga generation pipeline."""
    
    def __init__(self, settings_file: str = "config/settings.yaml", env_file: str = ".env"):
        """
        Initialize configuration manager.
        
        Args:
            settings_file: Path to YAML settings file
            env_file: Path to environment file
        """
        self.project_root = Path(__file__).parent.parent
        self.settings_file = self.project_root / settings_file
        self.env_file = self.project_root / env_file
        
        # Load environment variables
        if self.env_file.exists():
            load_dotenv(self.env_file)
        
        # Load YAML settings
        self.settings = self._load_settings()
        
        # Cache for resolved paths
        self._path_cache = {}
    
    def _load_settings(self) -> Dict[str, Any]:
        """Load settings from YAML file."""
        if not self.settings_file.exists():
            raise FileNotFoundError(f"Settings file not found: {self.settings_file}")
        
        try:
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            raise Exception(f"Error loading settings file: {e}")
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation.
        
        Args:
            key_path: Dot-separated path to the configuration value
            default: Default value if key not found
            
        Returns:
            Configuration value
            
        Example:
            config.get("models.checkpoint.path")
            config.get("comfyui.server.url")
        """
        keys = key_path.split('.')
        value = self.settings
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def get_env(self, key: str, default: Any = None) -> Any:
        """
        Get environment variable.
        
        Args:
            key: Environment variable name
            default: Default value if not found
            
        Returns:
            Environment variable value
        """
        return os.getenv(key, default)
    
    def get_model_path(self, model_type: str, model_name: str = None) -> Optional[str]:
        """
        Get absolute path to a model file.
        
        Args:
            model_type: Type of model (checkpoint, controlnet, lora, etc.)
            model_name: Specific model name (optional, uses default if not specified)
            
        Returns:
            Absolute path to model file
        """
        cache_key = f"{model_type}_{model_name or 'default'}"
        
        if cache_key in self._path_cache:
            return self._path_cache[cache_key]
        
        # Get model configuration
        if model_name:
            model_config = self.get(f"models.{model_type}.{model_name}")
        else:
            # Get first available model of this type
            models = self.get(f"models.{model_type}", {})
            if not models:
                return None
            model_config = next(iter(models.values()))
        
        if not model_config or 'path' not in model_config:
            return None
        
        # Resolve absolute path
        model_path = self.project_root / model_config['path']
        abs_path = str(model_path) if model_path.exists() else None
        
        # Cache the result
        self._path_cache[cache_key] = abs_path
        return abs_path
    
    def get_workflow_path(self, workflow_name: str) -> Optional[str]:
        """
        Get absolute path to a workflow template.
        
        Args:
            workflow_name: Name of the workflow
            
        Returns:
            Absolute path to workflow file
        """
        workflow_config = self.get(f"workflows.{workflow_name}")
        if not workflow_config or 'template' not in workflow_config:
            return None
        
        workflow_path = self.project_root / workflow_config['template']
        return str(workflow_path) if workflow_path.exists() else None
    
    def get_comfyui_url(self) -> str:
        """Get ComfyUI server URL."""
        # Environment variable takes precedence
        env_url = self.get_env("COMFYUI_URL")
        if env_url:
            return env_url
        
        # Fall back to settings
        return self.get("comfyui.server.url", "http://127.0.0.1:8188")
    
    def get_comfyui_installation_path(self) -> str:
        """Get ComfyUI installation path."""
        # Environment variable takes precedence
        env_path = self.get_env("COMFYUI_INSTALLATION_PATH")
        if env_path:
            return str(self.project_root / env_path)
        
        # Fall back to settings
        install_path = self.get("comfyui.installation_path", "ComfyUI-master")
        return str(self.project_root / install_path)
    
    def get_generation_settings(self) -> Dict[str, Any]:
        """Get image generation settings."""
        settings = self.get("generation", {})
        
        # Override with environment variables if available
        env_overrides = {
            "width": self.get_env("IMAGE_WIDTH"),
            "height": self.get_env("IMAGE_HEIGHT"),
            "steps": self.get_env("GENERATION_STEPS"),
            "cfg_scale": self.get_env("CFG_SCALE"),
            "sampler_name": self.get_env("SAMPLER_NAME"),
            "scheduler": self.get_env("SCHEDULER"),
        }
        
        # Apply environment overrides
        dimensions = settings.get("dimensions", {})
        sampling = settings.get("sampling", {})
        
        for key, value in env_overrides.items():
            if value is not None:
                if key in ["width", "height"]:
                    dimensions[key] = int(value)
                elif key in ["steps"]:
                    sampling[key] = int(value)
                elif key in ["cfg_scale"]:
                    sampling["cfg_scale"] = float(value)
                elif key in ["sampler_name", "scheduler"]:
                    sampling[key] = value
        
        settings["dimensions"] = dimensions
        settings["sampling"] = sampling
        return settings
    
    def get_color_mode_config(self, color_mode: str) -> Dict[str, Any]:
        """
        Get configuration for a specific color mode.
        
        Args:
            color_mode: Color mode name (color, black_and_white)
            
        Returns:
            Color mode configuration
        """
        return self.get(f"color_modes.{color_mode}", {})
    
    def get_prompt_config(self) -> Dict[str, Any]:
        """Get prompt configuration."""
        return self.get("prompts", {})
    
    def get_output_config(self) -> Dict[str, Any]:
        """Get output configuration."""
        return self.get("output", {})
    
    def get_validation_config(self) -> Dict[str, Any]:
        """Get validation configuration."""
        return self.get("validation", {})
    
    def is_feature_enabled(self, feature_name: str) -> bool:
        """
        Check if a feature is enabled.
        
        Args:
            feature_name: Name of the feature
            
        Returns:
            True if feature is enabled
        """
        return self.get(f"features.{feature_name}", False)
    
    def get_debug_config(self) -> Dict[str, Any]:
        """Get debug configuration."""
        return self.get("debug", {})
    
    def validate_model_paths(self) -> Dict[str, bool]:
        """
        Validate that all required model files exist.
        
        Returns:
            Dictionary mapping model paths to existence status
        """
        validation_results = {}
        
        # Check all model types
        model_types = ["checkpoint", "vae", "controlnet", "t2i_adapter", "lora", "ip_adapter", "embeddings"]
        
        for model_type in model_types:
            models = self.get(f"models.{model_type}", {})
            for model_name, model_config in models.items():
                if isinstance(model_config, dict) and 'path' in model_config:
                    model_path = self.project_root / model_config['path']
                    validation_results[model_config['path']] = model_path.exists()
        
        return validation_results
    
    def validate_workflow_paths(self) -> Dict[str, bool]:
        """
        Validate that all workflow template files exist.
        
        Returns:
            Dictionary mapping workflow paths to existence status
        """
        validation_results = {}
        
        workflows = self.get("workflows", {})
        for workflow_name, workflow_config in workflows.items():
            if isinstance(workflow_config, dict) and 'template' in workflow_config:
                workflow_path = self.project_root / workflow_config['template']
                validation_results[workflow_config['template']] = workflow_path.exists()
        
        return validation_results
    
    def get_missing_models(self) -> list:
        """Get list of missing model files."""
        validation = self.validate_model_paths()
        return [path for path, exists in validation.items() if not exists]
    
    def get_missing_workflows(self) -> list:
        """Get list of missing workflow files."""
        validation = self.validate_workflow_paths()
        return [path for path, exists in validation.items() if not exists]
    
    def reload(self):
        """Reload configuration from files."""
        self.settings = self._load_settings()
        self._path_cache.clear()
        
        # Reload environment variables
        if self.env_file.exists():
            load_dotenv(self.env_file, override=True)


# Global configuration instance
_config_instance = None

def get_config() -> ConfigManager:
    """Get global configuration instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = ConfigManager()
    return _config_instance

def reload_config():
    """Reload global configuration."""
    global _config_instance
    if _config_instance is not None:
        _config_instance.reload()
    else:
        _config_instance = ConfigManager()


if __name__ == "__main__":
    # Test configuration manager
    config = ConfigManager()
    
    print("=== Configuration Manager Test ===")
    print(f"ComfyUI URL: {config.get_comfyui_url()}")
    print(f"ComfyUI Installation: {config.get_comfyui_installation_path()}")
    print(f"Checkpoint model: {config.get_model_path('checkpoint')}")
    print(f"Generation settings: {config.get_generation_settings()}")
    
    print("\n=== Model Validation ===")
    missing_models = config.get_missing_models()
    if missing_models:
        print("Missing models:")
        for model in missing_models:
            print(f"  - {model}")
    else:
        print("All models found!")
    
    print("\n=== Workflow Validation ===")
    missing_workflows = config.get_missing_workflows()
    if missing_workflows:
        print("Missing workflows:")
        for workflow in missing_workflows:
            print(f"  - {workflow}")
    else:
        print("All workflows found!")