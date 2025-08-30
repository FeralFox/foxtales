import React, {useEffect, useRef, useState} from 'react'
import {saveToIndexedDB} from "./dbaccess";


const URL="http://192.168.178.21"


async function fetchAsync (url: string) {
    let response = await fetch(url);
    return await response.json();
}


export const Library = () => {
    const [books, setBooks] = useState([])
    let initialized = false
    async function uploadFile(element: any) {
        var file = element.target.files[0];

        var formData = new FormData();
        formData.append('file', file);
        const response = await fetch(`${URL}:8000/add_book`, {
            method: 'POST',
            body: formData,
            // Headers are automatically set by browser for FormData
        });
        loadBooks()
    }

    async function downloadBook(identifier: string) {
        const fetchedBooks = await fetchAsync(`${URL}:8000/get_book_content?identifier=${identifier}`);
        const bookMetaData = await fetchAsync(`${URL}:8000/get_book?identifier=${identifier}`);
        const cover = await fetchAsync(`${URL}:8000/get_cover_b64?identifier=${identifier}`);
        await saveToIndexedDB(
            `books`,
            "books",
            {id: identifier,
             data: bookMetaData,
             cover: cover.cover}
        )
        
        await saveToIndexedDB(`book_${identifier}`, "data", {id: "cover", data: cover})
        for (let chapterId of Object.keys(fetchedBooks)) {
            const bookData = fetchedBooks[chapterId];
            await saveToIndexedDB(`book_${identifier}`, "data", {id: chapterId, data: bookData})
        }
    }
    async function loadBooks() {
        const fetchedBooks = await fetchAsync(`${URL}:8000/list_books`)
        console.log(fetchedBooks)
        setBooks(fetchedBooks)
    }

    useEffect(() => {
        if (!initialized) {
            initialized=true;
            loadBooks();
        }
    }, [])

    // @ts-ignore
    const k = books.map(book => <div key={book.identifier}><span>{book.title}<button onClick={() => downloadBook(book.identifier)}>Download</button></span></div>);
    // Saved to localstorage
    return (
        <div>
            <div>
                <a href={"/"}>Offline Library</a>
                <a href={"/library"}>Library</a>
            </div>
            <input type="file" accept="*" onChange={uploadFile}/>
            <div>
                {k}
                <br/>
            </div>
        </div>
    )
}
export default Library