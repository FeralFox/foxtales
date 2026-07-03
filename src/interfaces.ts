export interface BookMeta {
  title: string
  uuid: string
  author_sort: string
  authors: string
  cover: string
  cover_url: string
  formats: string[]
  id: number
  identifiers: Map<string, string>
  languages: string[]
  last_modified: string
  description: string
  pubdate: string
  series_index: number
  size: number
  tags: string[]
  timestamp: string
  fxtl_owner: string
  fxtl_progress: number
  fxtl_progress_update: string
  fxtl_status: string[]
}

export interface SearchedBook {
  uuid: string
  title: string
  pubdate: string
  cover_url: string
  description: string
  authors: string
  identifiers: Map<string, string>
}
