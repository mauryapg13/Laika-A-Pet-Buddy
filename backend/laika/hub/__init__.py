"""Laika device model: the hub's brain. JSON in, JSON out.

    config.py  limits, button/node map, choice tokens
    hub.py     Hub class: node state machine + the 6 features
    ml.py      learned pull threshold, anomaly detector, daily summary
"""
from .hub import Hub

__all__ = ["Hub"]
