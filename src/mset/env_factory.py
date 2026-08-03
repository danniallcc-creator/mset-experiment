from __future__ import annotations

from typing import Any

from .config import RunConfig
from .environment import MSETEnvironment
from .market_environment import MarketNetworkEnvironment


def make_environment(config: RunConfig, *args: Any, **kwargs: Any) -> MSETEnvironment:
    if config.environment_variant == "commons":
        return MSETEnvironment(config, *args, **kwargs)
    if config.environment_variant == "market_network":
        return MarketNetworkEnvironment(config, *args, **kwargs)
    raise ValueError(f"unknown environment variant: {config.environment_variant}")
