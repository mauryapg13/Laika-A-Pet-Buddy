export default function PawPrint({ size = 40, className = '' }) {
  return (
    <svg width={size} height={size} viewBox="0 0 64 64" className={className} aria-hidden="true">
      <ellipse cx="32" cy="42" rx="14" ry="12" />
      <ellipse cx="14" cy="26" rx="6" ry="8" transform="rotate(-20 14 26)" />
      <ellipse cx="25" cy="15" rx="6" ry="8.5" transform="rotate(-6 25 15)" />
      <ellipse cx="39" cy="15" rx="6" ry="8.5" transform="rotate(6 39 15)" />
      <ellipse cx="50" cy="26" rx="6" ry="8" transform="rotate(20 50 26)" />
    </svg>
  )
}
