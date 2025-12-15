class MCP:
    def __init__(self, tools: dict):
        self.tools = tools

    def run(self, llm_output: dict):
        tool = llm_output.get("tool")
        params = llm_output.get("params", {})

        if tool not in self.tools:
            return {"error": f"Tool '{tool}' no permitida"}

        return self.tools[tool](**params)
