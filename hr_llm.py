from dotenv import load_dotenv
import os

from langchain.chat_models import init_chat_model

from langchain_core.messages import SystemMessage, HumanMessage
from llm_config_bc import SYSTEM_PROMPT,RESUME,JD, SYSTEM_PROMPT_SUM

from extracter import extract_github_links
from github_fetcher import get_evaluable_profiles

load_dotenv()


links = extract_github_links("Tharun.pdf")["repo_apis"]
data = get_evaluable_profiles(links)
groq = init_chat_model(
    model="gemini-3.5-flash",
    model_provider="google_genai",
    temperature=0,
    api_key = os.getenv("GOOGLE_API_KEY")
)

# Summarisation Block

readme = groq.invoke([
    SystemMessage(content = SYSTEM_PROMPT_SUM),
    HumanMessage(content = f"""<JOB_DESCRIPTION>
                    {JD}
                    </JOB_DESCRIPTION>

                    <README_FILES>
                    {data}
                    </README_FILES>)""")
])

# Final Block

response = groq.invoke([
    SystemMessage(content = SYSTEM_PROMPT),
    HumanMessage(content = f"""<JOB_DESCRIPTION>
                    {JD}
                    </JOB_DESCRIPTION>

                    <RESUME>
                    {RESUME}
                    </RESUME>

                    <README_FILES>
                    {readme}
                    </README_FILES>)""")
])

print("START")
print(response.text)
print("END")
