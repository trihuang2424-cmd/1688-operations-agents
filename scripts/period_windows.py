#!/usr/bin/env python3
"""Compute ended operating periods. No network, business data or state writes."""
import argparse
import json
from datetime import date, timedelta


def window(start, end):
    return {'start': start.isoformat(), 'end': end.isoformat(),
            'calendar_days': (end - start).days + 1}


def prior_month(start):
    end = start.replace(day=1) - timedelta(days=1)
    return end.replace(day=1), end


def review_windows(as_of):
    if not isinstance(as_of, date) or type(as_of) is not date:
        raise ValueError('as_of must be a local calendar date')
    this_monday = as_of - timedelta(days=as_of.weekday())
    week_start, week_end = this_monday - timedelta(days=7), this_monday - timedelta(days=1)
    month_start, month_end = prior_month(as_of)
    baseline_start, baseline_end = prior_month(month_start)
    return {
        'timezone': 'Asia/Shanghai', 'as_of': as_of.isoformat(),
        'data_completeness': 'not_checked',
        'weekly': {
            'current': window(week_start, week_end),
            'baseline_basis': 'four_weeks_same_weekdays',
            'baseline': window(week_start - timedelta(days=28), week_end - timedelta(days=28)),
            'trend': window(week_start - timedelta(days=7), week_end - timedelta(days=7)),
        },
        'monthly': {
            'current': window(month_start, month_end),
            'baseline_basis': 'previous_complete_calendar_month',
            'baseline': window(baseline_start, baseline_end),
            'show_totals_and_daily_averages': True,
        },
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--as-of', required=True, help='Asia/Shanghai local date, YYYY-MM-DD')
    args = parser.parse_args(argv)
    try:
        result = review_windows(date.fromisoformat(args.as_of))
    except (ValueError, OverflowError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
