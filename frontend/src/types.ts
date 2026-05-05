export interface UpdateItem {
  name: string
  current_version: string
  new_version: string
}

export interface CheckerStatus {
  type: string
  update_available: boolean
  updates: UpdateItem[]
  error: string | null
}
