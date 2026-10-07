import * as vscode from "vscode";

const SESSION_KEY = "biancheng.sessionId";
const PROPOSAL_KEY = "biancheng.proposalId";

export function setSession(
  ctx: vscode.ExtensionContext,
  id: string
): void {
  ctx.workspaceState.update(SESSION_KEY, id);
}

export function getSession(
  ctx: vscode.ExtensionContext
): string | undefined {
  return ctx.workspaceState.get<string>(SESSION_KEY);
}

export function setProposal(
  ctx: vscode.ExtensionContext,
  id: string
): void {
  ctx.workspaceState.update(PROPOSAL_KEY, id);
}

export function getProposal(
  ctx: vscode.ExtensionContext
): string | undefined {
  return ctx.workspaceState.get<string>(PROPOSAL_KEY);
}

export function clearProposal(ctx: vscode.ExtensionContext): void {
  ctx.workspaceState.update(PROPOSAL_KEY, undefined);
}
