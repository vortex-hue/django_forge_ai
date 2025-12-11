"""
Orchestrator for executing AI agent tasks.
"""
from typing import Dict, Any, List, Optional
from django.utils import timezone

from .models import AgentConfig, AgentTask, AgentTaskLog
from ..utils.llm_client import get_llm_client


class AgentOrchestrator:
    """
    Orchestrates the execution of AI agent tasks.
    """
    
    def __init__(self, agent_config: AgentConfig):
        self.agent = agent_config
        self.llm_client = get_llm_client()
        self.tools = self._initialize_tools()
    
    def _initialize_tools(self) -> Dict[str, callable]:
        """Initialize available tools for the agent"""
        tools = {}
        
        for tool_name in self.agent.tools:
            if tool_name == 'web_search':
                tools[tool_name] = self._web_search
            elif tool_name == 'database_query':
                tools[tool_name] = self._database_query
            elif tool_name == 'file_read':
                tools[tool_name] = self._file_read
            # Add more tools as needed
        
        return tools
    
    def execute_task(self, task: AgentTask) -> str:
        """
        Execute an agent task.
        
        Args:
            task: AgentTask instance to execute
        
        Returns:
            Task result string
        """
        task.mark_running()
        
        try:
            # Build system prompt
            system_prompt = self._build_system_prompt()
            
            # Initial user prompt
            user_prompt = self._build_initial_prompt(task)
            
            # Agent loop
            result = self._agent_loop(task, system_prompt, user_prompt)
            
            task.mark_completed(result)
            return result
            
        except Exception as e:
            error_msg = str(e)
            task.mark_failed(error_msg)
            raise
    
    def _build_system_prompt(self) -> str:
        """Build system prompt for the agent"""
        if self.agent.system_prompt:
            return self.agent.system_prompt
        
        # Default system prompt
        prompt = f"You are {self.agent.name}. {self.agent.persona}\n\n"
        prompt += "Your goals are:\n"
        for goal in self.agent.goals:
            prompt += f"- {goal}\n"
        
        if self.agent.tools:
            prompt += "\nAvailable tools:\n"
            for tool in self.agent.tools:
                prompt += f"- {tool}\n"
        
        prompt += "\nYou should think step by step and use tools when necessary."
        
        return prompt
    
    def _build_initial_prompt(self, task: AgentTask) -> str:
        """Build initial user prompt for the task"""
        prompt = f"Task: {task.task_description}\n"
        
        if task.context:
            prompt += "\nContext:\n"
            for key, value in task.context.items():
                prompt += f"{key}: {value}\n"
        
        return prompt
    
    def _agent_loop(self, task: AgentTask, system_prompt: str, initial_prompt: str) -> str:
        """Execute the agent reasoning loop."""
        conversation_history = [{"role": "user", "content": initial_prompt}]
        
        for iteration in range(1, self.agent.max_iterations + 1):
            response = self._get_agent_response(conversation_history, system_prompt, task, iteration)
            tool_call = self._extract_tool_call(response)
            
            if tool_call:
                tool_result = self._execute_tool(tool_call, task, iteration)
                conversation_history = self._update_conversation_with_tool_result(
                    conversation_history, response, tool_result
                )
                self._update_task_iteration(task, iteration)
            else:
                self._update_task_iteration(task, iteration)
                return response
        
        return conversation_history[-1].get("content", "Task incomplete - max iterations reached")
    
    def _get_agent_response(self, conversation_history: list, system_prompt: str, task: AgentTask, iteration: int) -> str:
        """Get agent response from LLM and log it."""
        response = self.llm_client.generate(
            prompt=conversation_history[-1]["content"],
            system_prompt=system_prompt,
            temperature=self.agent.temperature
        )
        
        AgentTaskLog.objects.create(
            task=task,
            iteration=iteration,
            action="llm_response",
            observation=response
        )
        return response
    
    def _update_conversation_with_tool_result(self, conversation_history: list, response: str, tool_result: str) -> list:
        """Update conversation history with tool execution result."""
        conversation_history.append({"role": "assistant", "content": response})
        conversation_history.append({"role": "user", "content": f"Tool result: {tool_result}"})
        return conversation_history
    
    def _update_task_iteration(self, task: AgentTask, iteration: int):
        """Update task iteration count."""
        task.iterations_used = iteration
        task.save(update_fields=['iterations_used'])
    
    def _extract_tool_call(self, response: str) -> Optional[Dict[str, Any]]:
        """Extract tool call from agent response. In production, use structured output or function calling."""
        if "TOOL_CALL:" not in response:
            return None
        
        try:
            parts = response.split("TOOL_CALL:")[1].strip().split("\n")[0]
            tool_name = parts.split("(")[0].strip()
            args_str = parts.split("(")[1].split(")")[0] if "(" in parts else ""
            return {"tool": tool_name, "args": args_str}
        except Exception:
            return None
    
    def _execute_tool(self, tool_call: Dict[str, Any], task: AgentTask, iteration: int) -> str:
        """Execute a tool call"""
        tool_name = tool_call.get("tool")
        
        if tool_name not in self.tools:
            return f"Error: Tool '{tool_name}' not available"
        
        try:
            result = self.tools[tool_name](tool_call.get("args", ""))
            
            # Log tool execution
            AgentTaskLog.objects.create(
                task=task,
                iteration=iteration,
                action=f"tool_{tool_name}",
                observation=result
            )
            
            return result
        except Exception as e:
            error_msg = f"Error executing tool {tool_name}: {str(e)}"
            AgentTaskLog.objects.create(
                task=task,
                iteration=iteration,
                action=f"tool_{tool_name}_error",
                observation=error_msg
            )
            return error_msg
    
    def _web_search(self, query: str) -> str:
        """Web search tool placeholder. In production, integrate with a real search API."""
        return f"Web search results for: {query} (placeholder - implement with real search API)"
    
    def _database_query(self, query: str) -> str:
        """Database query tool placeholder. In production, execute actual database queries."""
        return f"Database query results for: {query} (placeholder - implement with real DB queries)"
    
    def _file_read(self, file_path: str) -> str:
        """File read tool (placeholder)"""
        try:
            with open(file_path, 'r') as f:
                return f.read()
        except Exception as e:
            return f"Error reading file: {str(e)}"


def execute_agent_task(task_id: int) -> str:
    """
    Execute an agent task by ID.
    
    Args:
        task_id: ID of the AgentTask to execute
    
    Returns:
        Task result string
    """
    task = AgentTask.objects.get(pk=task_id)
    agent_config = task.agent
    
    orchestrator = AgentOrchestrator(agent_config)
    return orchestrator.execute_task(task)

