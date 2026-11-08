import unittest
from datetime import date, timedelta

from period_windows import review_windows


class PeriodWindowTests(unittest.TestCase):
    def test_current_operating_example(self):
        result = review_windows(date(2026, 10, 30))
        week = result['weekly']
        self.assertEqual(week['current'], {'start': '2026-10-19', 'end': '2026-10-25', 'calendar_days': 7})
        self.assertEqual(week['baseline']['start'], '2026-09-21')
        self.assertEqual(week['baseline']['end'], '2026-09-27')
        self.assertEqual(week['trend']['start'], '2026-10-12')
        self.assertEqual(result['monthly']['current']['start'], '2026-09-01')
        self.assertEqual(result['monthly']['baseline']['calendar_days'], 31)

    def test_sunday_excludes_the_still_open_day(self):
        self.assertEqual(review_windows(date(2026, 10, 25))['weekly']['current']['end'], '2026-10-18')
        self.assertEqual(review_windows(date(2026, 10, 26))['weekly']['current']['end'], '2026-10-25')

    def test_month_rolls_only_after_last_day(self):
        self.assertEqual(review_windows(date(2026, 10, 31))['monthly']['current']['end'], '2026-09-30')
        self.assertEqual(review_windows(date(2026, 11, 1))['monthly']['current']['end'], '2026-10-31')

    def test_year_rollover(self):
        result = review_windows(date(2027, 1, 1))
        self.assertEqual(result['monthly']['current']['start'], '2026-12-01')
        self.assertEqual(result['monthly']['baseline']['end'], '2026-11-30')
        self.assertEqual(result['weekly']['baseline']['start'], '2026-11-23')

    def test_february_and_leap_year(self):
        for year, days in ((2024, 29), (2025, 28), (2100, 28), (2000, 29)):
            with self.subTest(year=year):
                result = review_windows(date(year, 3, 1))
                self.assertEqual(result['monthly']['current']['calendar_days'], days)
                self.assertEqual(result['monthly']['baseline']['calendar_days'], 31)

    def test_daily_invariants_across_calendar_year(self):
        for offset in range(366):
            as_of = date(2024, 1, 1) + timedelta(days=offset)
            result = review_windows(as_of)
            for role in ('current', 'baseline', 'trend'):
                span = result['weekly'][role]
                start, end = date.fromisoformat(span['start']), date.fromisoformat(span['end'])
                self.assertEqual(start.weekday(), 0)
                self.assertEqual(end.weekday(), 6)
                self.assertEqual((end - start).days, 6)
                self.assertLess(end, as_of)
            for role in ('current', 'baseline'):
                span = result['monthly'][role]
                start, end = date.fromisoformat(span['start']), date.fromisoformat(span['end'])
                self.assertEqual(start.day, 1)
                self.assertEqual((end + timedelta(days=1)).day, 1)
                self.assertLess(end, as_of)
            self.assertEqual(result['data_completeness'], 'not_checked')


if __name__ == '__main__':
    unittest.main()
