# Render 환경 최적화 Gunicorn 설정
bind = "0.0.0.0:5000"

# Worker 설정 (메모리 제한 고려)
workers = 1  # Render 무료 플랜: 메모리 제한으로 1개만
worker_class = "sync"
worker_connections = 50  # 연결 수 제한

# Timeout 설정 (긴 작업 대응)
timeout = 300  # 30초 → 300초 (파일 처리/임베딩 시간 고려)
keepalive = 5
graceful_timeout = 30

# 메모리 최적화
max_requests = 100  # Worker 재시작 주기
max_requests_jitter = 10  # 랜덤 jitter
preload_app = False  # 메모리 절약

# 로깅
loglevel = "info"
accesslog = "-"
errorlog = "-"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" in %(D)sμs'

# Render 환경 최적화
def when_ready(server):
    server.log.info("Gunicorn 서버 시작 완료 (Render 최적화)")

def worker_int(worker):
    worker.log.info("Worker 인터럽트 - 정리 중...")

def pre_fork(server, worker):
    server.log.info("Worker 시작 중...")

def post_fork(server, worker):
    server.log.info("Worker 준비 완료")