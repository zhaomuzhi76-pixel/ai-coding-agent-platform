import {
  useCallback,
  useMemo,
  useRef,
} from "react"

import type {
  ChangeEvent,
  KeyboardEvent,
  UIEvent,
} from "react"

import {
  useEditorDocument,
} from "./editor_document"

import {
  lineCount,
  statusLabel,
} from "./editor_surface_support"

import type {
  EditorSurfaceProps,
} from "./editor_surface_contract"

export function useEditorSurfaceController(
  props: EditorSurfaceProps,
) {
  const document =
    useEditorDocument(
      props.activeFileSource,
      props.fileVersion ?? 0,
    )

  const editorRef =
    useRef<HTMLTextAreaElement | null>(
      null,
    )

  const gutterRef =
    useRef<HTMLDivElement | null>(
      null,
    )

  const lines = useMemo(
    () =>
      Array.from(
        {
          length: lineCount(
            document.content,
          ),
        },
        (_, index) =>
          index + 1,
      ),
    [document.content],
  )

  const onChange = useCallback(
    (
      event:
        ChangeEvent<HTMLTextAreaElement>,
    ) => {
      document.changeContent(
        event.currentTarget.value,
      )
    },
    [document.changeContent],
  )

  const onKeyDown = useCallback(
    (
      event:
        KeyboardEvent<HTMLTextAreaElement>,
    ) => {
      if (
        (event.ctrlKey ||
          event.metaKey) &&
        event.key.toLowerCase() === "s"
      ) {
        event.preventDefault()
        void document.save()
        return
      }

      if (
        event.key !== "Tab" ||
        event.shiftKey
      ) {
        return
      }

      event.preventDefault()

      const textarea =
        event.currentTarget

      const start =
        textarea.selectionStart

      const end =
        textarea.selectionEnd

      const next =
        textarea.value.slice(
          0,
          start,
        ) +
        "\t" +
        textarea.value.slice(end)

      document.changeContent(next)

      requestAnimationFrame(() => {
        const current =
          editorRef.current

        if (!current) {
          return
        }

        const caret =
          start + 1

        current.selectionStart =
          caret
        current.selectionEnd =
          caret
      })
    },
    [
      document.changeContent,
      document.save,
    ],
  )

  const onScroll = useCallback(
    (
      event:
        UIEvent<HTMLTextAreaElement>,
    ) => {
      if (gutterRef.current) {
        gutterRef.current.scrollTop =
          event.currentTarget.scrollTop
      }
    },
    [],
  )

  const editable =
    !document.readOnly &&
    !document.loading &&
    !document.saving

  const saveDisabled =
    document.readOnly ||
    document.loading ||
    document.saving ||
    !document.dirty

  const status =
    statusLabel(
      document.loading,
      document.saving,
      document.loadError,
      document.saveError,
      document.dirty,
    )

  return {
    document,
    editorRef,
    gutterRef,
    lines,
    editable,
    saveDisabled,
    status,
    onChange,
    onKeyDown,
    onScroll,
  }
}
