"""真实多 agent / 多 LLM 运行时底层。

分层：
  L0: protocol / spec / worker_entry
  L1: agent_process / supervisor
  L2: model_router / process_role
  L3: factory （接入现有 backend/agent/runtime）

铁律：
  - 复用 backend/agent/runtime 的 AgentRole / Blackboard / RoleRegistry / AgentRuntime
  - 本包不重复定义 role / blackboard / runtime
  - IPC 消息强制 session_id
"""
