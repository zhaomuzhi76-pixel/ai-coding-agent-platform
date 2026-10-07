import React from 'react';
import type { ProviderCard as PC } from '../../types/model_registry';

interface Props {
  p: PC;
  onTest: (id: string) => void;
  onVerify: (id: string) => void;
  onSelect: (id: string) => void;
}

export const ProviderCard: React.FC<Props> = ({ p, onTest, onVerify, onSelect }) => (
  <div
    className={'mr-provider-card' + (p.enabled ? '' : ' disabled')}
    onClick={() => onSelect(p.id)}
    role="button"
    tabIndex={0}
    onKeyDown={(e) => e.key === 'Enter' && onSelect(p.id)}
  >
    <div className="mr-provider-header">
      <span className={'mr-dot ' + (p.connected ? 'ok' : 'err')} />
      <span className="mr-name">{p.name}</span>
      <span className={'mr-kind ' + p.kind}>{p.kind}</span>
    </div>
    <div className="mr-url">{p.base_url || 'no base_url'}</div>
    <div className="mr-meta">
      <span>models {p.model_count}</span>
      {p.has_key ? <span>key set</span> : <span className="mr-warn">no key</span>}
    </div>
    <div className="mr-actions">
      <button onClick={(e) => { e.stopPropagation(); onTest(p.id); }}>Test</button>
        <button onClick={(e) => { e.stopPropagation(); onVerify(p.id); }}
                title="测试并写入已验证，测试通过的模型会自动进入 ROLE ROUTING 下拉的【✅ 已验证】组"
                style={{ background: "rgba(79,214,154,.15)", color: "#4fd69a" }}>
          验证
        </button>
      <button onClick={(e) => { e.stopPropagation(); onSelect(p.id); }}>Detail</button>
    </div>
  </div>
);

export default ProviderCard;
