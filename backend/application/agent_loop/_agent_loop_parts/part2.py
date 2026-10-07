"""Part 2 of agent_loop.py."""
from __future__ import annotations
from backend.core.observability.silent import swallow

from .part1 import (Any, DEFAULT_MAX_STEPS, DEFAULT_MODE, LLM_CALL_TIMEOUT_SEC, asyncio, build_system_prompt, dispatch_tool, maybe_intercept, parse_action, render_observation, time,)  # noqa
from .part1 import _dedup_key  # noqa

async def run_agent_loop(
    task: str,
    workspace: str,
    *,
    gateway: Any,
    provider: str,
    model: str,
    max_steps: int = DEFAULT_MAX_STEPS,
    on_step: Any = None, sandbox_mode: str = DEFAULT_MODE,
    domains: list | None = None,
    tenant_id: str = "",
) -> dict[str, Any]:
    """自主循环执行 task。

    gateway 需实现 async chat(provider, messages, model, **kw) -> str

    返回 {success, answer, steps, trace} 或 {success:False, error, ...}
    """
    if not task.strip():
        return {"success": False, "error": "empty task", "steps": 0}
    if gateway is None:
        return {"success": False, "error": "gateway required", "steps": 0}

    messages: list[dict[str, str]] = [
        {"role": "system", "content": build_system_prompt(workspace, max_steps, domains)},
        {"role": "user", "content": f"任务：{task}"},
    ]
    trace: list[dict[str, Any]] = []
    visited: set[str] = set()
    _unknown_tool_count = 0  # [FLB] 防御：连续未知工具上限
    changes: list[dict[str, Any]] = []

    for step in range(1, max_steps + 1):
        # 硬超时 60s：无论底层挂在哪，都不让事件循环被占满
        try:
            raw = await asyncio.wait_for(
                gateway.chat(provider, messages, model),
                timeout=LLM_CALL_TIMEOUT_SEC,
            )
        except asyncio.TimeoutError:
            # [FR2] 超时也返回 answer（前端需要文字），含已有 trace
            _steps_done = step - 1
            _last_obs = trace[-1].get("observation", "") if trace else ""
            _answer = (
                f"（推理超时，已执行 {_steps_done} 步）"
            )
            if _last_obs:
                _answer += f"\n最后观察：{_last_obs[:300]}"
            return {
                "success": False,
                "answer": _answer,
                "error": (
                    f"LLM call timeout "
                    f"({LLM_CALL_TIMEOUT_SEC}s): provider={provider} "
                    f"model={model}"
                ),
                "steps": _steps_done,
                "trace": trace,
            }
        except Exception as exc:
            _steps_done = step - 1
            _last_obs = trace[-1].get("observation", "") if trace else ""
            _answer = f"（推理失败：{type(exc).__name__}，已执行 {_steps_done} 步）"
            if _last_obs:
                _answer += f"\n最后观察：{_last_obs[:300]}"
            return {
                "success": False,
                "answer": _answer,
                "error": f"LLM call failed: {type(exc).__name__}: {exc}",
                "steps": _steps_done,
                "trace": trace,
            }

        action = parse_action(str(raw))
        thought = str(action.get("thought", ""))

        # 完成分支
        if action.get("done") is True:
            answer = str(action.get("answer", "")).strip()
            trace.append({"step": step, "thought": thought, "done": True})
            return {
                "success": True,
                "answer": answer or "(无回答)",
                "steps": step,
                "trace": trace,
                "changes": changes,
            }

        # 工具分支
        name = str(action.get("action", "")).strip()
        args = action.get("args") or {}
        if not isinstance(args, dict):
            args = {}

        # 防重复：同工具同路径视为重复
        key = _dedup_key(name, args)
        if key and key in visited:
            obs = (
                f"ERROR: 你刚才已经调用过 {name}({args})，结果相同。"
                f"请换一个动作，或立刻 done=true 总结。"
            )
            entry = {
                "step": step, "thought": thought,
                "action": name, "args": args,
                "observation": obs[:500], "repeated": True,
                "ts_ms": int(time.time() * 1000),
            }
            trace.append(entry)
            if on_step is not None:
                res = on_step(entry)
                if asyncio.iscoroutine(res):
                    try:
                        await res
                    except Exception as e:
                        swallow("application.agent_loop._agent_loop_parts.part2:105", e)
            messages.append({"role": "assistant", "content": str(raw)})
            messages.append({"role": "user", "content": f"工具结果：\n{obs}"})
            continue

        if key:
            visited.add(key)

        # 审批拦截：写操作先挂起等用户批准
        decision = await maybe_intercept(
            name, args, workspace, on_step=on_step,
            mode=sandbox_mode, tenant_id=tenant_id,
        )
        if decision in ("rejected", "timeout"):
            obs = (
                f"用户拒绝或超时：{name}({args}) 未执行。"
                f"请换方案或直接 done=true。"
            )
            entry = {
                "step": step, "thought": thought,
                "action": name, "args": args,
                "observation": obs[:500],
                "rejected": True,
                "ts_ms": int(time.time() * 1000),
            }
            trace.append(entry)
            if on_step is not None:
                res = on_step(entry)
                if asyncio.iscoroutine(res):
                    try:
                        await res
                    except Exception as e:
                        swallow("application.agent_loop._agent_loop_parts.part2:137", e)
            messages.append({"role": "assistant", "content": str(raw)})
            messages.append({
                "role": "user",
                "content": f"工具结果：\n{obs}",
            })
            continue

        # 写操作：写前抓 before 快照（用现有 read_file 工具，不引入新依赖）
        before_snapshot = ""
        if name in ("write_file", "edit_file"):
            path_for_snap = str(args.get("path", "")).strip()
            if path_for_snap and workspace:
                try:
                    snap = await dispatch_tool(
                        "read_file", {"path": path_for_snap}, workspace,
                        domains=domains,
                    )
                    if isinstance(snap, dict):
                        for k in ("content", "text", "data"):
                            v = snap.get(k)
                            if isinstance(v, str):
                                before_snapshot = v
                                break
                except Exception:
                    before_snapshot = ""

        result = await dispatch_tool(name, args, workspace, domains=domains)

        # [FLB] 未知工具防御：连续 3 次幻觉工具名 → 强制终止
        if isinstance(result, dict) and not result.get("ok"):
            _err = str(result.get("error", ""))
            if "unknown tool" in _err:
                _unknown_tool_count += 1
                if _unknown_tool_count >= 3:
                    trace.append({
                        "step": step, "thought": thought,
                        "action": name, "args": args,
                        "observation": _err[:200],
                        "unknown_tool_aborted": True,
                    })
                    # [FR2] 降级：仍返回 answer（前端需要文字），说明为何失败
                    _fallback_answer = (
                        f"抱歉，我尝试调用了不存在的工具（{name}）。"
                        f"本次可用的工具仅有：read_file / list_dir / grep / "
                        f"count_files / file_stat / write_file / edit_file / "
                        f"delete_file / run_command。请用其中一个重试，"
                        f"或告诉我具体想做什么。"
                    )
                    return {
                        "success": True,
                        "answer": _fallback_answer,
                        "steps": step,
                        "trace": trace,
                        "changes": changes,
                        "degraded": True,
                    }
            else:
                _unknown_tool_count = 0  # 有正常返回就重置

        # 写操作：成功则收集 changes（前端自动渲染 diff）
        if isinstance(result, dict) and result.get("ok"):
            if name == "write_file":
                changes.append({
                    "file": str(args.get("path", "")),
                    "before": before_snapshot,
                    "after": str(args.get("content", "")),
                })
            elif name == "edit_file":
                changes.append({
                    "file": str(args.get("path", "")),
                    "before": before_snapshot or str(args.get("old", "")),
                    "after": str(args.get("new", "")),
                })

        obs = render_observation(result)

        entry = {
            "step": step,
            "thought": thought,
            "action": name,
            "args": args,
            "observation": obs[:500],
            "ts_ms": int(time.time() * 1000),
        }
        trace.append(entry)
        if on_step is not None:
            res = on_step(entry)
            if asyncio.iscoroutine(res):
                try:
                    await res
                except Exception as e:
                    swallow("application.agent_loop._agent_loop_parts.part2:197", e)

        remaining = max_steps - step
        entry["remaining"] = remaining

        messages.append({"role": "assistant", "content": str(raw)})
        if remaining <= 2:
            tail = f"\n\n【警告】只剩 {remaining} 步。立刻 done=true 总结。"
        elif remaining <= 4:
            tail = f"\n\n【提示】剩 {remaining} 步。信息足够请立即 done=true。"
        else:
            tail = "\n\n继续。"
        messages.append({
            "role": "user",
            "content": f"工具结果：\n{obs}{tail}",
        })

    _last_obs = trace[-1].get("observation", "") if trace else ""
    _answer = f"（已达步骤上限 {max_steps}）"
    if _last_obs:
        _answer += f"\n最后观察：{_last_obs[:300]}"
    return {
        "success": False,
        "answer": _answer,
        "error": f"max steps ({max_steps}) exceeded",
        "steps": max_steps,
        "trace": trace,
        "changes": changes,
    }
