import unittest
from update_profile_stats import parse_calendar, summarize, render

class ContributionStatsTests(unittest.TestCase):
    def days(self, counts):
        return [{'date': f'2026-10-{i+1:02d}', 'count': n} for i, n in enumerate(counts)]
    def test_streaks_and_average_use_active_days(self):
        stats = summarize(self.days([0, 2, 4, 0, 8, 0]))
        self.assertEqual(stats['total_contributions'], 14)
        self.assertEqual(stats['active_days'], 3)
        self.assertEqual(stats['longest_streak'], 2)
        self.assertEqual(stats['current_streak'], 1)
        self.assertEqual(stats['avg_per_active_day'], 4.7)
    def test_only_today_can_be_skipped_in_current_streak(self):
        self.assertEqual(summarize(self.days([3, 0, 0]))['current_streak'], 0)
        self.assertEqual(summarize(self.days([1, 2, 3]))['current_streak'], 3)
    def test_zero_activity(self):
        stats = summarize(self.days([0, 0]))
        self.assertEqual(stats['avg_per_active_day'], 0)
        self.assertEqual(stats['longest_streak'], 0)
        self.assertIn('height="0.0"', render(stats))
    def test_zero_day_with_missing_date_is_not_silently_discarded(self):
        for attrs in ['id="a"', 'data-date="2026-10-01"']:
            with self.assertRaises(ValueError):
                parse_calendar(f'<td class="ContributionCalendar-day" {attrs}></td><tool-tip for="a">No contributions on October.</tool-tip>')
    def test_tooltip_mapping_not_dom_order(self):
        html = '<td class="ContributionCalendar-day" id="b" data-date="2026-10-02"></td><td class="ContributionCalendar-day" id="a" data-date="2026-10-01"></td><tool-tip for="a">1 contribution on October 1st.</tool-tip><tool-tip for="b">1,234 contributions on October 2nd.</tool-tip>'
        self.assertEqual(parse_calendar(html), self.days([1, 1234]))
    def test_unknown_count_or_missing_date_fails(self):
        with self.assertRaises(ValueError):
            parse_calendar('<td class="ContributionCalendar-day" id="a" data-date="2026-10-01"></td>')
        html = ''.join(f'<td class="ContributionCalendar-day" id="d{i}" data-date="2026-10-{i:02d}"></td><tool-tip for="d{i}">No contributions on October.</tool-tip>' for i in [1, 3])
        with self.assertRaises(ValueError):
            parse_calendar(html)

if __name__ == '__main__':
    unittest.main()
