export function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  const exponent = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1)
  const value = bytes / Math.pow(1024, exponent)
  return `${exponent === 0 ? value : value.toFixed(1)} ${units[exponent]}`
}

export function formatModality(modality: string): string {
  switch (modality) {
    case 'optical':
      return 'Optical'
    case 'sar':
      return 'SAR'
    case 'multispectral':
      return 'Multispectral'
    default:
      return 'Unknown modality'
  }
}

export function formatRole(role?: string): string | null {
  switch (role) {
    case 'temporal-before':
      return 'Temporal pair · before'
    case 'temporal-after':
      return 'Temporal pair · after'
    case 'optical-pair':
      return 'Optical + SAR pair · optical'
    case 'sar-pair':
      return 'Optical + SAR pair · SAR'
    default:
      return null
  }
}
