from typing import TypedDict, List



class TranslateState(TypedDict):
    original: str

    # 청크 단위로 채워갈 예정이여서 List로 변경
    translated: List[str]