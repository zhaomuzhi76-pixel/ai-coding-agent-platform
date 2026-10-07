import {
  I18nProvider,
} from "../core/i18n/i18n"

import {
  ApplicationSurface,
} from "./integration/application_surface"

import {
  ControlPlaneProvider,
} from "./integration/context/control_plane_context"

import {
  ErrorBoundary,
} from "./integration/error_boundary"

export function App() {
  return (
    <I18nProvider>
      <ErrorBoundary label="i18n">
        <ControlPlaneProvider>
          <ErrorBoundary label="control-plane">
            <ApplicationSurface />
          </ErrorBoundary>
        </ControlPlaneProvider>
      </ErrorBoundary>
    </I18nProvider>
  )
}
