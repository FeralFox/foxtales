import React from 'react'
import {Route, Routes, BrowserRouter} from "react-router-dom";
import Reader from "./Reader";
import Library from "./Library";
import OfflineLibrary from "./OfflineLibrary";


export const App = () => {
    return (
        <BrowserRouter>
            <Routes>
                <Route path="/" element={<OfflineLibrary />} />
                <Route path="/library" element={<Library />} />
                <Route path="/book" element={<Reader />} />
            </Routes>
        </BrowserRouter>
    )
}
export default App