/** 通用可拖拽分隔条（VSCode 风格） */
import { useCallback, useEffect, useRef, useState } from 'react';

export type Direction = 'horizontal' | 'vertical';

interface Props {
  direction: Direction;
  /** 当前尺寸（像素或比例），拖动时回调新值 */
  size: number;
  onResize: (next: number) => void;
  /** 最小值 / 最大值（像素） */
  min?: number;
  max?: number;
  /** 双击复位值 */
  resetValue?: number;
  /** 存储键（用于持久化） */
  storageKey?: string;
}

export function ResizeHandle({
  direction, size, onResize, min = 80, max = 800,
  resetValue, storageKey,
}: Props) {
  const dragging = useRef(false);
  const startPos = useRef(0);
  const startSize = useRef(0);
  const [hover, setHover] = useState(false);

  const onMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    dragging.current = true;
    startPos.current = direction === 'vertical' ? e.clientX : e.clientY;
    startSize.current = size;
    document.body.style.cursor =
      direction === 'vertical' ? 'col-resize' : 'row-resize';
    document.body.style.userSelect = 'none';
    document.body.classList.add('mr-resizing');
  }, [direction, size]);

  useEffect(() => {
    const onMove = (e: MouseEvent) => {
      if (!dragging.current) return;
      const cur = direction === 'vertical' ? e.clientX : e.clientY;
      const delta = cur - startPos.current;
      let next = startSize.current + delta;
      // 垂直分隔条：向左拖减小宽度
      if (direction === 'vertical') next = startSize.current + delta;
      next = Math.max(min, Math.min(max, next));
      onResize(next);
    };
    const onUp = () => {
      if (!dragging.current) return;
      dragging.current = false;
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
      document.body.classList.remove('mr-resizing');
      if (storageKey) {
        try { localStorage.setItem(storageKey, String(size)); } catch {}
      }
    };
    document.addEventListener('mousemove', onMove);
    document.addEventListener('mouseup', onUp);
    return () => {
      document.removeEventListener('mousemove', onMove);
      document.removeEventListener('mouseup', onUp);
    };
  }, [direction, size, onResize, min, max, storageKey]);

  const onDoubleClick = useCallback(() => {
    if (resetValue !== undefined) onResize(resetValue);
  }, [resetValue, onResize]);

  const isV = direction === 'vertical';
  return (
    <div
      className={`mr-resize-handle ${isV ? 'mr-resize-v' : 'mr-resize-h'}`}
      onMouseDown={onMouseDown}
      onDoubleClick={onDoubleClick}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      title="拖动调整 · 双击复位"
      style={{
        background: hover ? '#2563eb' : 'transparent',
      }}
    />
  );
}

/** 清理旧 localStorage 键（一次性） */
export function clearLegacyKeys(keys: string[]) {
  try {
    keys.forEach((k) => localStorage.removeItem(k));
  } catch {}
}

/** 从 localStorage 读取尺寸 */
export function loadSize(key: string, fallback: number): number {
  try {
    const v = localStorage.getItem(key);
    if (v) return Number(v);
  } catch {}
  return fallback;
}

export default ResizeHandle;
