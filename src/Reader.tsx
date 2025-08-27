import React, {useEffect, useRef, useState} from 'react'
import {ReactReader} from 'react-reader'
import type {NavItem, Rendition} from 'epubjs'
import {loadFromIndexedDB} from "./dbaccess";


interface IProps {
    bookId: string
}


function getNavButton() {
    // @ts-ignore
    return document.getElementById("root").firstChild.firstChild.firstChild.firstChild.getElementsByTagName("button")[0]
}

function getBackButton() {
    // @ts-ignore
    return document.getElementById("root").firstChild.firstChild.firstChild.firstChild.getElementsByTagName("button")[1]
}

function getNextButton() {
    // @ts-ignore
    return document.getElementById("root").firstChild.firstChild.firstChild.firstChild.getElementsByTagName("button")[2]
}


function nextPage() {
    getNextButton().click()
}

function previousPage() {
    getBackButton().click()
}


export const Reader = (props: IProps) => {
    const [page, setPage] = useState('')
    const [chapter, setChapter] = useState('')
    const [bookData, setBookData] = useState("")
    const [location, setLocation] = useState<string | number>(0)
    const rendition = useRef<Rendition | undefined>(undefined)
    const toc = useRef<NavItem[]>([])
    useEffect(() => {
        async function loadBook() {
            // @ts-ignore
            const bd = await loadFromIndexedDB("books", props.bookId)
            // @ts-ignore
            setBookData(bd.data)
        }

        if (!bookData) {
            loadBook()
        }
    })
    console.log(location)
    return (
        <div style={{position: "relative", height: '100vh', display: 'flex', flexDirection: "column"}}>
            <div style={{width: "100vw", height: "100%"}}>
                <ReactReader
                    url={bookData}
                    location={location}
                    epubInitOptions={{encoding: "base64"}}
                    tocChanged={(_toc) => (toc.current = _toc)}
                    locationChanged={(loc: string) => {
                        setLocation(loc)
                        if (rendition.current && toc.current) {
                            const {displayed, href} = rendition.current.location.start
                            const chapter_ = toc.current.find((item) => item.href.startsWith(href))
                            console.log(chapter_, toc.current, href)
                            setPage(
                                `${displayed.page} of ${displayed.total}`
                            )
                            setChapter(chapter_?.label || "")
                        }
                    }}
                    getRendition={(_rendition: Rendition) => {
                        rendition.current = _rendition
                    }}
                />
            </div>
            <div style={{
                display: "grid", gridTemplateColumns: "1fr 1fr", padding: "5px 10px",
                color: "#0009",
                position: "absolute",
                bottom: 0,
                left: 0,
                zIndex: 1,
                boxSizing: "border-box",
                width: "100vw"
            }}>
                <div style={{
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    whiteSpace: "nowrap",
                }}>{chapter}</div>
                <div style={{textAlign: "right"}}>{page}</div>
            </div>
            <div style={{zIndex: 99, position: "absolute", top: 0, left: 0, width: "100%", height: "100%", display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gridTemplateRows: "1fr 1fr 1fr"}}>
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