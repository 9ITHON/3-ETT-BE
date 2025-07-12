import logging
import sys
import os
from datetime import datetime
from typing import Dict, Any
import json
from pathlib import Path

class CustomFormatter(logging.Formatter):
    """색상과 함께 로그를 포맷하는 커스텀 포맷터"""
    
    # ANSI 색상 코드
    COLORS = {
        'DEBUG': '\033[36m',    # 청록색
        'INFO': '\033[32m',     # 녹색
        'WARNING': '\033[33m',  # 노란색
        'ERROR': '\033[31m',    # 빨간색
        'CRITICAL': '\033[35m', # 자홍색
        'RESET': '\033[0m'      # 리셋
    }
    
    def format(self, record):
        # 로그 레벨에 따른 색상 적용
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']
        
        # 기본 포맷 설정
        log_format = f"{color}[%(asctime)s] %(levelname)s{reset} - %(name)s - %(message)s"
        
        # 추가 정보가 있으면 포함
        if hasattr(record, 'user_id'):
            log_format = f"{color}[%(asctime)s] %(levelname)s{reset} - %(name)s - [User: %(user_id)s] - %(message)s"
        
        if hasattr(record, 'request_id'):
            log_format = f"{color}[%(asctime)s] %(levelname)s{reset} - %(name)s - [ReqID: %(request_id)s] - %(message)s"
            
        formatter = logging.Formatter(log_format, datefmt='%Y-%m-%d %H:%M:%S')
        return formatter.format(record)

class JSONFormatter(logging.Formatter):
    """구조화된 JSON 로그 포맷터"""
    
    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # 추가 컨텍스트 정보 포함
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
        if hasattr(record, 'translation_stats'):
            log_entry['translation_stats'] = record.translation_stats
        if hasattr(record, 'error_details'):
            log_entry['error_details'] = record.error_details
            
        return json.dumps(log_entry, ensure_ascii=False)

class EasyTranslateLogger:
    """쉬운말 번역 서비스 전용 로거"""
    
    def __init__(self, name: str = "easy_translate"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # 중복 핸들러 방지
        if not self.logger.handlers:
            self._setup_handlers()
    
    def _setup_handlers(self):
        """로그 핸들러 설정"""
        # 로그 디렉토리 생성
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # 1. 콘솔 핸들러 (개발용)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(CustomFormatter())
        self.logger.addHandler(console_handler)
        
        # 2. 파일 핸들러 (일반 로그)
        file_handler = logging.FileHandler(
            log_dir / "easy_translate.log",
            encoding='utf-8'
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(CustomFormatter())
        self.logger.addHandler(file_handler)
        
        # 3. JSON 파일 핸들러 (구조화된 로그)
        json_handler = logging.FileHandler(
            log_dir / "easy_translate.json",
            encoding='utf-8'
        )
        json_handler.setLevel(logging.INFO)
        json_handler.setFormatter(JSONFormatter())
        self.logger.addHandler(json_handler)
        
        # 4. 에러 전용 핸들러
        error_handler = logging.FileHandler(
            log_dir / "errors.log",
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(CustomFormatter())
        self.logger.addHandler(error_handler)
    
    def info(self, message: str, **kwargs):
        """일반 정보 로그"""
        self._log_with_context(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """경고 로그"""
        self._log_with_context(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """에러 로그"""
        self._log_with_context(logging.ERROR, message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        """디버그 로그"""
        self._log_with_context(logging.DEBUG, message, **kwargs)
    
    def _log_with_context(self, level: int, message: str, **kwargs):
        """컨텍스트 정보와 함께 로그 기록"""
        extra = {}
        
        # 사용자 ID 추가
        if 'user_id' in kwargs:
            extra['user_id'] = kwargs.pop('user_id')
        
        # 요청 ID 추가
        if 'request_id' in kwargs:
            extra['request_id'] = kwargs.pop('request_id')
        
        # 번역 통계 추가
        if 'translation_stats' in kwargs:
            extra['translation_stats'] = kwargs.pop('translation_stats')
        
        # 에러 상세 정보 추가
        if 'error_details' in kwargs:
            extra['error_details'] = kwargs.pop('error_details')
        
        # 남은 kwargs는 메시지에 포함
        if kwargs:
            message = f"{message} | Context: {kwargs}"
        
        self.logger.log(level, message, extra=extra)
    
    def log_translation_request(self, text: str, user_id: str = None, request_id: str = None):
        """번역 요청 로그"""
        stats = {
            'original_length': len(text),
            'original_word_count': len(text.split()),
            'request_type': 'translation'
        }
        
        self.info(
            f"번역 요청 시작 - 원문 길이: {len(text)}자, 단어 수: {len(text.split())}개",
            user_id=user_id,
            request_id=request_id,
            translation_stats=stats
        )
    
    def log_translation_success(self, original: str, translated: str, 
                              duration: float, user_id: str = None, request_id: str = None):
        """번역 성공 로그"""
        stats = {
            'original_length': len(original),
            'translated_length': len(translated),
            'duration_seconds': duration,
            'compression_ratio': len(translated) / len(original) if original else 0,
            'status': 'success'
        }
        
        self.info(
            f"번역 완료 - 원문: {len(original)}자 → 번역: {len(translated)}자, 소요시간: {duration:.2f}초",
            user_id=user_id,
            request_id=request_id,
            translation_stats=stats
        )
    
    def log_translation_error(self, text: str, error: Exception, 
                            user_id: str = None, request_id: str = None):
        """번역 실패 로그"""
        error_details = {
            'error_type': type(error).__name__,
            'error_message': str(error),
            'original_length': len(text),
            'status': 'failed'
        }
        
        self.error(
            f"번역 실패 - 원문: {len(text)}자, 에러: {type(error).__name__}: {str(error)}",
            user_id=user_id,
            request_id=request_id,
            error_details=error_details
        )
    
    def log_streaming_start(self, text: str, user_id: str = None, request_id: str = None):
        """스트리밍 번역 시작 로그"""
        self.info(
            f"스트리밍 번역 시작 - 원문 길이: {len(text)}자",
            user_id=user_id,
            request_id=request_id,
            translation_stats={'original_length': len(text), 'mode': 'streaming'}
        )
    
    def log_streaming_chunk(self, chunk_count: int, user_id: str = None, request_id: str = None):
        """스트리밍 청크 로그"""
        if chunk_count % 10 == 0:  # 10개마다 로그
            self.debug(
                f"스트리밍 진행 중 - 청크 수: {chunk_count}개",
                user_id=user_id,
                request_id=request_id
            )
    
    def log_streaming_complete(self, total_chunks: int, duration: float, 
                             user_id: str = None, request_id: str = None):
        """스트리밍 완료 로그"""
        stats = {
            'total_chunks': total_chunks,
            'duration_seconds': duration,
            'chunks_per_second': total_chunks / duration if duration > 0 else 0,
            'mode': 'streaming',
            'status': 'completed'
        }
        
        self.info(
            f"스트리밍 완료 - 총 청크: {total_chunks}개, 소요시간: {duration:.2f}초",
            user_id=user_id,
            request_id=request_id,
            translation_stats=stats
        )

# 글로벌 로거 인스턴스
logger = EasyTranslateLogger()