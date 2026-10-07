import {
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react"

import {
  readEditorFile,
} from "./editor_file_reader"

import {
  writeEditorFile,
} from "./editor_file_writer"

import type {
  FileNodeSource,
} from "../explorer/file_node_source"

function errorMessage(
  error:unknown,
):string{
  return error instanceof Error
    ? error.message
    : String(error)
}

export interface EditorDocumentState {
  content:string
  loading:boolean
  saving:boolean
  dirty:boolean
  loadError:string|null
  saveError:string|null
  readOnly:boolean
  save():Promise<void>
  changeContent(content:string):void
}

export function useEditorDocument(
  source:FileNodeSource|null,
  fileVersion:number = 0,
):EditorDocumentState{
  const [content,setContent] =
    useState("")
  const [loading,setLoading] =
    useState(false)
  const [saving,setSaving] =
    useState(false)
  const [dirty,setDirty] =
    useState(false)
  const [loadError,setLoadError] =
    useState<string|null>(null)
  const [saveError,setSaveError] =
    useState<string|null>(null)

  const version =
    useRef(0)

  const trailingNewline =
    useRef(false)

  useEffect(()=>{
    const current =
      ++version.current

    setContent("")
    setLoading(false)
    setSaving(false)
    setDirty(false)
    setLoadError(null)
    setSaveError(null)
    trailingNewline.current = false

    if(!source){
      return
    }

    setLoading(true)

    void readEditorFile(source)
      .then(text=>{
        if(current !== version.current){
          return
        }

        trailingNewline.current =
          text.endsWith("\n")
        setContent(text)
        setDirty(false)
        setLoadError(null)
      })
      .catch(error=>{
        if(current !== version.current){
          return
        }

        setContent("")
        setDirty(false)
        setLoadError(
          errorMessage(error),
        )
      })
      .finally(()=>{
        if(current === version.current){
          setLoading(false)
        }
      })

    return ()=>{
      if(current === version.current){
        version.current++
      }
    }
  },[source, fileVersion])

  const save = useCallback(
    async()=>{
      const currentSource =
        source

      if(
        !currentSource?.writeText ||
        loading ||
        saving ||
        !dirty
      ){
        return
      }

      const current =
        version.current

      setSaving(true)
      setSaveError(null)

      const contentToWrite =
        trailingNewline.current &&
        !content.endsWith("\n")
          ? `${content}\n`
          : content

      try{
        await writeEditorFile(
          currentSource,
          contentToWrite,
        )

        if(current !== version.current){
          return
        }

        if(
          contentToWrite !== content
        ){
          setContent(contentToWrite)
        }

        setDirty(false)
        setSaveError(null)
      }catch(error){
        if(current !== version.current){
          return
        }

        setSaveError(
          errorMessage(error),
        )
      }finally{
        if(current === version.current){
          setSaving(false)
        }
      }
    },
    [
      content,
      dirty,
      loading,
      saving,
      source,
    ],
  )

  const changeContent =
    useCallback(
      (next:string)=>{
        if(loading || saving){
          return
        }

        setContent(next)
        setDirty(true)
        setSaveError(null)
      },
      [loading,saving],
    )

  return {
    content,
    loading,
    saving,
    dirty,
    loadError,
    saveError,
    readOnly:!source?.writeText,
    save,
    changeContent,
  }
}
