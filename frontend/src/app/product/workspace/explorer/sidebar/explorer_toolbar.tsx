interface Props {
  onCollapse?: () => void
}

export function ExplorerToolbar(
  props: Props,
) {

  return (
    <div className="explorer-toolbar">

      <button
        type="button"
        onClick={
          props.onCollapse
        }
      >
        ◀
      </button>

    </div>
  )

}
