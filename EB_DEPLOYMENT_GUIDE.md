# AWS Elastic Beanstalk 배포 가이드

## 📋 사전 준비사항

### 1. AWS IAM 사용자 생성
1. AWS Console → IAM → Users → Create User
2. 권한 정책 연결:
   - `AWSElasticBeanstalkFullAccess`
   - `AmazonS3FullAccess`
3. Access Key 생성 (나중에 GitHub Secrets에 등록)

### 2. GitHub Secrets 설정
Repository → Settings → Secrets and variables → Actions → New repository secret

필수 Secrets:
```
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=ap-northeast-2
EB_APPLICATION_NAME=spoil-backend
EB_ENVIRONMENT_NAME=spoil-backend-env
```

---

## 🚀 Elastic Beanstalk 환경 생성

### 1. EB CLI 설치 (선택사항)
```bash
pip install awsebcli
```

### 2. AWS Console에서 EB 환경 생성

#### Step 1: Application 생성
- Application name: `spoil-backend`
- Platform: Python 3.11
- Platform branch: Python 3.11 running on 64bit Amazon Linux 2023

#### Step 2: Environment 설정
- Environment name: `spoil-backend-env`
- Domain: 자동 생성 또는 직접 입력

#### Step 3: Network 설정
- VPC: Default VPC 선택
- Instance subnets: 모든 AZ 선택
- Public IP: ✅ Enabled

#### Step 4: Capacity 설정
- Environment type: **Single instance** (Free Tier)
- Instance type: t3.micro

#### Step 5: Database 설정
- ❌ Enable database 체크 안 함 (RDS는 별도 생성 권장)

---

## 🔐 EB 환경 변수 설정

EB Console → Configuration → Software → Environment properties

필수 환경 변수:
```
SECRET_KEY=django-insecure-your-secret-key
DEBUG=False
KAKAO_SECRET_KEY=your-kakao-key
KAKAO_REDIRECT_URI=https://your-domain.com/api/user/kakao/callback/
KAKAO_CLIENT_SECRET=your-kakao-client-secret
OPENAI_API_KEY=sk-...
CHANNEL_ACCESS_KEY=your-channel-key
CHANNEL_ACCESS_SECRET=your-channel-secret
DATABASE_URL=postgresql://user:pass@host:5432/dbname
ALLOWED_HOSTS=.elasticbeanstalk.com,yourdomain.com
```

---

## 🗄️ RDS PostgreSQL 설정 (선택사항)

### 1. RDS 인스턴스 생성
- Engine: PostgreSQL 15
- Template: Free tier
- DB instance class: db.t3.micro
- Storage: 20GB
- VPC: EB와 동일한 VPC
- Public access: No (보안 강화)

### 2. 보안 그룹 설정
RDS Security Group Inbound Rules:
```
Type: PostgreSQL (5432)
Source: [EB 인스턴스 보안 그룹]
```

### 3. DATABASE_URL 생성
```
postgresql://username:password@endpoint:5432/database_name
```
→ EB 환경 변수에 등록

---

## 📦 S3 미디어 파일 설정 (필수)

### 1. S3 버킷 생성
```bash
# AWS Console에서 생성
Bucket name: spoil-backend-media
Region: ap-northeast-2 (서울)
Block all public access: ❌ (미디어 파일 공개)
```

### 2. django-storages 설정
```bash
# requirements.txt에 추가
django-storages[s3]==1.14.2
boto3==1.34.51
```

### 3. settings.py 업데이트
```python
# S3 Settings (환경 변수로 관리)
if not DEBUG:
    AWS_ACCESS_KEY_ID = env('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = env('AWS_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = env('AWS_STORAGE_BUCKET_NAME')
    AWS_S3_REGION_NAME = 'ap-northeast-2'
    AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
    
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/media/'
```

---

## 🔄 배포 프로세스

### 자동 배포 (GitHub Actions)
```bash
# main 브랜치에 push
git add .
git commit -m "Deploy to EB"
git push origin main

# GitHub Actions가 자동으로:
# 1. 테스트 실행
# 2. EB에 배포
# 3. 결과 확인
```

### 수동 배포 (EB CLI)
```bash
# 초기 설정
eb init -p python-3.11 spoil-backend --region ap-northeast-2

# 환경 생성 (최초 1회)
eb create spoil-backend-env --single

# 배포
eb deploy

# 로그 확인
eb logs

# SSH 접속
eb ssh

# 환경 상태 확인
eb status
```

---

## 🐛 트러블슈팅

### 1. 배포 실패 시
```bash
# EB 로그 확인
eb logs

# AWS Console → Elastic Beanstalk → Logs → Request Logs
```

### 2. 환경 변수 누락
```bash
# EB Console → Configuration → Software
# 모든 필수 환경 변수 확인
```

### 3. Static 파일 404
```bash
# SSH 접속 후
eb ssh
cd /var/app/current
source /var/app/venv/*/bin/activate
python manage.py collectstatic --noinput
```

### 4. RDS 연결 실패
```bash
# 보안 그룹 확인
# RDS Inbound: EB 보안 그룹 허용 확인
# DATABASE_URL 형식 확인
```

---

## 📊 모니터링

### CloudWatch 로그
- Application logs
- Web server logs
- EB health status

### EB 헬스 체크
- URL: `/` (기본)
- Timeout: 5초
- Interval: 30초

---

## 💰 비용 예상 (Free Tier 12개월)

```
✅ EC2 t3.micro: $0
✅ RDS t3.micro: $0
✅ S3 (5GB): $0
✅ 데이터 전송 (15GB/월): $0
━━━━━━━━━━━━━━━━━━━
총: $0/월

⚠️ Free Tier 만료 후:
- EC2: ~$8/월
- RDS: ~$15/월
- S3: ~$0.12/월
━━━━━━━━━━━━━━━━━━━
총: ~$23/월
```

---

## 🔗 유용한 명령어

```bash
# EB 상태 확인
eb status

# 환경 열기
eb open

# 로그 스트리밍
eb logs --stream

# 환경 재시작
eb restart

# 환경 종료 (비용 절약)
eb terminate spoil-backend-env

# 환경 변수 설정
eb setenv DEBUG=False SECRET_KEY=your-key
```

---

## ✅ 체크리스트

배포 전:
- [ ] AWS IAM 사용자 생성
- [ ] GitHub Secrets 등록
- [ ] EB 환경 생성
- [ ] EB 환경 변수 설정
- [ ] RDS 생성 및 연결
- [ ] S3 버킷 생성
- [ ] `requirements.txt` 업데이트

배포 후:
- [ ] 헬스 체크 확인
- [ ] Static 파일 로드 확인
- [ ] 미디어 파일 업로드 테스트
- [ ] API 엔드포인트 테스트
- [ ] 관리자 페이지 접근 확인

---

## 📞 문제 발생 시

1. GitHub Actions 로그 확인
2. EB Console → Logs 확인
3. CloudWatch 로그 확인
4. `eb ssh`로 직접 접속하여 디버깅
