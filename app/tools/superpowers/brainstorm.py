"""
app/tools/superpowers/brainstorm.py
"""

def build_brainstorm_prompt(user_prompt: str, brand_context: str, user_context: str, session_context: str) -> str:
    return f"""You are the Lead Orchestrator for AgentPress. 
Your goal is to BRAINSTORM and finalize a detailed Document Specification (Spec) based on the user request.

USER REQUEST:
{user_prompt}

BRAND GUIDELINES:
{brand_context}

USER PREFERENCES:
{user_context}

PAST SESSION CONTEXT:
{session_context}

INSTRUCTIONS:
1. Define the purpose and target audience of the document.
2. Outline the core themes and key sections required.
3. Specify any mandatory brand elements (colors, logos, tone).
4. Identify data points that the Researcher needs to gather.
5. Identify formatting requirements (e.g., slide count for PPTX, page layout for DOCX).

Output a structured Markdown Document Specification."""
