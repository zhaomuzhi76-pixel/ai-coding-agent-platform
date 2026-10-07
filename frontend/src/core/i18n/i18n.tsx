import {
  createContext,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react"
import { message, type MessageKey } from "./messages"
import {
  readLocale,
  writeLocale,
  type Locale,
} from "./locale"

interface I18nValue {
  locale: Locale
  setLocale(locale: Locale): void
  t(key: MessageKey): string
}

const I18nContext =
  createContext<I18nValue | null>(null)

export function I18nProvider(
  props: { children: ReactNode },
) {
  const [locale, setLocaleState] =
    useState<Locale>(readLocale)

  const value = useMemo<I18nValue>(
    () => ({
      locale,
      setLocale(next) {
        writeLocale(next)
        setLocaleState(next)
      },
      t(key) {
        return message(locale, key)
      },
    }),
    [locale],
  )

  return (
    <I18nContext.Provider value={value}>
      {props.children}
    </I18nContext.Provider>
  )
}

export function useI18n(): I18nValue {
  const value = useContext(I18nContext)

  if (!value) {
    throw new Error("i18n context required")
  }

  return value
}
