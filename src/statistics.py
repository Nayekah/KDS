from __future__ import annotations

import math


def mean(values: list[float]) -> float:
    return sum(values) / len(values)


def median(values: list[float]) -> float:
    ordered = sorted(values)
    n = len(ordered)
    mid = n // 2
    if n % 2:
        return ordered[mid]
    return (ordered[mid - 1] + ordered[mid]) / 2


def pearson(x: list[float], y: list[float]) -> float:
    mx = mean(x)
    my = mean(y)
    sx = math.sqrt(sum((v - mx) ** 2 for v in x))
    sy = math.sqrt(sum((v - my) ** 2 for v in y))
    if sx == 0 or sy == 0:
        return 0.0
    return sum((a - mx) * (b - my) for a, b in zip(x, y)) / (sx * sy)


def rank(values: list[float]) -> list[float]:
    indexed = sorted((v, i) for i, v in enumerate(values))
    ranks = [0.0] * len(values)
    i = 0
    while i < len(indexed):
        j = i
        while j + 1 < len(indexed) and indexed[j + 1][0] == indexed[i][0]:
            j += 1
        avg = (i + j + 2) / 2
        for k in range(i, j + 1):
            ranks[indexed[k][1]] = avg
        i = j + 1
    return ranks


def spearman(x: list[float], y: list[float]) -> float:
    return pearson(rank(x), rank(y))


def simple_regression(x: list[float], y: list[float]) -> tuple[float, float, float]:
    mx = mean(x)
    my = mean(y)
    sxx = sum((v - mx) ** 2 for v in x)
    if sxx == 0:
        return my, 0.0, 0.0
    slope = sum((a - mx) * (b - my) for a, b in zip(x, y)) / sxx
    intercept = my - slope * mx
    yhat = [intercept + slope * v for v in x]
    ss_tot = sum((v - my) ** 2 for v in y)
    ss_res = sum((obs - pred) ** 2 for obs, pred in zip(y, yhat))
    r2 = 1 - ss_res / ss_tot if ss_tot else 0.0
    return intercept, slope, r2


def clamp_probability(value: float) -> float:
    return min(max(value, 1e-6), 1 - 1e-6)
