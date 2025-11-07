from django.test import TestCase
from django.db import IntegrityError
from .models import Season
from series.models import Series

class SeasonModelTest(TestCase):
    def setUp(self):
        self.series = Series.objects.create(title='테스트 애니메이션')
        self.season = Season.objects.create(
            series=self.series,
            season_number=1
        )

    def test_season_creation(self):
        """시즌 생성 테스트"""
        self.assertEqual(self.season.series, self.series)
        self.assertEqual(self.season.season_number, 1)

    def test_season_str_method(self):
        """시즌 문자열 표현 테스트"""
        expected = f"{self.series.title} - Season 1"
        self.assertEqual(str(self.season), expected)

    def test_unique_together_constraint(self):
        """시리즈와 시즌 번호의 unique_together 제약 조건 테스트"""
        with self.assertRaises(IntegrityError):
            # 같은 시리즈에 같은 시즌 번호를 가진 시즌을 생성
            Season.objects.create(
                series=self.series,
                season_number=1
            )

    def test_ordering(self):
        """시즌 정렬 순서 테스트"""
        season2 = Season.objects.create(
            series=self.series,
            season_number=2
        )
        seasons = Season.objects.all()
        self.assertEqual(seasons[0], self.season)  # season_number=1
        self.assertEqual(seasons[1], season2)      # season_number=2
