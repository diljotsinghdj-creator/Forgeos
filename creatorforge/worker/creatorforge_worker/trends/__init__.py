"""Trend Radar: finds what people are watching and searching this week, month or year,
groups the signals into topics, and turns a topic into video ideas and grounded scripts."""
from .radar import PERIODS, TrendRadar
from .niches import NICHES, REGIONS

__all__ = ["NICHES", "PERIODS", "REGIONS", "TrendRadar"]
