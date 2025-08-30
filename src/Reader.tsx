import React, {useEffect, useRef, useState} from 'react'
import {ReactReader} from 'react-reader'
import type {NavItem, Rendition} from 'epubjs'
import {loadFromIndexedDB, saveToIndexedDB} from "./dbaccess";


export const Reader = () => {
    const [bookData, setBookData] = useState({})
    const [pageData, setPageData] = useState("")
    const [location, setLocation] = useState([-1, 0])
    useEffect(() => {
        const bookId = window.location.hash.substring(4)
        async function loadBook() {
            // @ts-ignore
            const bd = await loadFromIndexedDB("books", "books", bookId)
            // @ts-ignore
            setBookData(bd)
            // @ts-ignore
            setLocation([bd.data.progress.chapter, bd.data.progress.position])
        }

        if (Object.keys(bookData).length === 0) {
            loadBook()
        }
    }, [])

    useEffect(() => {
        async function loadPosition() {
            // @ts-ignore
            const first_page_id = bookData.data.chapters[location[0]].identifier
            // @ts-ignore
            const first_page = await loadFromIndexedDB(`book_${bookData.data.identifier}`, "data", first_page_id)
            // @ts-ignore
            setPageData(first_page.data)
            const newearr = {...bookData}
            // @ts-ignore
            newearr.data.progress = {chapter: location[0], position: location[1], lastUpdated: Math.floor(Date.now() / 1000)}
            setBookData(newearr)
            await saveToIndexedDB("books", "books", newearr)
        }
        if (location[0] != -1) {loadPosition()}
    }, [location])

    function nextPage() {
        // @ts-ignore
        if (location[0] === bookData.data.chapters.length - 1) {
            return
        }
        setLocation([location[0] + 1, 0])
    }

    function previousPage() {
        // @ts-ignore
        if (location[0] === 0) {return}
        // @ts-ignore
        setLocation([location[0] - 1, 0])
    }

    return (
        <div style={{position: "relative", height: '100vh', display: 'flex', flexDirection: "column"}}>
            <img src={`data:image/png;base64,${pageData}` || undefined}
                 style={{
                     width: "100%",
                     height: "100%",
                     objectFit: "contain"
                 }}/>

            <div style={{
                zIndex: 99,
                position: "absolute",
                top: 0,
                left: 0,
                width: "100%",
                height: "100%",
                display: "grid",
                gridTemplateColumns: "1fr 1fr 1fr",
                gridTemplateRows: "1fr 1fr 1fr"
            }}>
                <div onClick={nextPage}></div>
                <div></div>
                <div onClick={previousPage}></div>
                <div onClick={previousPage}></div>
                <div></div>
                <div onClick={nextPage}></div>
                <div onClick={previousPage}></div>
                <div></div>
                <div onClick={nextPage}></div>
            </div>
        </div>
    )
}
export default Reader