from django.core.management.base import BaseCommand, CommandError
from django.core.files import File
from django.db import transaction
from series.models import Series
from season.models import Season
from episode.models import Episode
from genre.models import Genre
import csv
import os
import re

class Command(BaseCommand):
    help = "CSV(title,description,season,episode,episode_title,content,genre)와 이미지를 Series/Episodes로 import"

    def add_arguments(self, parser):
        parser.add_argument("csv_path", type=str)
        parser.add_argument("--image", help="시리즈 이미지 파일 경로")
        parser.add_argument("--update", action="store_true", help="기존 에피소드 제목/내용/시리즈 설명/장르 업데이트")

    def open_csv(self, path):
        for enc in ("utf-8-sig", "cp949", "utf-8"):
            try:
                return open(path, "r", encoding=enc, newline="")
            except UnicodeDecodeError:
                continue
        raise CommandError("CSV 인코딩을 읽을 수 없습니다. utf-8-sig 또는 cp949로 저장해보세요.")

    def parse_genres(self, raw):
        if not raw:
            return []
        parts = [p.strip() for p in re.split(r"[,\;，]", raw) if p.strip()]
        return parts

    @transaction.atomic
    def handle(self, *args, **options):
        csv_path = options["csv_path"]
        image_path = options.get("image")
        do_update = options["update"]

        f = self.open_csv(csv_path)
        reader = csv.DictReader(f)
        required = {"title", "description", "season", "episode", "episode_title", "content"}
        if not required.issubset(set(reader.fieldnames or [])):
            raise CommandError(f"CSV 헤더는 {required} 가 모두 필요합니다. 현재: {reader.fieldnames}")

        rows = list(reader)
        if not rows:
            raise CommandError("CSV에 데이터 행이 없습니다.")

        # 시리즈 정보은 첫 행의 title/description 사용
        first_row = rows[0]
        series_title = (first_row.get("title") or "").strip()
        series_description = (first_row.get("description") or "").strip()

        # 모든 행에서 genre 컬럼 수집 (빈값 무시)
        genre_names_set = set()
        if "genre" in (reader.fieldnames or []):
            for r in rows:
                raw = r.get("genre", "") or ""
                for g in self.parse_genres(raw):
                    genre_names_set.add(g)

        # Series 생성 및 업데이트
        series, created = Series.objects.get_or_create(
            title=series_title,
            defaults={"description": series_description}
        )
        if not created and do_update:
            series.description = series_description
            series.save()
        elif created:
            # ensure description set if created
            if series.description != series_description:
                series.description = series_description
                series.save()

        # 장르 처리: through 테이블에 series_id, genre_id로 매핑 (기존 매핑 삭제 후 재생성)
        if genre_names_set:
            genre_objs = []
            for gname in genre_names_set:
                obj, _ = Genre.objects.get_or_create(name=gname)
                genre_objs.append(obj)

            through_model = series.genres.through
            # 기존 매핑 삭제
            through_model.objects.filter(series_id=series.pk).delete()
            # 새로 삽입
            for g in genre_objs:
                through_model.objects.get_or_create(series_id=series.pk, genre_id=g.pk)

        # 이미지 처리
        if image_path and os.path.exists(image_path):
            with open(image_path, 'rb') as img_file:
                series.photo.save(
                    os.path.basename(image_path),
                    File(img_file),
                    save=True
                )

        # 에피소드 처리 (모든 행 순회)
        created_eps = 0
        updated_eps = 0

        for i, row in enumerate(rows, start=1):
            try:
                season_number = int(row["season"])
                episode_number = int(row["episode"])
            except (ValueError, TypeError):
                raise CommandError(f"{i}행: season/episode가 정수가 아닙니다. 값={row}")

            title = (row.get("episode_title") or "").strip()
            content = row.get("content") or ""

            season, _ = Season.objects.get_or_create(series=series, season_number=season_number)
            ep, ep_created = Episode.objects.get_or_create(
                season=season,
                episode_number=episode_number,
                defaults={"episode_title": title, "content": content},
            )
            if ep_created:
                created_eps += 1
            else:
                if do_update:
                    changed = False
                    if title and ep.episode_title != title:
                        ep.episode_title = title
                        changed = True
                    if ep.content != content:
                        ep.content = content
                        changed = True
                    if changed:
                        ep.save()
                        updated_eps += 1

        self.stdout.write(self.style.SUCCESS(
            f"완료: 생성 {created_eps}개" + (f", 업데이트 {updated_eps}개" if do_update else "")
        ))