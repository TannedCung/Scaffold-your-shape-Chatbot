"""Custom React Agent with built-in quick_response termination logic.

This module provides a custom implementation of create_react_agent that includes
automatic termination when the quick_response tool is called.
"""

from typing import Union, Sequence, Optional, Type, Any, Callable, Literal, cast, get_type_hints
from langchain_core.tools import BaseTool
from langchain_core.messages import BaseMessage, AIMessage, ToolMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, END
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt.tool_node import ToolNode
from langgraph.utils.runnable import RunnableCallable
from langgraph.graph.message import add_messages
from langgraph.constants import Send
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.runnables.base import Runnable as RunnableLike
from langchain_core.prompt_values import PromptValue
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.store.base import BaseStore
from typing_extensions import TypedDict

# Import necessary utilities from langgraph.prebuilt
from langgraph.prebuilt.chat_agent_executor import (
    AgentState,
    AgentStateWithStructuredResponse,
    _get_prompt_runnable,
    _should_bind_tools,
    _get_model,
    _get_state_value,
    _validate_chat_history
)

# Type aliases
StateSchemaType = Union[Type[TypedDict], Type[Any]]
LanguageModelLike = Union[str, RunnableLike]
Prompt = Union[str, SystemMessage, Callable, RunnableLike, None]
StructuredResponseSchema = Union[dict, type, tuple[str, Union[dict, type]]]
Checkpointer = Union[None, bool, BaseCheckpointSaver]
AnyMessage = BaseMessage


def create_react_agent_with_quick_response_termination(
    model: Union[str, LanguageModelLike],
    tools: Union[Sequence[Union[BaseTool, Callable, dict[str, Any]]], ToolNode],
    *,
    prompt: Optional[Prompt] = None,
    response_format: Optional[
        Union[StructuredResponseSchema, tuple[str, StructuredResponseSchema]]
    ] = None,
    pre_model_hook: Optional[RunnableLike] = None,
    post_model_hook: Optional[RunnableLike] = None,
    state_schema: Optional[StateSchemaType] = None,
    config_schema: Optional[Type[Any]] = None,
    checkpointer: Optional[Checkpointer] = None,
    store: Optional[BaseStore] = None,
    interrupt_before: Optional[list[str]] = None,
    interrupt_after: Optional[list[str]] = None,
    debug: bool = False,
    version: Literal["v1", "v2"] = "v2",
    name: Optional[str] = None,
) -> CompiledStateGraph:
    """Create a react agent with built-in quick_response termination logic.
    
    This is a custom version of create_react_agent that automatically terminates
    when the quick_response tool is called, preventing further agent processing.
    
    Args:
        Same as create_react_agent from langgraph.prebuilt
        
    Returns:
        A compiled state graph with quick_response termination logic
    """
    
    if version not in ("v1", "v2"):
        raise ValueError(
            f"Invalid version {version}. Supported versions are 'v1' and 'v2'."
        )

    if state_schema is not None:
        required_keys = {"messages", "remaining_steps"}
        if response_format is not None:
            required_keys.add("structured_response")

        schema_keys = set(get_type_hints(state_schema))
        if missing_keys := required_keys - set(schema_keys):
            raise ValueError(f"Missing required key(s) {missing_keys} in state_schema")

    if state_schema is None:
        state_schema = (
            AgentStateWithStructuredResponse
            if response_format is not None
            else AgentState
        )

    llm_builtin_tools: list[dict] = []
    if isinstance(tools, ToolNode):
        tool_classes = list(tools.tools_by_name.values())
        tool_node = tools
    else:
        llm_builtin_tools = [t for t in tools if isinstance(t, dict)]
        tool_node = ToolNode([t for t in tools if not isinstance(t, dict)])
        tool_classes = list(tool_node.tools_by_name.values())

    if isinstance(model, str):
        try:
            from langchain.chat_models import init_chat_model  # type: ignore[import-not-found]
        except ImportError:
            raise ImportError(
                "Please install langchain (`pip install langchain`) to use '<provider>:<model>' string syntax for `model` parameter."
            )
        model = cast(BaseChatModel, init_chat_model(model))

    tool_calling_enabled = len(tool_classes) > 0

    if (
        _should_bind_tools(model, tool_classes, num_builtin=len(llm_builtin_tools))
        and len(tool_classes + llm_builtin_tools) > 0
    ):
        model = cast(BaseChatModel, model).bind_tools(tool_classes + llm_builtin_tools)

    model_runnable = _get_prompt_runnable(prompt) | model

    # If any of the tools are configured to return_directly after running,
    # our graph needs to check if these were called
    should_return_direct = {t.name for t in tool_classes if t.return_direct}

    def _are_more_steps_needed(state: StateSchemaType, response: BaseMessage) -> bool:
        has_tool_calls = isinstance(response, AIMessage) and response.tool_calls
        all_tools_return_direct = (
            all(call["name"] in should_return_direct for call in response.tool_calls)
            if isinstance(response, AIMessage)
            else False
        )
        remaining_steps = _get_state_value(state, "remaining_steps", None)
        is_last_step = _get_state_value(state, "is_last_step", False)
        return (
            (remaining_steps is None and is_last_step and has_tool_calls)
            or (
                remaining_steps is not None
                and remaining_steps < 1
                and all_tools_return_direct
            )
            or (remaining_steps is not None and remaining_steps < 2 and has_tool_calls)
        )

    def _get_model_input_state(state: StateSchemaType) -> StateSchemaType:
        if pre_model_hook is not None:
            messages = (
                _get_state_value(state, "llm_input_messages")
            ) or _get_state_value(state, "messages")
            error_msg = f"Expected input to call_model to have 'llm_input_messages' or 'messages' key, but got {state}"
        else:
            messages = _get_state_value(state, "messages")
            error_msg = (
                f"Expected input to call_model to have 'messages' key, but got {state}"
            )

        if messages is None:
            raise ValueError(error_msg)

        _validate_chat_history(messages)
        # we're passing messages under `messages` key, as this is expected by the prompt
        # Always use dictionary access for state updates
        state["messages"] = messages

        return state

    # Define the function that calls the model
    def call_model(state: StateSchemaType, config: RunnableConfig) -> StateSchemaType:
        state = _get_model_input_state(state)
        response = cast(AIMessage, model_runnable.invoke(state, config))
        # add agent name to the AIMessage
        response.name = name

        if _are_more_steps_needed(state, response):
            return {
                "messages": [
                    AIMessage(
                        id=response.id,
                        content="Sorry, need more steps to process this request.",
                    )
                ]
            }
        # We return a list, because this will get added to the existing list
        return {"messages": [response]}

    async def acall_model(state: StateSchemaType, config: RunnableConfig) -> StateSchemaType:
        state = _get_model_input_state(state)
        response = cast(AIMessage, await model_runnable.ainvoke(state, config))
        # add agent name to the AIMessage
        response.name = name
        if _are_more_steps_needed(state, response):
            return {
                "messages": [
                    AIMessage(
                        id=response.id,
                        content="Sorry, need more steps to process this request.",
                    )
                ]
            }
        # We return a list, because this will get added to the existing list
        return {"messages": [response]}

    input_schema: StateSchemaType
    if pre_model_hook is not None:
        # For now, use the same schema - this is a simplified version
        input_schema = state_schema
    else:
        input_schema = state_schema

    def generate_structured_response(
        state: StateSchemaType, config: RunnableConfig
    ) -> StateSchemaType:
        messages = _get_state_value(state, "messages")
        structured_response_schema = response_format
        if isinstance(response_format, tuple):
            system_prompt, structured_response_schema = response_format
            messages = [SystemMessage(content=system_prompt)] + list(messages)

        model_with_structured_output = _get_model(model).with_structured_output(
            cast(StructuredResponseSchema, structured_response_schema)
        )
        response = model_with_structured_output.invoke(messages, config)
        return {"structured_response": response}

    async def agenerate_structured_response(
        state: StateSchemaType, config: RunnableConfig
    ) -> StateSchemaType:
        messages = _get_state_value(state, "messages")
        structured_response_schema = response_format
        if isinstance(response_format, tuple):
            system_prompt, structured_response_schema = response_format
            messages = [SystemMessage(content=system_prompt)] + list(messages)

        model_with_structured_output = _get_model(model).with_structured_output(
            cast(StructuredResponseSchema, structured_response_schema)
        )
        response = await model_with_structured_output.ainvoke(messages, config)
        return {"structured_response": response}

    if not tool_calling_enabled:
        # Handle case with no tools - same as original
        workflow = StateGraph(state_schema, config_schema=config_schema)
        workflow.add_node(
            "agent",
            RunnableCallable(call_model, acall_model),
            input_schema=input_schema,
        )
        if pre_model_hook is not None:
            workflow.add_node("pre_model_hook", pre_model_hook)
            workflow.add_edge("pre_model_hook", "agent")
            entrypoint = "pre_model_hook"
        else:
            entrypoint = "agent"

        workflow.set_entry_point(entrypoint)

        if post_model_hook is not None:
            workflow.add_node("post_model_hook", post_model_hook)
            workflow.add_edge("agent", "post_model_hook")

        if response_format is not None:
            workflow.add_node(
                "generate_structured_response",
                RunnableCallable(
                    generate_structured_response,
                    agenerate_structured_response,
                ),
            )
            if post_model_hook is not None:
                workflow.add_edge("post_model_hook", "generate_structured_response")
            else:
                workflow.add_edge("agent", "generate_structured_response")

        return workflow.compile(
            checkpointer=checkpointer,
            store=store,
            interrupt_before=interrupt_before,
            interrupt_after=interrupt_after,
            debug=debug,
            name=name,
        )

    # CUSTOM LOGIC: Define the function that determines whether to continue or not
    # This is where we add the quick_response termination logic
    def should_continue_with_quick_response_check(state: StateSchemaType) -> Union[str, list[Send]]:
        messages = _get_state_value(state, "messages")
        last_message = messages[-1]
        
        # CUSTOM: Check for quick_response routing (like transfer_to_* tools)
        # If quick_response is called, route directly to END (just like transfer tools route to agents)
        if isinstance(last_message, AIMessage) and last_message.tool_calls:
            for tool_call in last_message.tool_calls:
                tool_name = None
                if hasattr(tool_call, 'name'):
                    tool_name = tool_call.name
                elif isinstance(tool_call, dict):
                    tool_name = tool_call.get('name')
                elif hasattr(tool_call, 'get'):
                    tool_name = tool_call.get('name')
                
                if tool_name == 'quick_response':
                    # Route directly to END (same pattern as transfer_to_* → other agents)
                    return END
        
        # Original logic continues...
        # If there is no function call, then we finish
        if not isinstance(last_message, AIMessage) or not last_message.tool_calls:
            if post_model_hook is not None:
                return "post_model_hook"
            elif response_format is not None:
                return "generate_structured_response"
            else:
                return END
        # Otherwise if there is, we continue
        else:
            if version == "v1":
                return "tools"
            elif version == "v2":
                if post_model_hook is not None:
                    return "post_model_hook"
                tool_calls = [
                    tool_node.inject_tool_args(call, state, store)
                    for call in last_message.tool_calls
                ]
                return [Send("tools", [tool_call]) for tool_call in tool_calls]

    # Define a new graph
    workflow = StateGraph(state_schema or AgentState, config_schema=config_schema)

    # Define the two nodes we will cycle between
    workflow.add_node(
        "agent",
        RunnableCallable(call_model, acall_model),
        input_schema=input_schema,
    )
    workflow.add_node("tools", tool_node)

    # Optionally add a pre-model hook node
    if pre_model_hook is not None:
        workflow.add_node("pre_model_hook", pre_model_hook)
        workflow.add_edge("pre_model_hook", "agent")
        entrypoint = "pre_model_hook"
    else:
        entrypoint = "agent"

    # Set the entrypoint as `agent`
    workflow.set_entry_point(entrypoint)

    agent_paths = []
    post_model_hook_paths = [entrypoint, "tools"]

    # Add a post model hook node if post_model_hook is provided
    if post_model_hook is not None:
        workflow.add_node("post_model_hook", post_model_hook)
        agent_paths.append("post_model_hook")
        workflow.add_edge("agent", "post_model_hook")
    else:
        agent_paths.append("tools")

    # Add a structured output node if response_format is provided
    if response_format is not None:
        workflow.add_node(
            "generate_structured_response",
            RunnableCallable(
                generate_structured_response,
                agenerate_structured_response,
            ),
        )
        if post_model_hook is not None:
            post_model_hook_paths.append("generate_structured_response")
        else:
            agent_paths.append("generate_structured_response")
    else:
        if post_model_hook is not None:
            post_model_hook_paths.append(END)
        else:
            agent_paths.append(END)

    if post_model_hook is not None:
        def post_model_hook_router(state: StateSchemaType) -> Union[str, list[Send]]:
            """Route to the next node after post_model_hook."""
            messages = _get_state_value(state, "messages")
            tool_messages = [
                m.tool_call_id for m in messages if isinstance(m, ToolMessage)
            ]
            last_ai_message = next(
                m for m in reversed(messages) if isinstance(m, AIMessage)
            )
            pending_tool_calls = [
                c for c in last_ai_message.tool_calls if c["id"] not in tool_messages
            ]

            if pending_tool_calls:
                pending_tool_calls = [
                    tool_node.inject_tool_args(call, state, store)
                    for call in pending_tool_calls
                ]
                return [Send("tools", [tool_call]) for tool_call in pending_tool_calls]
            elif isinstance(messages[-1], ToolMessage):
                return entrypoint
            elif response_format is not None:
                return "generate_structured_response"
            else:
                return END

        workflow.add_conditional_edges(
            "post_model_hook",
            post_model_hook_router,
            path_map=post_model_hook_paths,
        )

    # CUSTOM: Use our modified should_continue function
    workflow.add_conditional_edges(
        "agent",
        should_continue_with_quick_response_check,
        path_map=agent_paths,
    )

    def route_tool_responses(state: StateSchemaType) -> str:
        messages = _get_state_value(state, "messages")
        for m in reversed(messages):
            if not isinstance(m, ToolMessage):
                break
            if m.name in should_return_direct:
                return END

        # handle a case of parallel tool calls where
        # the tool w/ `return_direct` was executed in a different `Send`
        if isinstance(m, AIMessage) and m.tool_calls:
            if any(call["name"] in should_return_direct for call in m.tool_calls):
                return END

        return entrypoint

    if should_return_direct:
        workflow.add_conditional_edges(
            "tools", route_tool_responses, path_map=[entrypoint, END]
        )
    else:
        workflow.add_edge("tools", entrypoint)

    # Finally, we compile it!
    return workflow.compile(
        checkpointer=checkpointer,
        store=store,
        interrupt_before=interrupt_before,
        interrupt_after=interrupt_after,
        debug=debug,
        name=name,
    )
