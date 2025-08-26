import React from 'react'
import {Route, Routes, BrowserRouter} from "react-router-dom";
import Reader from "./Reader";
import Library from "./Library";


export const App = () => {
    return (
        <BrowserRouter>
            <Routes>
                <Route path="/" element={<Library />} />
                <Route path="/book" element={<Reader file="file" />} />
            </Routes>
        </BrowserRouter>
    )
}
export default App