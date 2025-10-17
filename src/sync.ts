import {loadFromBookDb, saveToBookDb} from "./dbaccess";
import {authHeaders, URL} from "./constants";


export async function syncDbUpdates() {
    const current_updates = await loadFromBookDb("db_updates", "update-progress", {})
    for (let book_id of Object.keys(current_updates)) {
        const progress = current_updates[book_id]
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
    }
    await saveToBookDb("db_updates", {}, `update-progress`)
}