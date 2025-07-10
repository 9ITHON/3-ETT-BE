import os
from dotenv import load_dotenv

load_dotenv()


class Global:
    class env:
        OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")

    @classmethod
    def validate_env(cls):
        from pydantic import BaseModel, Field

        class EnvValidator(BaseModel):
            OPENAI_API_KEY: str = Field(..., min_length=1, description="OpenAI API 키")

        try:
            EnvValidator(
                OPENAI_API_KEY=cls.env.OPENAI_API_KEY,
            )
        except Exception as e:
            raise ValueError(f"환경변수 검증 실패: {str(e)}")
