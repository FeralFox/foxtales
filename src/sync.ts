import {loadFromBookDb, saveToBookDb} from "./dbaccess";
import {authHeaders, URL} from "./constants";


async function updateSingleDb(dbName: string) {
    const current_updates = await loadFromBookDb("db_updates", dbName, {})
    for (let book_id of Object.keys(current_updates)) {
        const progress = current_updates[book_id]
        try {
            const response = await fetch(`${URL}/set_book_metadata`,
                {
                    method: 'POST',
                    headers: {
                        'Accept': 'application/json',
                        'Content-Type': 'application/json',
                        ...authHeaders()
                    },
                    body: JSON.stringify({
                        book_id: book_id,
                        ...progress
                    })
                })
        } catch (e: any) {
            if (e.message === "Failed to fetch") {return}
            else {throw e}
        }
    }
    await saveToBookDb("db_updates", {}, dbName)
}

export async function syncDbUpdates() {
    await updateSingleDb("update-progress");
    await updateSingleDb("update-read-status");
}

export async function syncedUpdate(dbName: string, bookId: string, data: object) {
    const current_updates = await loadFromBookDb("db_updates", dbName, {})
    current_updates[bookId] = data
    await saveToBookDb("db_updates", current_updates, dbName)
    await syncDbUpdates()
}