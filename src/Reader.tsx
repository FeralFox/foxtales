import { useState } from 'react';
import {
    Reader,
    ReaderContent,
    ReaderNext,
    ReaderPrevious,
    loadEPUB, loadComicBook
} from './react-ebook';


function EbookReader() {
    const [book, setBook] = useState(null);
    const [progress, setProgress] = useState(0);

    const handleFileChange = async (e: any) => {
        const file = e.target.files[0];
        if (file) {
            let loadedEbook;
            if (file.name.toLowerCase().endsWith(".epub")) {
                loadedEbook = await loadEPUB(file)
            } else if (file.name.toLowerCase().endsWith(".cbz")) {
                loadedEbook = await loadComicBook(file);
            };
            // @ts-ignore
            setBook(loadedEbook);
            setProgress(0)
        }
    };

    if (!book) {
        return (
            <div>
                <h2>Select an ebook to read</h2>
                <input type="file" accept=".epub,.pdf,.cbz" onChange={handleFileChange} />
            </div>
        );
    }

    const onProgressChange = (progress: number) => {
        setProgress(progress)
    }

    return (
        <Reader
            book={book}
            progress={progress}
            onProgressChange={onProgressChange}
        >
            <div style={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
                <div style={{ flex: 1, overflow: 'hidden' }}>
                    <ReaderContent
                        fontSize={16}
                        lineSpacing={1.5}
                        justify={true}
                        hyphenate={true}
                        flow="paginated"
                    />
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '1rem' }}>
                    <ReaderPrevious>Previous</ReaderPrevious>
                    <div>{Math.round(progress * 100)}%</div>
                    <ReaderNext>Next</ReaderNext>
                </div>
            </div>
        </Reader>
    );
}

export default EbookReader