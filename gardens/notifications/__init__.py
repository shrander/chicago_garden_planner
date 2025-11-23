"""
Garden notification system for tracking planting and harvest schedules.

This module provides functionality for calculating and formatting notifications
about garden tasks such as seed starting, transplanting, planting, and harvesting.
"""

from .calculators import calculate_garden_notifications

__all__ = ['calculate_garden_notifications']
