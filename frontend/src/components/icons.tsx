import type { SVGProps } from 'react'

type IconProps = SVGProps<SVGSVGElement>

const base = {
  width: 16,
  height: 16,
  viewBox: '0 0 16 16',
  fill: 'none',
  stroke: 'currentColor',
  strokeWidth: 1.6,
  strokeLinecap: 'round' as const,
  strokeLinejoin: 'round' as const,
}

export function CheckIcon(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="M3 8.5 6.2 12 13 4" />
    </svg>
  )
}

export function WarningIcon(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="M8 2.2 14.5 13.5H1.5L8 2.2Z" />
      <path d="M8 6.5v3.2" />
      <circle cx="8" cy="11.6" r="0.15" fill="currentColor" stroke="none" />
    </svg>
  )
}

export function ErrorIcon(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <circle cx="8" cy="8" r="6.2" />
      <path d="M5.8 5.8 10.2 10.2" />
      <path d="M10.2 5.8 5.8 10.2" />
    </svg>
  )
}

export function UploadIcon(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="M8 11V2.5" />
      <path d="M4.5 6 8 2.5 11.5 6" />
      <path d="M2.5 11v2a1 1 0 0 0 1 1h9a1 1 0 0 0 1-1v-2" />
    </svg>
  )
}

export function SatelliteIcon(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <rect x="6" y="6" width="4" height="4" rx="0.5" transform="rotate(45 8 8)" />
      <path d="M4.5 4.5 2.5 2.5" />
      <path d="M11.5 11.5 13.5 13.5" />
      <path d="M2.5 6 1 4.5" />
      <path d="M6 2.5 4.5 1" />
      <path d="M13.5 2.5 8 8" />
    </svg>
  )
}

export function LayersIcon(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="M8 2 14 5.5 8 9 2 5.5 8 2Z" />
      <path d="M2 8.5 8 12 14 8.5" />
      <path d="M2 11.5 8 15 14 11.5" />
    </svg>
  )
}

export function ImageIcon(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <rect x="2" y="3" width="12" height="10" rx="1" />
      <circle cx="5.5" cy="6.5" r="1" />
      <path d="M2 11 6 8l2.5 2L11 8l3 3" />
    </svg>
  )
}

export function TrashIcon(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="M3 4.5h10" />
      <path d="M5.5 4.5V3a1 1 0 0 1 1-1h3a1 1 0 0 1 1 1v1.5" />
      <path d="M4.5 4.5 5 13a1 1 0 0 0 1 1h4a1 1 0 0 0 1-1l.5-8.5" />
    </svg>
  )
}

export function ChevronDownIcon(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="M3.5 6 8 10.5 12.5 6" />
    </svg>
  )
}

export function SendIcon(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="M13.5 2.5 7 9" />
      <path d="M13.5 2.5 9.3 13.5 7 9 2.5 6.7 13.5 2.5Z" />
    </svg>
  )
}

export function SpinnerIcon(props: IconProps) {
  return (
    <svg {...base} viewBox="0 0 16 16" {...props} className={`animate-spin ${props.className ?? ''}`}>
      <path d="M8 2v2.4" />
      <path d="M8 11.6V14" opacity="0.3" />
      <path d="M13.3 8h-2.4" opacity="0.5" />
      <path d="M5.1 8H2.7" opacity="0.8" />
    </svg>
  )
}

export function ScanIcon(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="M2 5V3a1 1 0 0 1 1-1h2" />
      <path d="M11 2h2a1 1 0 0 1 1 1v2" />
      <path d="M14 11v2a1 1 0 0 1-1 1h-2" />
      <path d="M5 14H3a1 1 0 0 1-1-1v-2" />
      <circle cx="8" cy="8" r="2.4" />
    </svg>
  )
}

export function CompassIcon(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <circle cx="8" cy="8" r="6" />
      <path d="M10.2 5.8 8.9 8.9 5.8 10.2 7.1 7.1 10.2 5.8Z" />
    </svg>
  )
}

export function GridIcon(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <rect x="2" y="2" width="5" height="5" rx="0.5" />
      <rect x="9" y="2" width="5" height="5" rx="0.5" />
      <rect x="2" y="9" width="5" height="5" rx="0.5" />
      <rect x="9" y="9" width="5" height="5" rx="0.5" />
    </svg>
  )
}

export function SettingsIcon(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <circle cx="8" cy="8" r="2.5" />
      <path d="M8 1.5v1.2M8 13.3v1.2M1.5 8h1.2M13.3 8h1.2M3.4 3.4l.9.9M11.7 11.7l.9.9M3.4 12.6l.9-.9M11.7 4.3l.9-.9" />
    </svg>
  )
}

export function RefreshIcon(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="M14 2v4h-4" />
      <path d="M2 14v-4h4" />
      <path d="M3.51 6a6 6 0 0 1 9.4-1.28L14 6M2 10l1.09 1.28A6 6 0 0 0 12.49 10" />
    </svg>
  )
}

