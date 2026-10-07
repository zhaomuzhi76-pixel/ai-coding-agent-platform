export type WorkspaceResizeTarget =
  | "sidebar"
  | "agent"
  | "bottom"


export class WorkspaceResizeController {

  private root: HTMLElement

  constructor(root: HTMLElement){
    this.root = root
  }


  setWidth(
    target: WorkspaceResizeTarget,
    value:number,
  ){

    if(target === "sidebar"){
      this.root.style.setProperty(
        "--explorer-width",
        `${value}px`,
      )
    }


    if(target === "agent"){
      this.root.style.setProperty(
        "--workspace-agent-width",
        `${value}px`,
      )
    }

  }


  setHeight(
    value:number,
  ){

    this.root.style.setProperty(
      "--workspace-bottom-height",
      `${value}px`,
    )

  }

}
