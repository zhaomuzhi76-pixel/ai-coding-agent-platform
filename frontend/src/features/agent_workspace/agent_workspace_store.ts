import { initialAgentWorkspaceState, type AgentWorkspaceState, } from "./agent_workspace_state";
import type { AgentWorkspaceGateway, AgentWorkspaceSocket, } from "./agent_workspace_gateway";
import { operationError, } from "./agent_workspace_store_support";
import { saveMessages, loadMessages } from "./persistence/session_messages_local_store";
import { saveModelPreference } from "./persistence/model_preference_local_store";
import { AgentWorkspaceExecution, } from "./agent_workspace_execution";
export type { AgentWorkspaceState, } from "./agent_workspace_state";
export type AgentWorkspaceListener = () => void;
export class AgentWorkspaceStore {
    private readonly gateway: AgentWorkspaceGateway;
    private readonly execution: AgentWorkspaceExecution;
    private state: AgentWorkspaceState = structuredClone(initialAgentWorkspaceState);
    private listeners = new Set<AgentWorkspaceListener>();
    private operationVersion = 0;
    private activeSocket: AgentWorkspaceSocket | null = null;
    constructor(gateway: AgentWorkspaceGateway) {
        this.gateway = gateway;
        this.execution = new AgentWorkspaceExecution(gateway);
    }
    getSnapshot(): AgentWorkspaceState {
        return this.state;
    }
    subscribe(listener: AgentWorkspaceListener) {
        this.listeners.add(listener);
        return () => this.listeners.delete(listener);
    }
    async selectSession(sessionId: string) {
        const operation = ++this.operationVersion;
        this.closeActiveSocket();
        this.patch({
            phase: "loading_session",
            session: null,
            result: null,
            error: null,
            message: "",
            messages: [],
            socketState: "idle",
        });
        try {
            const session = await this.gateway.loadSession(sessionId);
            if (!this.isCurrent(operation)) {
                return;
            }
            const restoredMessages =
                loadMessages(session.session_id);
            this.patch({
                phase: "ready",
                session,
                error: null,
                messages: restoredMessages,
            });
        }
        catch (error) {
            if (!this.isCurrent(operation)) {
                return;
            }
            this.patch({
                phase: "error",
                error: operationError(error),
            });
            throw error;
        }
    }
    async execute() {
        if (this.state.phase === "executing") {
            throw new Error("agent execution already active");
        }
        const operation = ++this.operationVersion;
        try {
            const result = await this.execution.run(this.state, {
                patch: value => this.patchCurrent(operation, value),
                appendMessage: message => this.appendCurrentMessage(operation, message),
                setSocket: socket => this.setActiveSocket(operation, socket),
                isCurrent: () => this.isCurrent(operation),
            });
            if (this.isCurrent(operation)) {
                this.patch({
                    phase: "success",
                    result,
                    error: null,
                });
            }
            return result;
        }
        finally {
            if (this.isCurrent(operation)) {
                this.activeSocket = null;
            }
        }
    }
    appendMessage(message: AgentWorkspaceState["messages"][number]) {
        const nextMessages = [
            ...this.state.messages,
            message,
        ];
        this.patch({
            messages: nextMessages,
        });
        const sid = this.state.session?.session_id;
        if (sid) {
            saveMessages(sid, nextMessages);
        }
    }
    setMessage(message: string) {
        if (this.isExecuting()) {
            return;
        }
        this.patch({
            message,
            error: null,
            phase: this.state.session
                ? "ready"
                : this.state.phase,
        });
    }
    setModelSelection(model: AgentWorkspaceState["model"]) {
        // 允许执行中切换：切模型只影响下一次任务，不干扰正在执行的操作。
        // 旧实现在 isExecuting() 时静默 return，导致 UI 显示切了但 state 未更新。
        this.patch({
            model,
            error: null,
        });
        saveModelPreference(model);
    }
    clearResult() {
        this.patch({
            result: null,
            error: null,
            phase: this.state.session ? "ready" : "idle",
        })
    }

    reset() {
        ++this.operationVersion;
        this.closeActiveSocket();
        const preservedModel = this.state.model;
        this.state =
            structuredClone(initialAgentWorkspaceState);
        this.state.model = preservedModel;
        this.emit();
    }
    dispose() {
        ++this.operationVersion;
        this.closeActiveSocket();
        this.listeners.clear();
    }
    private isExecuting() {
        return this.state.phase === "executing";
    }
    private isCurrent(operation: number) {
        return operation === this.operationVersion;
    }
    private patchCurrent(operation: number, value: Partial<AgentWorkspaceState>) {
        if (this.isCurrent(operation)) {
            this.patch(value);
        }
    }
    private appendCurrentMessage(operation: number, message: AgentWorkspaceState["messages"][number]) {
        if (this.isCurrent(operation)) {
            this.appendMessage(message);
        }
    }
    private setActiveSocket(operation: number, socket: AgentWorkspaceSocket | null) {
        if (this.isCurrent(operation)) {
            this.activeSocket = socket;
        }
        else {
            socket?.close();
        }
    }
    private closeActiveSocket() {
        this.activeSocket?.close();
        this.activeSocket = null;
    }
    private patch(value: Partial<AgentWorkspaceState>) {
        this.state = {
            ...this.state,
            ...value,
            revision: this.state.revision + 1,
        };
        this.emit();
    }
    private emit() {
        for (const listener of this.listeners) {
            listener();
        }
    }
}
