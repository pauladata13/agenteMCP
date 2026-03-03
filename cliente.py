import asyncio
import json
from openai import AsyncOpenAI
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Conexión a modelo local (Ollama)
llm = AsyncOpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama"
)

SYSTEM_PROMPT = """
Eres un asistente para documentos .txt. REGLAS IMPORTANTES:

1. 'list_txt_files()' DEVUELVE SOLO LA LISTA DE NOMBRES DE ARCHIVOS, NO su contenido
2. Para LEER COMPLETO usa: read_full_txt("nombre_exacto.txt")

EJEMPLO CORRECTO:
Usuario: "¿Qué archivos hay?"
list_txt_files() → "Archivos disponibles: - archivo1.txt - archivo2.txt"
Tú respondes: "Tienes estos archivos: archivo1.txt y archivo2.txt"

NUNCA digas que list_txt_files muestra "contenido". Solo muestra nombres.

Responde en castellano, texto plano.
"""


def sanitize_text(text) -> str:
    if not text:
        return ""
    return "".join(c for c in str(text) if not (0xD800 <= ord(c) <= 0xDFFF))


async def run_client():
    server_params = StdioServerParameters(
        command="python",
        args=["server.py"]
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:

            await session.initialize()
            mcp_tools = await session.list_tools()

            print("[+] Connected to MCP server.")
            print("Type 'exit' to quit.\n")

            # Convert MCP tools to OpenAI format
            tools_for_llm = []
            for tool in mcp_tools.tools:
                tools_for_llm.append({
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.inputSchema
                    }
                })

            messages = [{"role": "system", "content": SYSTEM_PROMPT}]

            while True:
                user_input = input("You: ")

                if user_input.lower() == "exit":
                    break

                messages.append({"role": "user", "content": user_input})

                response = await llm.chat.completions.create(
                    model="llama3.2",
                    messages=messages,
                    tools=tools_for_llm
                )

                msg = response.choices[0].message

                # Si el modelo quiere usar tools
                if msg.tool_calls:

                    messages.append({
                        "role": "assistant",
                        "tool_calls": msg.tool_calls
                    })

                    for tool_call in msg.tool_calls:
                        function_name = tool_call.function.name
                        arguments = json.loads(tool_call.function.arguments)

                        print(f"\n[*] Using tool: {function_name}")

                        result = await session.call_tool(function_name, arguments)

                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": str(result.content)
                        })

                    # Segunda llamada al modelo con resultado de tool
                    final_response = await llm.chat.completions.create(
                        model="llama3.2",
                        messages=messages
                    )

                    final_text = final_response.choices[0].message.content
                    messages.append({"role": "assistant", "content": final_text})

                    print("\nAssistant:", final_text, "\n")

                else:
                    reply = msg.content
                    messages.append({"role": "assistant", "content": reply})
                    print("\nAssistant:", reply, "\n")


if __name__ == "__main__":
    asyncio.run(run_client())