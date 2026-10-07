import * as vscode from "vscode";
import {
  currentModel, get, post, workspacePath,
} from "./apiClient";
import {
  clearProposal, getProposal, getSession,
  setProposal, setSession,
} from "./sessionState";

interface SessionResp { session_id: string; }
interface ProposalResp {
  proposal_id: string;
  status: string;
  file_count: number;
}

export async function cmdCreateSession(
  ctx: vscode.ExtensionContext
): Promise<void> {
  try {
    const data = await post<SessionResp>("/sessions", {
      workspace: workspacePath(),
      model: currentModel(),
      locale: vscode.workspace
        .getConfiguration("biancheng")
        .get<string>("locale", "zh-CN"),
    });
    setSession(ctx, data.session_id);
    vscode.window.showInformationMessage(
      `Session: ${data.session_id}`
    );
  } catch (err) {
    vscode.window.showErrorMessage(`Create session failed: ${err}`);
  }
}

export async function cmdPropose(
  ctx: vscode.ExtensionContext
): Promise<void> {
  const sid = getSession(ctx);
  if (!sid) {
    vscode.window.showWarningMessage("Create a session first.");
    return;
  }
  const editor = vscode.window.activeTextEditor;
  if (!editor) {
    vscode.window.showWarningMessage("Open a file first.");
    return;
  }
  const task = await vscode.window.showInputBox({
    prompt: "Describe the change",
    placeHolder: "e.g. add SEED_RATE constant",
  });
  if (!task) return;
  const rel = vscode.workspace.asRelativePath(editor.document.uri);
  try {
    const data = await post<ProposalResp>("/propose", {
      session_id: sid,
      task,
      files: [rel],
      workspace: workspacePath(),
      model: currentModel(),
    });
    setProposal(ctx, data.proposal_id);
    vscode.window.showInformationMessage(
      `Proposal ${data.proposal_id} (${data.file_count} files)`
    );
  } catch (err) {
    vscode.window.showErrorMessage(`Propose failed: ${err}`);
  }
}

export async function cmdApprove(
  ctx: vscode.ExtensionContext
): Promise<void> {
  const sid = getSession(ctx);
  const pid = getProposal(ctx);
  if (!sid || !pid) {
    vscode.window.showWarningMessage("No active proposal.");
    return;
  }
  try {
    await post("/approve", { session_id: sid, proposal_id: pid });
    vscode.window.showInformationMessage(`Approved ${pid}`);
  } catch (err) {
    vscode.window.showErrorMessage(`Approve failed: ${err}`);
  }
}

export async function cmdApply(
  ctx: vscode.ExtensionContext
): Promise<void> {
  const sid = getSession(ctx);
  const pid = getProposal(ctx);
  if (!sid || !pid) {
    vscode.window.showWarningMessage("No active proposal.");
    return;
  }
  try {
    await post("/apply", { session_id: sid, proposal_id: pid });
    vscode.window.showInformationMessage(`Applied ${pid}`);
  } catch (err) {
    vscode.window.showErrorMessage(`Apply failed: ${err}`);
  }
}

export async function cmdVerify(
  ctx: vscode.ExtensionContext
): Promise<void> {
  const sid = getSession(ctx);
  const pid = getProposal(ctx);
  if (!sid || !pid) {
    vscode.window.showWarningMessage("No active proposal.");
    return;
  }
  try {
    await post("/verify", {
      session_id: sid,
      proposal_id: pid,
      workspace: workspacePath(),
    });
    vscode.window.showInformationMessage(`Verified ${pid}`);
  } catch (err) {
    vscode.window.showErrorMessage(`Verify failed: ${err}`);
  }
}

export async function cmdLearn(
  ctx: vscode.ExtensionContext
): Promise<void> {
  const sid = getSession(ctx);
  const pid = getProposal(ctx);
  if (!sid || !pid) {
    vscode.window.showWarningMessage("No active proposal.");
    return;
  }
  try {
    await post("/learn", { session_id: sid, proposal_id: pid });
    clearProposal(ctx);
    vscode.window.showInformationMessage(`Learned ${pid}`);
  } catch (err) {
    vscode.window.showErrorMessage(`Learn failed: ${err}`);
  }
}

export function registerAll(ctx: vscode.ExtensionContext): void {
  const map: Array<[string, (c: vscode.ExtensionContext) => Promise<void>]> = [
    ["biancheng.createSession", cmdCreateSession],
    ["biancheng.propose", cmdPropose],
    ["biancheng.approve", cmdApprove],
    ["biancheng.apply", cmdApply],
    ["biancheng.verify", cmdVerify],
    ["biancheng.learn", cmdLearn],
  ];
  for (const [cmd, fn] of map) {
    ctx.subscriptions.push(
      vscode.commands.registerCommand(cmd, () => fn(ctx))
    );
  }
}
