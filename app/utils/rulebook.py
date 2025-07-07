import re
from typing import Dict, Any

patterns = {
    # 개인 정보
    "이름": re.compile(r"""
        (?:성명|이름)   # '성명' 또는 '이름'
        \s*            # 콜론 앞뒤의 공백 허용
        [ :：]         # ASCII 콜론 또는 fullwidth 콜론
        \s*            # 콜론 뒤 공백 허용
        ([가-힣]{2,4}) # 실제 이름(2~4글자)
    """, re.VERBOSE),
    "주민등록번호": re.compile(r"[0-9]{6}-[0-9]{7}"), #외국인 등록 번호도 이와 동일
    "운전면허번호": re.compile(r"[0-9]{2}-[0-9]{2}-[0-9]{6}-[0-9]{2}"),
    "건강보험증번호" : re.compile(r"[0-9]{11}"),

    # 계좌 번호는 직접 안써서 보내지 않나 싶음.
    # 사업자 등록 번호
    "사업자등록번호" : re.compile(r"[0-9]{3}-[0-9]{2}-[0-9]{5}"),
    "법인등록번호" : re.compile(r"법인등록번호\s*[:：]?\s*[0-9]{6}-[0-9]{7}"),

    # 연락처
    "전화번호":  re.compile(r"01[016789]-[0-9]{3,4}-[0-9]{4}"),
    "이메일": re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+"),
    
    # 집 주소는 정확할 것이라고 생각.
    "주소": re.compile(r"""
         (?:주소[:：]?\s*)?                                   
        (?:(?P<province>[가-힣]+?(?:도|광역시|특별시|시))\s+)?  
        (?P<city>[가-힣]+?(?:시|군|구))                       
        \s+
        (?P<district>[가-힣]+?(?:구|읍|면|동|리))               
        \s+
        (?P<street>[가-힣0-9]+?(?:로|길))                     
        \s*
        (?P<number>\d+) 
    """, re.VERBOSE),
    # "우편번호" : re.compile(r"(?<!\d)[0-9]{5}(?!\d)"),
}

def validate_rulebook(text: str) -> list[str]:
    return [
        key
        for key, regex in patterns.items()
        if regex.search(text)
    ]
