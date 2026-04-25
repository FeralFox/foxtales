export function computeInitialFetchCount(
  tile: any,
  container: any,
  minimum_books: number,
): number {
  if (!container || !tile) return minimum_books

  const containerWidth = container.clientWidth
  const containerHeight = document.getElementsByTagName('body')[0].clientHeight

  const style = window.getComputedStyle(tile)
  const marginX =
    parseFloat(style.marginLeft || '0') + parseFloat(style.marginRight || '0')
  const marginY =
    parseFloat(style.marginTop || '0') + parseFloat(style.marginBottom || '0')

  const tileWidth = Math.max(1, tile.offsetWidth + marginX)
  const tileHeight = Math.max(1, tile.offsetHeight + marginY)

  const cols = Math.max(1, Math.floor(containerWidth / tileWidth))
  const rows = Math.max(1, Math.floor(containerHeight / tileHeight))
  // one tile is used by the upload tile always visible
  const capacity = cols * rows - 1
  // keep a sensible lower bound to avoid fetching too few on tiny measurements
  console.log('Capacity to prefetch', cols, rows, capacity)
  return Math.max(minimum_books, capacity)
}

export function get_uuid(): string {
  return '10000000-1000-4000-8000-100000000000'.replace(/[018]/g, (c) =>
    (
      +c ^
      (crypto.getRandomValues(new Uint8Array(1))[0] & (15 >> (+c / 4)))
    ).toString(16),
  )
}

export function authHeaders(): HeadersInit {
  const token = localStorage.getItem('auth_token')
  if (token) {
    return { Authorization: `Bearer ${token}` }
  }
  // Return an empty Headers object to satisfy HeadersInit when no token is present
  return new Headers()
}

export async function fetchAsync(url: string, headers?: object) {
  const additional_headers = headers || {}
  const response = await fetch(url, {
    headers: authHeaders(),
    ...additional_headers,
  })
  if (response.status === 401) {
    window.location.hash = '#/login'
    throw 'Authorization error - forward to login page.'
  }
  return await response.json()
}

export async function postAsync(url: string, data: object) {
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
      ...authHeaders(),
    },
    body: JSON.stringify(data),
  })
  return await response.json()
}
