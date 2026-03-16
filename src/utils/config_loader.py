"""
Configuration Loader

Handles loading and parsing of configuration files.
"""

import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path
from dotenv import load_dotenv


class ConfigLoader:
    """Configuration loader with environment variable substitution."""

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize config loader.

        Args:
            config_path: Path to config file (defaults to config/config.yaml)
        """
        self.config_path = config_path or self._find_config_file()
        self.config: Dict[str, Any] = {}

        # Load environment variables
        load_dotenv()

    def _find_config_file(self) -> str:
        """
        Find config file in standard locations.

        Returns:
            Path to config file
        """
        possible_paths = [
            "config/config.yaml",
            "../config/config.yaml",
            "../../config/config.yaml",
        ]

        for path in possible_paths:
            if os.path.exists(path):
                return path

        # Default fallback
        return "config/config.yaml"

    def load(self) -> Dict[str, Any]:
        """
        Load configuration from file.

        Returns:
            Configuration dictionary
        """
        try:
            with open(self.config_path, 'r') as f:
                self.config = yaml.safe_load(f)

            # Substitute environment variables
            self.config = self._substitute_env_vars(self.config)

            return self.config

        except FileNotFoundError:
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in config file: {e}")

    def _substitute_env_vars(self, config: Any) -> Any:
        """
        Recursively substitute environment variables in config.

        Args:
            config: Configuration object (dict, list, or value)

        Returns:
            Configuration with substituted values
        """
        if isinstance(config, dict):
            return {
                key: self._substitute_env_vars(value)
                for key, value in config.items()
            }
        elif isinstance(config, list):
            return [self._substitute_env_vars(item) for item in config]
        elif isinstance(config, str):
            return self._substitute_string(config)
        else:
            return config

    def _substitute_string(self, value: str) -> str:
        """
        Substitute environment variables in a string.

        Supports ${VAR_NAME} syntax.

        Args:
            value: String value

        Returns:
            String with substituted values
        """
        if not value.startswith("${") or not value.endswith("}"):
            return value

        var_name = value[2:-1]
        env_value = os.getenv(var_name)

        if env_value is None:
            # Return original placeholder if not found
            return value

        return env_value

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key.

        Supports dot notation (e.g., "llm_provider.openai.api_key").

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self.config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any) -> None:
        """
        Set configuration value.

        Supports dot notation.

        Args:
            key: Configuration key
            value: Value to set
        """
        keys = key.split('.')
        config = self.config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value

    def save(self, path: Optional[str] = None) -> None:
        """
        Save configuration to file.

        Args:
            path: Path to save to (defaults to original path)
        """
        save_path = path or self.config_path

        with open(save_path, 'w') as f:
            yaml.dump(self.config, f, default_flow_style=False)


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Convenience function to load configuration.

    Args:
        config_path: Path to config file

    Returns:
        Configuration dictionary
    """
    loader = ConfigLoader(config_path)
    return loader.load()
