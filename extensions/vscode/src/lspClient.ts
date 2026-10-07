import * as vscode from "vscode";
import {
  LanguageClient,
  LanguageClientOptions,
  ServerOptions,
} from "vscode-languageclient/node";

let client: LanguageClient | undefined;

export function getConfig<T>(key: string, fallback: T): T {
  return vscode.workspace
    .getConfiguration("biancheng")
    .get<T>(key, fallback);
}

export function startLspClient(
  context: vscode.ExtensionContext
): LanguageClient {
  if (client) return client;

  const command = getConfig<string>("serverCommand", "python");
  const args = getConfig<string[]>("serverArgs", [
    "-m",
    "backend.lsp.cli",
  ]);

  const workspace =
    vscode.workspace.workspaceFolders?.[0]?.uri.fsPath ?? process.cwd();

  const serverOptions: ServerOptions = {
    command,
    args,
    options: { cwd: workspace, env: process.env },
  };

  const clientOptions: LanguageClientOptions = {
    documentSelector: [{ scheme: "file", language: "python" }],
    synchronize: {
      fileEvents: vscode.workspace.createFileSystemWatcher("**/*.py"),
    },
  };

  client = new LanguageClient(
    "bianchengLsp",
    "Biancheng AI LSP",
    serverOptions,
    clientOptions
  );
  client.start();
  context.subscriptions.push({ dispose: () => client?.stop() });
  return client;
}

export async function stopLspClient(): Promise<void> {
  if (client) {
    await client.stop();
    client = undefined;
  }
}
