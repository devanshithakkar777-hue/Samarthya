"""Spaced repetition (SM-2). Ratings: 1 again, 3 hard, 4 good, 5 easy."""
from datetime import date, timedelta

RATINGS = {1, 3, 4, 5}


def review(card, rating: int, today: date | None = None) -> None:
    today = today or date.today()
    if rating not in RATINGS:
        raise ValueError("rating must be 1, 3, 4 or 5")
    if rating < 3 or (rating == 1):
        card.reps, card.interval_days = 0, 1
        card.lapses += 1
    else:
        if card.reps == 0:
            card.interval_days = 1
        elif card.reps == 1:
            card.interval_days = 6
        else:
            card.interval_days = max(1, round(card.interval_days * card.ease))
        card.reps += 1
    card.ease = max(1.3, card.ease + (0.1 - (5 - rating) * (0.08 + (5 - rating) * 0.02)))
    card.due = today + timedelta(days=card.interval_days)
