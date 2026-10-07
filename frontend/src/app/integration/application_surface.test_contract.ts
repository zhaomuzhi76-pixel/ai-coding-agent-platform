export interface ApplicationSurfaceContract {
  id: string
  title: string
  ready: boolean
}

export const applicationSurfaceContract:
  ApplicationSurfaceContract = {
  id: "application-control-plane",
  title: "AI Engineering Control Plane",
  ready: true,
}
