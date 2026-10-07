import type {
  FileNodeSource,
} from "../explorer/file_node_source"

export async function readEditorFile(
  source:FileNodeSource,
):Promise<string>{
  return await source.readText()
}
