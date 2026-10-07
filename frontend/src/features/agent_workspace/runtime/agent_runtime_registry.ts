import type {
 AgentRuntimeCapability,
} from "./agent_runtime_capability_contract"


export class AgentRuntimeRegistry {


 private capabilities:
 AgentRuntimeCapability[]=[]


 register(
  capability:AgentRuntimeCapability,
 ){

  this.capabilities=[
   ...this.capabilities,
   capability,
  ]

 }


 list(){

  return this.capabilities

 }


 resolve(
  id:string,
 ){

  return this.capabilities.find(
   item=>item.id===id,
  )

 }

}
