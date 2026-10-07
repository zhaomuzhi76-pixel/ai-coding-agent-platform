import type {
  FileNodeSource,
} from "../explorer/file_node_source"

export async function writeEditorFile(
  source:FileNodeSource,
  content:string,
):Promise<void>{
  if(!source.writeText){
    throw new Error(
      "File is read only",
    )
  }

  await source.writeText(
    content,
  )
}
