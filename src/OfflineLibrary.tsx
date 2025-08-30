import React, {useEffect, useRef, useState} from 'react'
import {ReactReader} from 'react-reader'
import type {NavItem, Rendition} from 'epubjs'
import {getValuesFromIndexedDB, loadFromIndexedDB, saveToIndexedDB} from "./dbaccess";


export const OfflineLibrary = () => {
    const [offlineBooks, setOfflineBooks] = useState([])
    let initialized = false

    async function loadOfflineBooks() {
        try {
            const bks = await getValuesFromIndexedDB("books", "books")
            console.log(bks)
            // @ts-ignore
            bks.sort((a,b) => b.data.progress.lastUpdated - a.data.progress.lastUpdated);
            // @ts-ignore
            setOfflineBooks(bks)
        } catch (e) {
            window.location.href = "/library"
        }
    }

    useEffect(() => {
        if (!initialized) {
            initialized = true;
            loadOfflineBooks();
        }
    }, [])

    // @ts-ignore
    const l = [offlineBooks.map(book => <div title={book.data.title} onClick={() => {window.location.href=`/book#id=${book.data.identifier}`}} key={book.data.identifier} style={{cursor: "pointer"}}>
        <div style={
            {
                padding: "5px",
                margin: "1rem",
                fontWeight: "bold",
                whiteSpace: "nowrap",
                textOverflow: "ellipsis",
                overflow: "hidden",
                width: "15em",
                height: "23em",
            }}>
            <div style={{
                // @ts-ignore
                backgroundImage: `url(data:image/png;base64,${book.cover})`,
                width: "100%",
                height: "calc(100% - 2rem)",
                border: "1px solid #000",
                borderRadius: "5px",
                marginBottom: "5px",
            }}></div>
            {
                    // @ts-ignore
                    book.data.title
            }
            </div>
    </div>)]
    // Saved to localstorage
    return (
        <div>
            <div>
                <a href={"/"}>Offline Library</a>
                <a href={"/library"}>Library</a>
            </div>
            <div>
                Offline Library
            </div>
            <div style={{display: "flex", flexWrap: "wrap"}}>
                {l}
            </div>
        </div>
    )
}
export default OfflineLibrary