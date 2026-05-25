# app/core/llm/prompt_loader.py

from pathlib import Path

from app.config.logging import (
    get_logger,
)


logger = get_logger(
    "prompt-loader"
)


# =========================================================
# PROMPT PATH
# =========================================================
PROMPT_PATH = (
    Path(__file__)
    .parent
    / "system-prompt.txt"
)


# =========================================================
# LOAD SYSTEM PROMPT
# =========================================================
def load_system_prompt():

    try:

        with open(
            PROMPT_PATH,
            "r",
            encoding="utf-8",
        ) as file:

            prompt = file.read()

        logger.info(
            "System prompt loaded"
        )

        return prompt

    except Exception as e:

        logger.error(
            "Failed to load prompt",
            error=str(e),
        )

        raise e