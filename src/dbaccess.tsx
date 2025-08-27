function deleteFromIndexedDB(storeName: string, identifier: string){
    return new Promise(
        function(resolve, reject) {
            var dbRequest = indexedDB.open(storeName);

            dbRequest.onerror = function(event) {
                reject(Error("IndexedDB database error"));
            };

            dbRequest.onupgradeneeded = function(event: any) {
                // @ts-ignore
                var database    = event.target.result;
                var objectStore = database.createObjectStore(storeName, {keyPath: "id"});
            };

            dbRequest.onsuccess = function(event: any) {
                // @ts-ignore
                var database      = event.target.result;
                var transaction   = database.transaction([storeName], 'readwrite');
                var objectStore   = transaction.objectStore(storeName);
                // @ts-ignore
                var objectRequest = objectStore.delete(identifier);

                objectRequest.onerror = function(event: any) {
                    reject(Error('Error text'));
                };

                objectRequest.onsuccess = function(event: any) {
                    resolve('Data saved OK');
                };
            };
        }
    );
}



function loadFromIndexedDB(storeName: string, id: string, defaultvalue?: any){
    return new Promise(
        function(resolve, reject) {
            var dbRequest = indexedDB.open(storeName);

            dbRequest.onerror = function(event: any) {
                reject(Error("Error text"));
            };

            dbRequest.onupgradeneeded = function(event: any) {
                // Objectstore does not exist. Nothing to load
                event.target.transaction.abort();
                if (defaultvalue) {
                    resolve(defaultvalue)
                }
                reject(Error('Not found'));
            };

            dbRequest.onsuccess = function(event: any) {
                var database      = event.target.result;
                var transaction   = database.transaction([storeName]);
                var objectStore   = transaction.objectStore(storeName);
                var objectRequest = objectStore.get(id);

                objectRequest.onerror = function(event: any) {
                    if (defaultvalue) {
                        return resolve(defaultvalue)
                    } else {
                        reject(Error('Error text'));
                    }
                };

                objectRequest.onsuccess = function(event: any) {
                    if (objectRequest.result) resolve(objectRequest.result);
                    else reject(Error('object not found'));
                };
            };
        }
    );
}


function saveToIndexedDB(storeName: string, object: any){
    return new Promise(
        function(resolve, reject) {
            if (object.id === undefined) reject(Error('object has no id.'));
            var dbRequest = indexedDB.open(storeName);

            dbRequest.onerror = function(event: any) {
                reject(Error("IndexedDB database error"));
            };

            dbRequest.onupgradeneeded = function(event: any) {
                var database    = event.target.result;
                var objectStore = database.createObjectStore(storeName, {keyPath: "id"});
            };

            dbRequest.onsuccess = function(event: any) {
                var database      = event.target.result;
                var transaction   = database.transaction([storeName], 'readwrite');
                var objectStore   = transaction.objectStore(storeName);
                var objectRequest = objectStore.put(object); // Overwrite if exists

                objectRequest.onerror = function(event: any) {
                    reject(Error('Error text'));
                };

                objectRequest.onsuccess = function(event: any) {
                    resolve('Data saved OK');
                };
            };
        }
    );
}


export {saveToIndexedDB, deleteFromIndexedDB, loadFromIndexedDB}