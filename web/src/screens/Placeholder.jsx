import Icon from '../components/Icon'

export default function Placeholder({ screen, date }) {
  return (
    <div className="placeholder">
      <div className="placeholder-icon"><Icon name={screen.icon} size={28} /></div>
      <h2>{screen.title}</h2>
      {date && (
        <span className="pill pill-ochre">
          {date.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })}
        </span>
      )}
      <p>{screen.blurb}</p>
      <span className="pill">Coming next</span>
    </div>
  )
}
