import json

from google import genai

from config import GEMINI_API_KEY

from tools.analysis_tools import (
    prepare_analysis_data
)


client = genai.Client(
    api_key=GEMINI_API_KEY
)


SYSTEM_INSTRUCTION = """
You are an AI analyst for a draft lifecycle system.

Your job is to analyze historical draft lifecycle data.

Focus on:

1. Conversion behavior
2. User edits
3. Abandoned drafts
4. Frequently changed fields
5. Repeated edit patterns
6. Possible improvements

Rules:

- Only make claims supported by the data.
- Do not invent reasons for abandonment.
- Clearly distinguish observations from hypotheses.
- Mention sample size when it is small.
- Do not treat a small sample as a definite user preference.

Return your analysis using these sections:

KEY FINDINGS

EDIT PATTERNS

ABANDONMENT PATTERNS

RECOMMENDATIONS

Keep the analysis concise and practical.
"""


def analyze_lifecycle():

    data = prepare_analysis_data()

    prompt = (
        SYSTEM_INSTRUCTION
        + "\n\nLIFECYCLE DATA:\n"
        + json.dumps(
            data,
            indent=2
        )
    )

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    return response.text