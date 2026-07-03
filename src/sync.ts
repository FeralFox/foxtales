import { loadFromBookDb, saveToBookDb } from './dbaccess'
import { URL } from './constants'
import { postAsync } from './lib'

async function updateSingleDb(dbName: string) {
  const current_updates = await loadFromBookDb('db_updates', dbName, {})
  for (let book_uuid of Object.keys(current_updates)) {
    const updateData = current_updates[book_uuid]
    try {
      const response = await postAsync(`${URL}/set_book_metadata`, {
        book_uuid: book_uuid,
        update_type: dbName,
        update_data: updateData,
      })
      await saveToBookDb('db_updates', {}, dbName)
    } catch (e: any) {
      if (e.message === 'Failed to fetch') {
        return
      } else {
        throw e
      }
    }
  }
}

export async function syncDbUpdates() {
  await updateSingleDb('update-progress')
  await updateSingleDb('update-read-status')
  await updateSingleDb('update-favorite-status')
  await updateSingleDb('update-annotations')
}

export async function syncedUpdate(
  dbName: string,
  bookId: string,
  data: object,
  append?: boolean,
) {
  const current_updates = await loadFromBookDb('db_updates', dbName, {})
  if (append) {
    try {
      current_updates[bookId].push(data)
    } catch (err) {
      current_updates[bookId] = [data]
    }
  } else {
    current_updates[bookId] = data
  }
  await saveToBookDb('db_updates', current_updates, dbName)
  await syncDbUpdates()
}
