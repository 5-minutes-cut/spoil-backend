from django.test import TestCase
from django.db import IntegrityError
from .models import Genre
from series.models import Series

class GenreModelTest(TestCase):
    def setUp(self):
        self.genre = Genre.objects.create(name='액션')
        self.series = Series.objects.create(title='테스트 애니메이션')
        self.series.genres.add(self.genre)

    def test_genre_creation(self):
        """장르 생성 테스트"""
        self.assertEqual(self.genre.name, '액션')

    def test_genre_str_method(self):
        """장르 문자열 표현 테스트"""
        self.assertEqual(str(self.genre), '액션')

    def test_unique_name_constraint(self):
        """장르 이름 unique 제약 조건 테스트"""
        with self.assertRaises(IntegrityError):
            Genre.objects.create(name='액션')

    def test_genre_series_relation(self):
        """장르와 시리즈 관계 테스트"""
        self.assertEqual(self.genre.series.count(), 1)
        self.assertEqual(self.genre.series.first(), self.series)

        # 여러 시리즈에 같은 장르 추가 가능
        another_series = Series.objects.create(title='다른 애니메이션')
        another_series.genres.add(self.genre)
        self.assertEqual(self.genre.series.count(), 2)
