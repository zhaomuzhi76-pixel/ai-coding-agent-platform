export interface FileNodeSource {

  readText(): Promise<string>

  writeText?(
    content:string,
  ): Promise<void>

}
