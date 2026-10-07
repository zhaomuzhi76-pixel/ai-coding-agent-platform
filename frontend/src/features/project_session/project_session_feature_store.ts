import type { CreateSessionPayload, } from "../../core/api/project_session_api";
import type { ProjectResponse, SessionResponse, } from "./contracts/project_session_contract";
import { Store } from "../../core/state/store";
import { defaultProjectSessionGateway, type ProjectSessionFeatureGateway, } from "./project_session_feature_gateway";
import { initialProjectSessionFeatureState, type ProjectSessionFeatureState, } from "./project_session_feature_state";
export type { ProjectSessionFeatureGateway, } from "./project_session_feature_gateway";
type ProjectPayload = {
    name: string;
    rootPath: string;
    projectId?: string;
    workspaceId?: string;
};
export class ProjectSessionFeatureStore extends Store<ProjectSessionFeatureState> {
    private readonly gateway: ProjectSessionFeatureGateway;
    private operation = 0;
    constructor(gateway: ProjectSessionFeatureGateway = defaultProjectSessionGateway) {
        super(initialProjectSessionFeatureState);
        this.gateway = gateway;
    }
    loadProject(projectId: string) {
        return this.request(() => this.gateway.getProject(projectId), value => this.setProject(value));
    }
    createProject(payload: ProjectPayload) {
        return this.request(() => this.gateway.createProject({
            name: payload.name,
            root_path: payload.rootPath,
            project_id: payload.projectId,
            workspace_id: payload.workspaceId,
        }), value => this.setProject(value));
    }
    removeProject(projectId: string) {
        return this.request(() => this.gateway.removeProject(projectId), () => this.update(state => ({
            ...state,
            phase: "ready",
            project: null,
            session: null,
            error: null,
        })));
    }
    createSession(payload: CreateSessionPayload) {
        return this.request(() => this.gateway.createSession(payload), value => this.setSession(value));
    }
    loadSession(sessionId: string) {
        return this.request(() => this.gateway.loadSession(sessionId), value => this.setSession(value));
    }
    startSession(sessionId: string) {
        return this.request(() => this.gateway.startSession(sessionId), value => this.setSession(value));
    }
    closeSession(sessionId: string) {
        return this.request(() => this.gateway.closeSession(sessionId), value => this.setSession(value));
    }
    removeSession(sessionId: string) {
        return this.request(() => this.gateway.removeSession(sessionId), result => {
            if (!result.removed)
                return;
            this.update(state => ({
                ...state,
                phase: "ready",
                session: null,
                error: null,
            }));
        });
    }
    async findActiveSession(projectId: string): Promise<SessionResponse | null> {
        const revision = this.begin();
        try {
            const result = await this.gateway.projectSessions(projectId);
            const active = result.sessions.find(session => session.project_id === projectId
                && session.status === "active"
                && session.ready) ?? null;
            if (this.operation === revision
                && active) {
                this.setSession(active);
            }
            return active;
        }
        catch (error) {
            this.fail(revision, error);
            throw error;
        }
    }
    clearSession(): void {
        this.update(state => ({
            ...state,
            session: null,
        }));
    }
    clear(): void {
        this.operation += 1;
        this.setSnapshot({
            ...initialProjectSessionFeatureState,
            revision: this.getSnapshot().revision + 1,
        });
    }
    private request<T>(operation: () => Promise<T>, commit: (value: T) => void): Promise<T> {
        const revision = this.begin();
        return operation()
            .then(value => {
            if (this.operation === revision) {
                commit(value);
            }
            return value;
        })
            .catch(error => {
            this.fail(revision, error);
            throw error;
        });
    }
    private begin(): number {
        const revision = this.getSnapshot().revision + 1;
        this.operation = revision;
        this.update(state => ({
            ...state,
            phase: "loading",
            error: null,
            revision,
        }));
        return revision;
    }
    private fail(revision: number, error: unknown): void {
        if (this.operation !== revision)
            return;
        this.update(state => ({
            ...state,
            phase: "error",
            error: error instanceof Error
                ? error.message
                : "project/session operation failed",
            revision,
        }));
    }
    private setProject(project: ProjectResponse): void {
        this.update(state => ({
            ...state,
            phase: "ready",
            project,
            error: null,
        }));
    }
    private setSession(session: SessionResponse): void {
        this.update(state => ({
            ...state,
            phase: "ready",
            session,
            error: null,
        }));
    }
}
