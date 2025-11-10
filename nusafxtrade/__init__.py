# SPDX-License-Identifier: MIT
"""
Top-level package marker for the NusaNexus NoFOMO monorepo.

This file exists so that paths such as ``nusafxtrade.ai_engine`` can be imported
directly during testing without requiring an additional src layout.
"""

from . import ai_engine as ai_engine  # re-export package for convenience

__all__ = ["ai_engine"]
