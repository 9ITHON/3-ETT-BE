from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from app.agent.easyTranslate.prompt import EasyTranslatePrompt
from app.agent.easyTranslate.state import TranslateState
from app.config import Global
from app.utils.logger import logger


class EasyTranslateNode:
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", EasyTranslatePrompt.system_prompt),
            ("user", "{original}")
        ])
        logger.debug(f"EasyTranslateNode 초기화 - 스트리밍 모드: {llm.streaming}")

    def invoke(self, state: TranslateState) -> TranslateState:
        """한 번에 전체 번역 (non-streaming 모드)"""
        logger.debug(f"번역 노드 실행 - 원문: {state['original'][:50]}...")
        
        try:
            # 프롬프트 준비
            prompt = self.prompt_template.format_prompt(
                original=state["original"]
            ).to_messages()
            
            # LLM에 prompt 전달하여 번역 결과 얻기
            response = self.llm.invoke(prompt)
            state["translated"].append(response.content)
            
            logger.debug(f"번역 노드 완료 - 결과: {response.content[:50]}...")
            
            return state
            
        except Exception as e:
            logger.error(f"번역 노드 에러: {str(e)}")
            raise

    async def ainvoke(self, state: TranslateState):
        """스트리밍 모드로 토큰 단위 chunk 생성"""
        logger.debug(f"스트리밍 번역 노드 실행 - 원문: {state['original'][:50]}...")
        
        try:
            # 프롬프트 준비
            prompt = self.prompt_template.format_prompt(
                original=state["original"]
            ).to_messages()

            # astream() 으로 async iterator 얻기
            token_count = 0
            async for token in self.llm.astream(prompt):
                token_count += 1
                
                # token이 str인 경우가 많지만 만약 객체라면 token.content 사용
                chunk = token if isinstance(token, str) else token.content
                state["translated"].append(chunk)
                
                # 주기적으로 로그 (매 50개 토큰마다)
                if token_count % 50 == 0:
                    logger.debug(f"스트리밍 진행 - 토큰 수: {token_count}개")
                
                yield state
                
            logger.debug(f"스트리밍 번역 노드 완료 - 총 토큰: {token_count}개")
            
        except Exception as e:
            logger.error(f"스트리밍 번역 노드 에러: {str(e)}")
            raise