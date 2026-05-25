import json
import logging
from typing import Dict, Any
from e2b_code_interpreter import AsyncSandbox
import asyncio

logger = logging.getLogger(__name__)

class SandboxService:
    def __init__(self):
        pass

    async def execute_code(self, code: str, language: str = "python") -> Dict[str, Any]:
        """
        Execute code in a secure E2B sandbox environment.
        Currently supports python.
        """
        if language.lower() != "python":
            return {
                "status": "error",
                "output": None,
                "error": f"Language {language} is not supported. Only python is supported."
            }

        try:
            # We'll use AsyncSandbox to create a short-lived sandbox
            async with AsyncSandbox() as sandbox:
                execution = await sandbox.run_code(code)
                
                output = ""
                if execution.logs.stdout:
                    output += "\n".join(execution.logs.stdout)
                
                error = None
                if execution.error:
                    error = f"{execution.error.name}: {execution.error.value}\n{execution.error.traceback}"
                
                return {
                    "status": "success" if not error else "error",
                    "output": output if output else None,
                    "error": error,
                    "results": [result.model_dump() for result in execution.results] if execution.results else []
                }
        except Exception as e:
            logger.error(f"Sandbox execution failed: {str(e)}")
            return {
                "status": "error",
                "output": None,
                "error": str(e)
            }

sandbox_service = SandboxService()
