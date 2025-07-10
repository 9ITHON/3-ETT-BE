#!/bin/bash

# Docker 이미지 빌드
docker build -t ett-be-app .

# Docker 컨테이너 실행
docker run -p 8000:8000 --env-file .env ett-be-app
