import os
import httpx
import json
import re
from typing import List, Dict, Any

API_URL = os.getenv("AIPIPE_API_URL", "https://api.aipipe.io/v1/chat/completions")
API_KEY = os.getenv("AIPIPE_API_KEY")
MODEL = os.getenv("AIPIPE_MODEL", "gpt-5-nano")

class LLMAgent:
    def __init__(self):
        if not API_KEY:
            raise RuntimeError("AIPIPE_API_KEY missing")
        self.api_url = API_URL
        self.api_key = API_KEY
        self.model = MODEL

    async def call_llm(self, messages: List[Dict[str, str]]) -> str:
        async with httpx.AsyncClient(timeout=45.0) as client:
            resp = await client.post(
                self.api_url,
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                json={"model": self.model, "messages": messages},
            )
            resp.raise_for_status()

        parsed = resp.json()
        return parsed["choices"][0]["message"]["content"]

    async def get_structured_response(self, context: str, history: List[Dict[str, str]], email: str = None, secret: str = None) -> Dict[str, Any]:
        print("7 Calling LLM for structured response")

        system_prompt = (
            "You are an expert quiz solver. Your goal is to extract information from a webpage to answer a quiz question.\\n"
            "Based on the provided text, extract the following information:\\n"
            "1. `submit_url`: The URL where the answer must be POSTed.\\n"
            "2. `next_url`: The URL for the next question, if provided.\\n"
            "3. `answer`: The direct answer to the question. This could be a number, string, boolean, etc.\\n"
            "4. `python_code`: If the answer requires computation, downloading a file, or complex data processing, provide Python code to calculate the answer. The final result must be stored in a variable named `ANSWER`.\\n\\n"
            "Return a single JSON object with these keys. If a value is not found, set it to null.\\n"
        )
        if email:
            system_prompt += f"\\nYour email: {email}"
        if secret:
            system_prompt += f"\\nYour secret: {secret}"

        messages = [
            {"role": "system", "content": system_prompt},
            *history,
            {"role": "user", "content": f"Here is the page content:\\n\\n{context[:6000]}"}
        ]

        content = await self.call_llm(messages)

        history.append({"role": "user", "content": f"Page content: {context[:100]}"})
        history.append({"role": "assistant", "content": content})

        m = re.search(r"\{.*\}", content, re.DOTALL)
        if not m:
            print("Warning: LLM did not return a JSON object.")
            return {
                "submit_url": "https://tds-llm-analysis.s-anand.net/submit",
                "next_url": None,
                "answer": None,
                "python_code": None,
            }

        try:
            data = json.loads(m.group(0))
            if not data.get("submit_url"):
                data["submit_url"] = "https://tds-llm-analysis.s-anand.net/submit"
            return data
        except json.JSONDecodeError:
            print("Warning: Failed to decode JSON from LLM response.")
            return {
                "submit_url": "https://tds-llm-analysis.s-anand.net/submit",
                "next_url": None,
                "answer": None,
                "python_code": None,
            }
