// Moves an item up or down by swapping its position with the neighbour's
export function ReorderButtons({
  index,
  count,
  disabled,
  onMove,
}: {
  index: number;
  count: number;
  disabled: boolean;
  onMove: (delta: -1 | 1) => void;
}) {
  const button =
    "rounded border border-gray-300 px-2 py-1 text-sm hover:bg-gray-50 disabled:text-gray-300";
  return (
    <div className="flex gap-1">
      <button
        type="button"
        aria-label="Move up"
        className={button}
        disabled={disabled || index === 0}
        onClick={() => onMove(-1)}
      >
        Up
      </button>
      <button
        type="button"
        aria-label="Move down"
        className={button}
        disabled={disabled || index === count - 1}
        onClick={() => onMove(1)}
      >
        Down
      </button>
    </div>
  );
}
