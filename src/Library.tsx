import React, {useRef, useState} from 'react'
import {ReactReader} from 'react-reader'
import type {NavItem, Rendition} from 'epubjs'


export const Library = () => {
    function gotPhoto(element: any) {
        var file = element.target.files[0];
        var reader = new FileReader()
        reader.onload = function(base64) {
            localStorage["file"] = base64.target?.result;
        }
        reader.readAsDataURL(file);
    }
    // Saved to localstorage
    return (
        <div >
            <div >
                Library
            </div>
            <input type="file" accept="image/*;capture=camera" onChange={gotPhoto} />
            <div>
            <a href="/book">Book 1</a>
            </div>
        </div>
    )
}
export default Library