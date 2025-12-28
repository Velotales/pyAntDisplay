#!/usr/bin/env python3
"""
PyANTDisplay - Configuration Loader

Copyright (c) 2025 Velotales

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

Handles configuration file loading and merging.
"""

from typing import Any, Dict, Optional

try:
    import yaml  # type: ignore
except Exception:
    yaml = None

from colorama import Fore, Style


class ConfigLoader:
    """Handles configuration file loading and merging."""

    def load_app_config(
        self, app_config: str, local_config: Optional[str] = None
    ) -> Dict[str, Any]:
        """Load application configuration with optional local overrides."""
        if yaml is None:
            print(
                f"{Fore.RED}PyYAML not available, using empty config{Style.RESET_ALL}"
            )
            return {}

        # Load base config
        try:
            with open(app_config, "r") as f:
                base = yaml.safe_load(f) or {}
        except Exception:
            base = {}

        # Merge local config if provided
        if local_config:
            try:
                with open(local_config, "r") as f:
                    local = yaml.safe_load(f) or {}
                base = self._deep_merge(base, local)
            except Exception:
                pass

        return base

    def _deep_merge(self, a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries."""
        out = dict(a)
        for k, v in (b or {}).items():
            if isinstance(v, dict) and isinstance(out.get(k), dict):
                out[k] = self._deep_merge(out[k], v)
            else:
                out[k] = v
        return out
