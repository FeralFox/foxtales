import React, {useRef, useState} from 'react'
import {ReactReader} from 'react-reader'
import type {NavItem, Rendition} from 'epubjs'


interface IProps {
    file: string
}


export const Reader = (props: IProps) => {
    const [page, setPage] = useState('')
    const [chapter, setChapter] = useState('')
    const [location, setLocation] = useState<string | number>(0)
    const rendition = useRef<Rendition | undefined>(undefined)
    const toc = useRef<NavItem[]>([])
    return (
        <div style={{height: '100vh', display: 'flex', flexDirection: "column"}}>
            <div style={{width: "100vw", height: "100%"}}>
                <ReactReader
                    url={localStorage[props.file].replace('data:application/epub+zip;base64,', '')}
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
            <div style={{display: "grid", gridTemplateColumns: "1fr 1fr", padding: "5px"}}>
                <div>{chapter}</div>
                <div style={{textAlign: "right"}}>{page}</div>
            </div>
        </div>
    )
}
export default Reader