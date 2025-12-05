# TODO List for Fixing Issues

## Issue 1: "Flagged for review" not showing for low date confidence
- [x] Update `backend/services/confidence_scorer.py` to add specific check for date confidence < 0.5 to set `needs_review = True`

## Issue 2: AI missing duplicates
- [x] Update `backend/services/duplicate_detector.py` to lower similarity threshold from 85% to 75%
- [x] Adjust weights in similarity calculation to give more importance to vendor (0.4) and amount (0.4), reduce date (0.15) and category (0.05)
