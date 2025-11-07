from django.test import TestCase
from .models import Series
from genre.models import Genre

class SeriesModelTest(TestCase):
    def setUp(self):
        self.genre = Genre.objects.create(name='액션')
        self.series = Series.objects.create(
            title='테스트 애니메이션',
            description='테스트 설명'
        )
        self.series.genres.add(self.genre)

    def test_series_creation(self):
        """시리즈 생성 테스트"""
        self.assertEqual(self.series.title, '테스트 애니메이션')
        self.assertEqual(self.series.description, '테스트 설명')
        self.assertEqual(self.series.genres.count(), 1)
        self.assertEqual(self.series.genres.first().name, '액션')

    def test_series_str_method(self):
        """시리즈 문자열 표현 테스트"""
        self.assertEqual(str(self.series), '테스트 애니메이션')

    def test_series_photo_optional(self):
        """시리즈 사진 필드가 선택사항인지 테스트"""
        series = Series.objects.create(title='사진없는 애니메이션')
        self.assertTrue(series.photo in (None, ''))  # photo가 None이거나 빈 문자열
