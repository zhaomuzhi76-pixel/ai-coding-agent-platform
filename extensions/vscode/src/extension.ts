import * as vscode from "vscode";
import { registerAll } from "./commands";
import { startLspClient, stopLspClient } from "./lspClient";

export function activate(
  context: vscode.ExtensionContext
): void {
  try {
    startLspClient(context);
  } catch (err) {
    vscode.window.showErrorMessage(
      `LSP client start failed: ${err}`
    );
  }
  registerAll(context);
  vscode.window.showInformationMessage(
    "Biancheng AI Coding activated."
  );
}

export async function deactivate(): Promise<void> {
  await stopLspClient();
}
