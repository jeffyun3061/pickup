# API 서버 이미지 (관리자 웹 포함 same-origin 서빙)
# Railway: 서비스 Dockerfile Path = Dockerfile, 볼륨을 /data 에 마운트

# ---- 1단계: 관리자 웹 빌드 ----
FROM node:22-alpine AS adminweb
WORKDIR /web
COPY admin/package.json admin/package-lock.json ./
RUN npm ci
COPY admin/ ./
RUN npm run build

# ---- 2단계: FastAPI ----
FROM python:3.12-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

COPY server/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY server/app ./app
COPY --from=adminweb /web/dist ./admin-dist

# 업로드 이미지는 볼륨(/data)에 저장 — 재배포에도 유지
ENV ADMIN_DIST_DIR=/app/admin-dist \
    MEDIA_DIR=/data/media

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s \
  CMD python -c "import os,urllib.request; urllib.request.urlopen(f'http://127.0.0.1:{os.environ.get(\"PORT\",\"8000\")}/health/ready')" || exit 1

# 워커 1개 고정: 인메모리 rate limit·스케줄러 중복 실행 방지 (확장은 나중에)
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1 --proxy-headers --forwarded-allow-ips '*'"]
