import type { ReactNode } from "react"
import { useState } from "react"

interface Props {
  code?: ReactNode
  prompt?: ReactNode
}

export function WorkspaceSplitView(props: Props) {

  const [ratio,setRatio] = useState(70)

  function startResize(e: React.PointerEvent<HTMLDivElement>) {

    const startY = e.clientY
    const startRatio = ratio
    const parent =
      e.currentTarget.parentElement

    if(!parent){
      return
    }

    const height =
      parent.getBoundingClientRect().height


    const move = (event: PointerEvent)=>{

      const delta =
        ((event.clientY-startY)/height)*100

      setRatio(
        Math.max(
          25,
          Math.min(
            90,
            startRatio + delta,
          ),
        ),
      )
    }


    const stop = ()=>{

      window.removeEventListener(
        "pointermove",
        move,
      )

      window.removeEventListener(
        "pointerup",
        stop,
      )

    }


    window.addEventListener(
      "pointermove",
      move,
    )

    window.addEventListener(
      "pointerup",
      stop,
    )

  }


  return (

    <div
      className="workspace-split-view"
      style={{
        display:"grid",
        gridTemplateRows:
          `${ratio}% 6px ${100-ratio}%`,
        height:"100%",
        minHeight:0,
      }}
    >

      <div
        style={{
          minHeight:0,
          overflow:"hidden",
        }}
      >
        {props.code}
      </div>


      <div
        onPointerDown={startResize}
        style={{
          cursor:"row-resize",
        }}
      />


      <div
        style={{
          minHeight:0,
          overflow:"auto",
        }}
      >
        {props.prompt}
      </div>

    </div>

  )
}
