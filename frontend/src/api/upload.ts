import { apiClient } from './index'

export async function uploadRemoteSensingFile(
  file: File,
  onProgress?: (pct: number) => void,
) {
  return apiClient.uploadImage(file, onProgress)
}
