export const URL =
  import.meta.env.MODE === 'production' ? '' : 'http://localhost:8000'

export const ANNOTATION_CATEGORIES = {
  yellow: {
    color: '#c8c800',
    colorDarkMode: '#c8c800',
    displayName: 'Yellow',
  },
  green: {
    color: '#00c800',
    colorDarkMode: '#00c800',
    displayName: 'Green',
  },
  blue: {
    color: '#6666c8',
    colorDarkMode: '#6666c8',
    displayName: 'Blue',
  },
  red: {
    color: '#c80000',
    colorDarkMode: '#c80000',
    displayName: 'Red',
  },
}
