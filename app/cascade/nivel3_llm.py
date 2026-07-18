import asyncio

from groq import AsyncGroq

from app.config import settings

_client: AsyncGroq | None = None


def get_client() -> AsyncGroq:
    global _client
    if _client is None:
        _client = AsyncGroq(api_key=settings.groq_api_key)
    return _client


async def completar(system_prompt, historial, mensaje, modelo_cfg) -> str:
    if not settings.groq_api_key:
        raise RuntimeError("GROQ_API_KEY no configurada")

    modelo = modelo_cfg.get("nombre") or settings.groq_model_default
    mensajes = [{"role": "system", "content": system_prompt}]
    mensajes += [{"role": t["role"], "content": t["content"]} for t in historial]
    mensajes.append({"role": "user", "content": mensaje})

    respuesta = await asyncio.wait_for(
        get_client().chat.completions.create(
            model=modelo,
            messages=mensajes,
            temperature=modelo_cfg.get("temperatura", 0.4),
            max_tokens=modelo_cfg.get("max_tokens", 500),
        ),
        timeout=25,
    )
    return (respuesta.choices[0].message.content or "").strip()
