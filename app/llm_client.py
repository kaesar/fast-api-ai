"""Cliente LLM unificado.

- LLM_PROVIDER=openai -> OpenAI API (gpt-4o-mini por defecto, requiere OPENAI_API_KEY)
- LLM_PROVIDER=ollama -> Ollama local vía endpoint compatible OpenAI
  (http://localhost:11434/v1 + modelo gemma4:e4b-mlx, key dummy "ollama").

Se usa el SDK oficial `openai` en ambos casos; solo cambia base_url/model.
"""
from openai import AsyncOpenAI

from app import config

_client: AsyncOpenAI | None = None


def get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(
            api_key=config.LLM_API_KEY or "ollama",
            base_url=config.LLM_BASE_URL,
        )
    return _client


SYSTEM_PROMPT = (
    "Eres un asistente útil y conciso. Respondes en español salvo que "
    "el usuario pida otro idioma."
)


async def chat_completion(prompt: str, history: list[dict] | None = None) -> str:
    """Llama al LLM con un system prompt + historial opcional + prompt actual."""
    client = get_client()
    messages: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]
    if history:
        # solo últimos 10 mensajes para no crecer la sesión sin límite
        messages.extend(history[-10:])
    messages.append({"role": "user", "content": prompt})
    resp = await client.chat.completions.create(
        model=config.LLM_MODEL,
        messages=messages,  # type: ignore[arg-type]
        temperature=0.7,
    )
    return (resp.choices[0].message.content or "").strip()


def provider_info() -> dict:
    return {
        "provider": config.LLM_PROVIDER,
        "model": config.LLM_MODEL,
        "base_url": config.LLM_BASE_URL,
    }
