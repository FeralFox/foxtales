import React, {useRef, useState} from 'react'
import {ReactReader} from 'react-reader'
import type {NavItem, Rendition} from 'epubjs'
import {saveToIndexedDB} from "./dbaccess";


export const Library = () => {
    function gotPhoto(element: any) {
        var file = element.target.files[0];
        var reader = new FileReader()
        reader.onload = async function (base64) {
            await saveToIndexedDB("books", {
                "id": "one",
                // @ts-ignore
                "data": base64.target?.result?.replace('data:application/epub+zip;base64,', '')})
        }
        reader.readAsDataURL(file);
    }

    function doFullscreen() {
        document.getElementsByTagName("body")[0].requestFullscreen()
    }

    // Saved to localstorage
    return (
        <div>
            <div>
                Library
            </div>
            <input type="file" accept="image/*;capture=camera" onChange={gotPhoto}/>
            <div>
                <a href="/book">Book 1</a>
                <button onClick={doFullscreen}>Fullscreen</button>
            </div>
        </div>
    )
}
export default Library