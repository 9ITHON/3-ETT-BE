from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from app.agent.easyTranslate.prompt import EasyTranslatePrompt
from app.agent.easyTranslate.state import TranslateState
from app.config import Global

class EasyTranslateNode:
    def __init__(self, llm: ChatOpenAI):
        self.llm = ChatOpenAI(model="gpt-4o-mini", api_key=Global.env.OPENAI_API_KEY)
        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", EasyTranslatePrompt.system_prompt),
            ("user", "{original}")
        ])

    def invoke(self, state: TranslateState) -> TranslateState:
        # 한 번에 전체 번역 (스트리밍 모드 아님 / 테스트용?)
        prompt = self.prompt_template.format_prompt(
            original=state["original"]
        ).to_messages()
        response = self.llm.invoke(prompt)
        state["translated"].append(response.content)
        return state

    # async def ainvoke(self, state: TranslateState):
    #     # 스트리밍 모드로 토큰 단위 chunk 생성
    #     prompt = self.prompt_template.format_prompt(
    #         original=state["original"]
    #     ).to_messages()
    #     # ChatOpenAI 에 streaming=True 로 생성해야 .ainvoke() 가능
    #     async for chunk in self.llm.ainvoke(prompt):
    #         state["translated"].append(chunk.content)
    #         yield state


    async def ainvoke(self, state: TranslateState):
        # 1) prompt 준비
        prompt = self.prompt_template.format_prompt(
            original=state["original"]
        ).to_messages()

        # 2) astream() 으로 async iterator 얻기
        async for token in self.llm.astream(prompt):
            # token이 str인 경우가 많지만 만약 객체라면 token.content 사용
            chunk = token if isinstance(token, str) else token.content
            state["translated"].append(chunk)
            yield state