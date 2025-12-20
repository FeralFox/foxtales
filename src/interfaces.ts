export interface BookMeta {
  id: string
  uuid: string
  title: string
  fxtl_is_read: boolean
}

export interface SearchedBook {
  id: string
  title: string
  subtitle: string
  pubdate: string
  cover_url: string
  description: string
  authors: string[]
  isbn: string
}
