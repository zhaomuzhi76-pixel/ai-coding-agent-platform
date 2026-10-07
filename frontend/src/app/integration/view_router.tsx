import type {
  ComponentType,
  ReactElement,
} from "react"

import {
  useNavTab,
  type NavTab,
} from "../ui/shell/global_nav"

import type {
  ApplicationPluginProps,
} from "../plugins/plugin_contract"

import {
  PlatformView,
} from "../views/platform_view"
import {
  ModelsView,
} from "../../features/models/ui"
import {
  FinetunePage,
} from "../views/pages/finetune_page"
import {
  RagPage,
} from "../views/pages/rag_page"
import {
  ChatbotPage,
} from "../views/pages/chatbot_page"
import {
  McpPage,
} from "../views/pages/mcp_page"
import {
  SecurityPage,
} from "../views/pages/security_page"
import {
  MonitorPage,
} from "../views/pages/monitor_page"
import {
  ProvidersView,
} from "../../features/providers/ui"

interface ViewRouterProps {
  capability: {
    agentWorkspaceStore: ApplicationPluginProps["store"]
    agentWorkspaceController: ApplicationPluginProps["controller"]
    workspaceController: ApplicationPluginProps["workspaceController"]
    bridge: ApplicationPluginProps["bridge"]
  }
  codingPlugin: {
    render: ComponentType<ApplicationPluginProps>
  }
}

const TAB_VIEWS: Record<NavTab, () => ReactElement | null> = {
  platform: () => <PlatformView />,
  models: () => <ModelsView />,
  finetune: () => <FinetunePage />,
  rag: () => <RagPage />,
  chatbot: () => <ChatbotPage />,
  mcp: () => <McpPage />,
  security: () => <SecurityPage />,
  monitor: () => <MonitorPage />,
  providers: () => <ProvidersView />,
  coding: () => null,
}

export function ViewRouter(props: ViewRouterProps) {
  const tab: NavTab = useNavTab()

  if (tab === "coding") {
    const Coding = props.codingPlugin.render
    const cap = props.capability
    return (
      <Coding
        state={cap.agentWorkspaceStore.getSnapshot()}
        store={cap.agentWorkspaceStore}
        controller={cap.agentWorkspaceController}
        workspaceController={cap.workspaceController}
        bridge={cap.bridge}
      />
    )
  }

  return TAB_VIEWS[tab]()
}
