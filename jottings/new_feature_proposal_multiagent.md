I need to refactor my existing `DocAssistantService` (which is currently a simple RAG chain) into a robust **Multi-Agent System** using **LangGraph** and **Django**.

The goal is to support two distinct capabilities:
1.  **Documentation QA**: Answering questions based on DITA docs (Existing RAG logic).
2.  **Script Management**: Inserting or splitting script lines in the database via natural language commands.

### 🏗️ Architecture: The Supervisor-Worker Pattern
I want a graph that works like this:
1.  **Router/Supervisor**: Analyzes the user input to decide intent ("DOC_QA" vs "SCRIPT_EDIT").
2.  **DocQA Agent**: The existing RAG logic.
3.  **ScriptEditor Agent**: A new agent equipped with database tools.

### 🛠️ Tech Stack Requirements
- **Framework**: Django (models are in `scripts.models`).
- **Orchestration**: `langgraph` (StateGraph).
- **LLM**: `ChatGoogleGenerativeAI` (Gemini 2.5/3.0 or Pro).
- **Tools**: Use `@tool` decorator from `langchain_core.tools`.

### 🧩 Detailed Requirements

#### 1. The State
Define a `AgentState` TypedDict containing:
- `messages`: List of messages (conversation history).
- `next`: The next node to route to.

#### 2. The ScriptEditor Agent & Tools
Create a tool named `insert_script_line`.
- **Logic**: 
  - Input: `reference_id` (int), `position` ('before'/'after'), `content` (str), `speaker` (optional).
  - Database Logic: 
    - Fetch the `ScriptLine` by `reference_id`.
    - Calculate `new_order` using the float average formula: `(prev_order + next_order) / 2`.
    - If user provides only one language (e.g., Chinese), the LLM must generate the translation for the other field (`content_en` / `content_zh`) before calling the tool, OR the tool can handle it if you prefer. 
    - Create the record in Django DB.
  - **Output**: A confirmation string.

#### 3. The DocQA Agent
- Port the logic from my provided `DocAssistantService`.
- It should use the `DITAVectorStore` to retrieve context.
- Instead of just returning a string, it should return a generic AI response based on the context.

#### 4. The Router (Conditional Edge)
- Use a lightweight LLM call (or structured output) to classify the user's prompt.
- If it looks like "How do I use the app?", route to `DocQA`.
- If it looks like "Insert a line after #100", route to `ScriptEditor`.

### 📄 Existing Code Context
(Here is my current `rag_service.py` for reference)
[PASTE YOUR CURRENT CODE HERE]

### 🎯 Definition of Done
Please generate:
1.  `tools.py`: Containing the Django database manipulation tools.
2.  `agents.py`: Containing the LangGraph nodes and the graph definition.
3.  A refactored `DocAssistantService` class that simply invokes the graph.

我简要解释一下 LangGraph 在这里的运作模式：

状态 (State)： 这就好比一个共享的笔记本。用户发了一句“在 #998 后面加一句”，这句话被写进笔记本。

路由 (Router)： Router 看了眼笔记本，说：“这不是问文档的，这是要改数据的。转给 ScriptEditor。”

ScriptEditor 节点： 这个节点不仅能调用 LLM，还能绑定工具。

LLM 思考：“我要调用 insert_tool，参数是 id=998, pos=after...”

LangGraph 自动执行工具：执行你的 Django 数据库代码。

回环：工具执行完，把结果（“成功插入 ID #998.5”）写回笔记本。

回复： LLM 看到工具执行成功了，最后生成一句人话：“搞定！我已经把 Ross 的台词插进去了。”

用户并不一定会提供中英文对比，一般可能只提供英文，因此在提供LLM推定要插入的数据的各个字段的值时，需要提供 id 上下各3个index的文本内容，让LLM可以推断出 Speaker的值，并且 raw_text 遵循 "Speaker: Script Line"的格式。
