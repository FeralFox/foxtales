export function computeInitialFetchCount(
  tile: any,
  container: any,
  minimum_books: number,
): number {
  if (!container || !tile) return minimum_books

  const containerWidth = container.clientWidth
  const containerHeight = container.clientHeight

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
  return Math.max(minimum_books, capacity)
}
