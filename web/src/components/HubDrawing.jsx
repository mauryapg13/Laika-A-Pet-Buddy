import { FUNCTIONS, SLOTS } from '../data'

// 3D line drawing of the hub. Depth comes from drawing each part twice:
// a lighter copy offset up-right (the back edge), then the front face
// filled with paper so it hides whatever is behind it.
const DX = 9
const DY = -7

const BODY =
  'M180 80 C245 80 268 115 268 170 C268 215 280 260 270 295 C260 328 225 340 180 340 ' +
  'C135 340 100 328 90 295 C80 260 92 215 92 170 C92 115 115 80 180 80Z'

function Ear({ cx, angle }) {
  const cy = 60
  return (
    <g transform={`rotate(${angle} ${cx} ${cy + 32})`}>
      <rect x={cx - 15 + DX} y={cy - 35 + DY} width="30" height="70" rx="15" className="ln-back" />
      <rect x={cx - 15} y={cy - 35} width="30" height="70" rx="15" className="ln" />
      <path d={`M${cx - 7} ${cy - 20} Q${cx} ${cy - 27} ${cx + 7} ${cy - 20}`} className="ln-thin" />
    </g>
  )
}

// Hanging attachment under the bottom nodes. Parked features show nothing:
// "off" means the strap is retracted, not harder to pull.
function Attachment({ x, y, fn }) {
  if (fn === 'food') {
    return (
      <g>
        <path d={`M${x - 8} ${y + 13} L${x + 8} ${y + 13} L${x + 5} ${y + 26} L${x - 5} ${y + 26}Z`} className="ln" />
        <circle cx={x} cy={y + 36} r="2.4" className="treat" />
        <circle cx={x + 1} cy={y + 46} r="2" className="treat" />
      </g>
    )
  }
  const end = y + 48
  return (
    <g>
      <rect x={x - 4} y={y + 10} width="8" height={end - y - 10} rx="2" className="ln strap" />
      {fn === 'play' ? (
        <rect x={x - 17} y={end - 1} width="34" height="11" rx="5.5" className="ln handle" />
      ) : (
        <circle cx={x} cy={end + 8} r="9" className="ln ring" />
      )}
    </g>
  )
}

function Node({ slot, config, selected, onSelect }) {
  const { id, x, y, side } = slot
  const fn = config.fn ? FUNCTIONS[config.fn] : null
  const off = config.availability === 'off'
  const puckClass = !fn ? 'puck-empty' : off ? 'puck-off' : `puck-${fn.tone}`
  const lineEnd = side === 'left' ? 70 : 290
  const lineStart = side === 'left' ? x - 15 : x + 15
  const textX = side === 'left' ? 64 : 296
  const anchor = side === 'left' ? 'end' : 'start'
  const isBottom = id === 'N4' || id === 'N5'

  return (
    <g className={`tap ${selected ? 'is-selected' : ''}`} onClick={() => onSelect(id)} role="button" aria-label={`Configure ${id}`}>
      <line x1={lineStart} y1={y} x2={lineEnd} y2={y} className="leader" />
      <circle cx={lineEnd} cy={y} r="1.8" className="leader-dot" />
      <text x={textX} y={y - 5} textAnchor={anchor} className="co-id">
        {id}{fn && off ? ' · off' : ''}
      </text>
      <text x={textX} y={y + 10} textAnchor={anchor} className={`co-fn ${!fn ? 'is-empty' : ''}`}>
        {fn ? fn.label : 'Empty'}
      </text>

      {isBottom && fn && !off && <Attachment x={x} y={y} fn={config.fn} />}

      {selected && <circle cx={x} cy={y} r="23" className="sel-ring" />}
      <circle cx={x + 3} cy={y - 2.5} r="15" className="ln-back" />
      <circle cx={x} cy={y} r="15" className={`ln ${puckClass}`} />
      {fn ? (
        <rect x={x - 5.5} y={y - 2} width="11" height="4" rx="2" className="slot" />
      ) : (
        <circle cx={x} cy={y} r="8.5" className="ln-thin" />
      )}
      {/* Larger invisible hit area for fingers */}
      <circle cx={x} cy={y} r="26" fill="transparent" />
    </g>
  )
}

// focus: dims everything except the selected node (used on the setup screen).
export default function HubDrawing({ nodes, selected, onSelect, focus = false }) {
  const pad = nodes.boop
  const padFn = pad.fn ? FUNCTIONS[pad.fn] : null
  const padOff = pad.availability === 'off'

  return (
    <svg viewBox="0 0 360 385" className={`hub ${focus ? 'is-focus' : ''}`} role="img" aria-label="Laika hub">
      <defs>
        <path id="body" d={BODY} />
      </defs>

      <Ear cx={138} angle={-18} />
      <Ear cx={222} angle={18} />

      <use href="#body" transform={`translate(${DX} ${DY})`} className="ln-back" />
      <use href="#body" className="ln" />
      {/* Shell parting line */}
      <use href="#body" transform="translate(180 212) scale(0.93) translate(-180 -212)" className="ln-thin dashed" />

      {/* Eyes and camera */}
      <rect x="157" y="120" width="8" height="17" rx="4" className="ink" />
      <rect x="195" y="120" width="8" height="17" rx="4" className="ink" />
      <circle cx="180" cy="104" r="3.2" className="ln-thin" />

      {/* Central boop pad */}
      <g className={`tap ${selected === 'boop' ? 'is-selected' : ''}`} onClick={() => onSelect('boop')} role="button" aria-label="Configure boop pad">
        {selected === 'boop' && <ellipse cx="180" cy="222" rx="68" ry="72" className="sel-ring" />}
        <ellipse cx="180" cy="222" rx="60" ry="64" className={`ln pad ${padOff || !padFn ? 'pad-off' : ''}`} />
        <ellipse cx="183" cy="219.5" rx="52" ry="56" className="ln-thin" />
        <text x="180" y="214" textAnchor="middle" className="pad-kicker">BOOP</text>
        <text x="180" y="234" textAnchor="middle" className="pad-label">
          {padFn ? padFn.label : 'Empty'}
        </text>
      </g>

      {SLOTS.map((slot) => (
        <Node
          key={slot.id}
          slot={slot}
          config={nodes[slot.id]}
          selected={selected === slot.id}
          onSelect={onSelect}
        />
      ))}
    </svg>
  )
}
