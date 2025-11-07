from django.test import TestCase
from django.db import IntegrityError
from .models import Episode
from season.models import Season
from series.models import Series

class EpisodeModelTest(TestCase):
    def setUp(self):
        self.series = Series.objects.create(title='테스트 애니메이션')
        self.season = Season.objects.create(
            series=self.series,
            season_number=1
        )
        self.episode = Episode.objects.create(
            season=self.season,
            episode_number=1,
            episode_title='첫 번째 에피소드',
            content='에피소드 내용'
        )

    def test_episode_creation(self):
        """에피소드 생성 테스트"""
        self.assertEqual(self.episode.season, self.season)
        self.assertEqual(self.episode.episode_number, 1)
        self.assertEqual(self.episode.episode_title, '첫 번째 에피소드')
        self.assertEqual(self.episode.content, '에피소드 내용')

    def test_episode_str_method(self):
        """에피소드 문자열 표현 테스트"""
        expected = f"{self.series.title} S1E1"
        self.assertEqual(str(self.episode), expected)

    def test_unique_together_constraint(self):
        """시즌과 에피소드 번호의 unique_together 제약 조건 테스트"""
        with self.assertRaises(IntegrityError):
            # 같은 시즌에 같은 에피소드 번호를 가진 에피소드를 생성
            Episode.objects.create(
                season=self.season,
                episode_number=1,
                episode_title='중복 에피소드'
            )

    def test_ordering(self):
        """에피소드 정렬 순서 테스트"""
        episode2 = Episode.objects.create(
            season=self.season,
            episode_number=2,
            episode_title='두 번째 에피소드'
        )
        episodes = Episode.objects.all()
        self.assertEqual(episodes[0], self.episode)  # episode_number=1
        self.assertEqual(episodes[1], episode2)      # episode_number=2

    def test_content_optional(self):
        """에피소드 내용이 선택사항인지 테스트"""
        episode = Episode.objects.create(
            season=self.season,
            episode_number=3,
            episode_title='내용 없는 에피소드'
        )
        self.assertIsNone(episode.content)
