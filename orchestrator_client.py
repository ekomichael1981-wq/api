import httpx
import asyncio
import logging
import os
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
ORCHESTRATOR_URL = os.getenv("ORCHESTRATOR_URL", "https://your-railway-url.up.railway.app")
TIMEOUT_SECONDS = 30
RETRY_INTERVAL_SECONDS = 120  # 2 minutes

class OrchestratorClient:
    async def query_orchestrator(self, user_text: str) -> Dict[str, Any]:
        """
        Sends the user query to the orchestrator.
        Returns the JSON response if successful within timeout.
        Raises TimeoutError or HTTPError if it fails.
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    ORCHESTRATOR_URL,
                    json={"user_query": user_text},
                    timeout=TIMEOUT_SECONDS
                )
                response.raise_for_status()
                return response.json()
            except httpx.TimeoutException:
                logger.error(f"Orchestrator timed out after {TIMEOUT_SECONDS}s")
                raise TimeoutError("Orchestrator timed out")
            except httpx.HTTPStatusError as e:
                logger.error(f"Orchestrator returned error: {e.response.status_code}")
                raise

    async def retry_loop(self, user_text: str, callback_func):
        """
        Background task that retries the orchestrator every 2 minutes.
        When successful, calls the callback_func with the result.
        """
        logger.info("Starting retry loop for user query...")
        while True:
            await asyncio.sleep(RETRY_INTERVAL_SECONDS)
            try:
                logger.info("Retrying orchestrator...")
                result = await self.query_orchestrator(user_text)
                logger.info("Retry successful! Sending response.")
                await callback_func(result)
                break  # Exit loop on success
            except Exception as e:
                logger.error(f"Retry failed: {e}. Waiting {RETRY_INTERVAL_SECONDS}s...")
                # Continue looping

# Singleton instance
orchestrator_client = OrchestratorClient()
