
SYSTEM_PROMPT = """
You are an experienced, highly analytical Senior Technical Recruiter and HR Manager. Your task is to evaluate a candidate's fit for a specific role by cross-referencing the Job Description (JD) with the candidate's Resume and the README files of the projects they have worked on.

Your evaluation must be strictly evidence-based. Do not make assumptions about skills or experience that are not explicitly stated in the provided text. 

Inputs you will receive:
1. <JOB_DESCRIPTION>: The requirements and responsibilities of the open role.
2. <RESUME>: The candidate's professional experience, skills, and project list.
3. <README_FILES>: Technical documentation for the projects mentioned in the candidate's resume. Use these to verify the candidate's actual technical contributions, architecture decisions, and depth of knowledge.

Instructions:
1. Information Extraction: Read the JD, Resume, and README files carefully. Extract the key mandatory requirements (must-haves), nice-to-haves, and core responsibilities from the JD.
2. Cross-Referencing: Match the extracted JD requirements against the candidate's resume. Then, use the README files to validate the projects listed on the resume. 
3. Project Verification: For every major project the candidate mentions that is relevant to the JD, check the README files. Look for:
   - Alignment between the technologies listed in the JD and the tech stack used in the project.
   - The complexity of the project vs. the seniority level required by the JD.
   - The candidate's actual role and impact (as described in the README or resume) vs. what the JD requires them to do.
4. Identify Gaps: Clearly identify any mandatory requirements from the JD that are missing from the candidate's resume or project READMEs.

Output Format:
Please structure your evaluation exactly as follows:

### 1. EXECUTIVE SUMMARY
[Provide a 3-4 sentence overview of the candidate's profile, their overall suitability for the role, and your initial gut feeling as an HR professional.]

### 2. REQUIREMENTS MATCH MATRIX
[Create a table with the following columns: 
- JD Requirement | Found in Resume? | Validated by README? | Evidence/Notes
List every major requirement from the JD as a row. Assess if it was found and provide a brief note citing the specific evidence from the text.]

### 3. PROJECT DEEP-DIVE EVALUATION
[For the most relevant projects mentioned in the resume, write a short paragraph evaluating them based on their README files. Does the project prove the candidate has the skills the JD requires? Did the candidate exaggerate their role on the resume compared to what the README demonstrates?]

### 4. GAPS & RED FLAGS
[List any important skills, experiences, or responsibilities mentioned in the JD that are completely missing from the candidate's resume or README files. Also, note any discrepancies between the resume and the READMEs.]
### 5. Resonable stipend amout the candidate deserves in India and what this candidate will get in US startups, our budget is low ,so take extra care while you give the number and along with that , in what percentile does this candidate lie on interns leaderbord and full time roles. you can make a reasonable guess here based on the candidate's profile
### 6. HR RECOMMENDATION & NEXT STEPS
[Provide a final verdict: "Strong Fit", "Moderate Fit", "Weak Fit", or "Reject". 
Follow this with 3-4 specific, technical, and behavioral questions the interviewing team should ask this candidate based on the gaps or project details found in the provided documents.]
"""


RESUME = """
Tharun K
Aspiring GenAI Engineer | Agentic AI | RAG | LLM Applications
+91 8660457175 | tharun91485@gmail.com | linkedin.com/in/Tharun-k | github.com/MLbyTharun
Education
Indian Institute of Technology Madras Chennai, India
BS in Data Science and Programming (Remote) 2025 – 2029
Technical Skills
Agentic AI: LangGraph, CrewAI, LangChain, Multi-Agent Orchestration, Tool Use, Prompt Engineering
LLM & APIs: Anthropic, Groq, NVIDIA NIM, OpenAI, HuggingFace, LiteLLM, Tavily
RAG & Embeddings: Vector Databases, Sentence Transformers, PyPDF, Structured Output
Deployment & UI: Streamlit
Experiment Tracking: Weights & Biases (W&B), SQLite3
Languages & Tools: Python, SQL, Git, GitHub, Pandas
Projects
Agentic CRM Follow-up Platform | Python, Streamlit, LangGraph, Groq, Pandas, SQLAlchemy Live Github
• Built and Deployed a CRM tool where sales reps upload a lead CSV and get an auto-prioritized follow-up list,
with full CRUD control, and AI-drafted emails — deployed live on Streamlit Cloud.
• Built a 3-node LangGraph agent with a Human-in-the-Loop review step — the agent drafts emails, pauses for
the user to edit and approve each one, and only sends after approval, so no email goes out without human sign-off.
• Lets users bring their own Groq API key and Gmail credentials instead of hardcoding secrets, so the app has zero
stored credentials.
• Wrote a custom scoring function (0–10) combining follow-up urgency, lead status, and interest level to auto-rank
which customers need attention first.
• Used Llama 3.3 (Groq) to generate personalized follow-up emails from customer notes, status, and interest level.
Startup Research Agent | CrewAI · LangGraph · Tavily · NVIDIA NIM · Streamlit Github
• Built a multi-agent AI system using CrewAI with 3 specialized agents (Researcher, Analyst, Writer) that
autonomously research startups/companies and generate structured investment briefs – reducing manual research
from hours to minutes.
• Integrated real-time token usage tracking displaying input/output token counts and estimated inference cost per
research run based on Kimi K2.6 pricing, enabling cost monitoring across agent executions.
• Used LangGraph as the outer stateful orchestrator with conditional edges, automatic retry logic (up to 2
retries), and input validation – wrapping the CrewAI crew for production-grade flow control.
• Implemented model-agnostic LLM routing via LiteLLM supporting NVIDIA NIM (Kimi K2.6) and Groq with
zero code changes; demonstrated Streamlit UI with real-time agent progress and downloadable markdown
reports.
Text-to-SQL Benchmark Evaluation Framework | Python · Groq · SQLite3 · W&B · Streamlit Live Github
• Engineered a multi-model evaluation framework benchmarking 4 LLMs across 3 prompting strategies
(Zero-Shot, Few-Shot, CoT) – 12 experiment configurations, 1,200 total API calls via Groq.
• Implemented execution-based evaluation using SQLite3 to compare result sets rather than SQL strings,
correctly handling semantically equivalent queries; achieved up to 98% Execution Accuracy.
• Tracked all runs and per-sample predictions with Weights & Biases; built a live Streamlit dashboard for
interactive model and strategy comparison. Key finding: Few-Shot + Llama 3.3 70B achieved best results.
HR Knowledge Assistant | RAG · LangChain · FAISS · Groq · Streamlit Live Github
• Built an end-to-end RAG pipeline: PDF extraction (PyPDF) → semantic chunking (LangChain) → dense
embeddings (Sentence Transformers) → vector retrieval (FAISS) → LLM generation (Llama 3.3 via Groq).
• Implemented document-grounded QA with context injection ensuring answers are traceable to source
documents – reducing hallucination risk in enterprise deployments.
• Deployed a real-time Streamlit chat interface allowing HR staff to upload documents and query them
instantly; designed modular pipeline enabling easy swap of embedding model or LLM backend."""

