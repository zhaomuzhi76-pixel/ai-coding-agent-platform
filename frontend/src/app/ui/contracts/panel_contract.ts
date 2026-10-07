export type PanelPosition =
  | "left"
  | "center"
  | "right"
  | "bottom"

export interface PanelContract {
  id: string
  title: string
  position: PanelPosition
  visible: boolean
}
