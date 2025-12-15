class MCP:
    def __init__(self, tools: dict):
        if not isinstance(tools, dict) or not tools:
            raise ValueError("MCP requiere un diccionario de herramientas válido")

        self.tools = tools

    def run(self, llm_output: dict):              
        if not isinstance(llm_output, dict):
            raise ValueError("La salida del LLM debe ser un diccionario")

        tool = llm_output.get("tool")
        params = llm_output.get("params", {})

        if not tool:
            raise ValueError("No se especificó ninguna herramienta")

        if tool not in self.tools:
            raise ValueError(f"Herramienta no permitida: {tool}")

        if not isinstance(params, dict):
            raise ValueError("Los parámetros de la herramienta deben ser un diccionario")

        # Ejecuta la tool de forma segura
        return self.tools[tool](**params)
