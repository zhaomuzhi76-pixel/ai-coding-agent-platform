import type {
  ReactNode,
} from "react"


export function IdeBottomWorkspace(
  props:{
    terminal:ReactNode
    review:ReactNode
  },
){

  return (

    <section className="ide-bottom-workspace">


      <div className="ide-bottom-tab">

        TERMINAL

      </div>


      {props.terminal}


      <div className="ide-bottom-tab">

        DIFF REVIEW

      </div>


      {props.review}


    </section>

  )

}
