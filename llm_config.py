
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




JD = """# AI / Generative AI / Agentic AI Intern

**Location:** [Bangalore / Remote / Hybrid]
**Type:** Internship
**Company Stage:** Early-stage startup
**Team Size:** <50 members

## About the Role

We are looking for an **AI / Generative AI / Agentic AI Intern** to join our small, fast-moving team and work on real AI products used to solve meaningful business problems.

This is **not a role for someone who has only built tutorial-based chatbots, basic RAG applications, or followed AI courses without building anything substantial**.

We are looking for someone who has demonstrated the ability to **build, experiment, debug, and ship real AI systems**.

You will work closely with the founding and engineering team, take ownership of AI-related problems, and contribute directly to products and internal systems.

## What You'll Work On

Depending on your skills and interests, you may work on:

* Building and improving **LLM-powered applications**
* Designing **AI agents and multi-agent workflows**
* Developing reliable **agentic systems** capable of planning, tool usage, reasoning, and executing multi-step tasks
* Building production-oriented **RAG systems** with effective retrieval, reranking, evaluation, and context management
* Working with LLM APIs, open-source models, embeddings, vector databases, and AI infrastructure
* Designing workflows involving **human-in-the-loop systems, tool calling, structured outputs, and autonomous task execution**
* Evaluating LLM applications using meaningful metrics and real-world test cases
* Improving latency, cost, reliability, accuracy, and overall system performance
* Rapidly prototyping and deploying AI features in a fast-moving startup environment

## What We're Looking For

### Strongly Preferred

* Experience building **non-trivial AI, Generative AI, or Agentic AI projects**
* A portfolio or GitHub profile that demonstrates the ability to **build real systems, not just follow tutorials**
* Understanding of LLM application architecture and the limitations of current AI systems
* Experience with technologies such as:

  * Python
  * LLM APIs and/or open-source models
  * LangChain, LangGraph, LlamaIndex, CrewAI, or similar frameworks
  * RAG pipelines and vector databases
  * Function/tool calling
  * Structured outputs
  * AI agents and workflow orchestration
  * FastAPI or similar backend frameworks
  * Git and basic deployment practices

## The Kind of Projects We Value

We are interested in candidates who have built projects with genuine engineering depth, such as:

* AI agents that can independently complete multi-step tasks using tools
* Production-oriented RAG systems with proper retrieval strategies and evaluation
* LLM applications with meaningful benchmarks and performance comparisons
* AI systems integrated with APIs, databases, external tools, or real workflows
* Systems that solve a specific, non-trivial problem rather than simply demonstrating that an LLM can generate text
* Projects where you can clearly explain:

  * Why you chose a particular architecture
  * What alternatives you considered
  * How you evaluated the system
  * What failed and how you improved it
  * The trade-offs between cost, latency, accuracy, and complexity

## Projects We Are Not Looking For

Please do not apply solely based on projects such as:

* Basic ChatGPT clones
* Generic PDF chatbots
* Simple “chat with your documents” RAG applications
* Tutorial-following LangChain projects
* Basic AI resume screeners without meaningful engineering depth
* Simple prompt wrappers around an LLM API
* Generic sentiment analysis or text classification projects
* Projects copied from YouTube tutorials or courses with minimal independent work

**The quality of your thinking, engineering decisions, and ability to build will matter more than the number of projects on your resume.**

## What We Value

* Strong problem-solving ability
* Ability to learn quickly and independently
* Genuine curiosity about AI and emerging technologies
* Ability to go beyond tutorials and documentation
* Strong ownership and execution
* Comfort with ambiguity
* Ability to understand a problem and build a solution from scratch
* Willingness to experiment, fail, debug, and iterate quickly

## Who Should Apply?

You should apply if you have **a small number of strong, technically meaningful projects** that demonstrate your ability to build real AI systems.

We care much more about **one deeply engineered project than ten generic AI projects**.

If you have built something interesting, technically challenging, and can clearly explain your decisions and trade-offs, we would love to hear from you.

## How to Apply

Please share:

* Your resume
* GitHub profile
* Portfolio or relevant project links
* A brief explanation of the most technically challenging AI system you have built and what you learned while building it

**We will evaluate your actual work—not just the technologies listed on your resume.**
"""


SYSTEM_PROMPT_SUM = """You are an expert technical recruiter and resume information extraction system.

Your task is to extract ONLY the information from the resume that is relevant for evaluating the candidate against a job description.

Do not summarize the entire resume. Do not rewrite it. Do not include irrelevant personal information or generic details.

Focus on extracting information that helps determine the candidate's suitability for the role.

Extract the following:

1. Candidate's relevant technical skills

   * Programming languages
   * Frameworks and libraries
   * AI/ML/GenAI technologies
   * Databases
   * Cloud, deployment, and infrastructure tools
   * Other technologies directly relevant to the job

2. Relevant work experience

   * Job title and company
   * Responsibilities relevant to the job description
   * Technologies used
   * Important achievements and measurable impact

3. Relevant projects
   For each relevant project, extract:

   * Project name
   * What the project does
   * The candidate's technical contribution
   * Technologies and models used
   * Important technical features
   * Quantifiable results, if available
   * GitHub or live demo link, if available

4. Education
   Include only education details relevant to assessing the candidate's qualifications.

5. Relevant achievements
   Include only achievements that demonstrate technical ability, problem-solving ability, leadership, or relevance to the job.

6. GitHub, portfolio, or other technical links
   Extract these only if they are present and useful for evaluating the candidate.

IMPORTANT RULES:

* Extract information; do not invent or infer facts.
* Ignore irrelevant personal details such as full address, date of birth, gender, nationality, marital status, and other information that does not help evaluate the candidate.
* Remove generic soft skills unless they are supported by specific evidence.
* Remove repetitive information.
* Prioritize concrete evidence over claims.
* Preserve important numbers, metrics, technologies, model names, and technical details.
* If a section contains no relevant information, omit it.
* The output should be concise but sufficiently detailed for another LLM or recruiter to evaluate the candidate.

The output should follow this structure:

<CANDIDATE_PROFILE>
Name: [Name, if available]

<RELEVANT_SKILLS>
[Only relevant technical skills]
</RELEVANT_SKILLS>

<EXPERIENCE>
[Relevant experience with responsibilities, technologies, and measurable impact]
</EXPERIENCE>

<PROJECTS>
[Relevant projects with technical details, contributions, technologies, and results]
</PROJECTS>

<EDUCATION>
[Relevant education]
</EDUCATION>

<ACHIEVEMENTS>
[Relevant achievements]
</ACHIEVEMENTS>

<TECHNICAL_LINKS>
[GitHub, portfolio, demos, or other relevant links]
</TECHNICAL_LINKS>
</CANDIDATE_PROFILE>

<JOB_DESCRIPTION>
{JOB_DESCRIPTION}
</JOB_DESCRIPTION>

<README_FILES>
{READMES}
</README_FILES>

Extract only the information that is relevant to the JOB_DESCRIPTION.
"""