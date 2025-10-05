function deleteFromIndexedDB(storeName: string, tableName: string, identifier: string){
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
                var transaction   = database.transaction([tableName], 'readwrite');
                var objectStore   = transaction.objectStore(tableName);
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


function getValuesFromIndexedDB(storeName: string, tableName: string){
    return new Promise(
        function(resolve, reject) {
            var dbRequest = indexedDB.open(storeName);

            dbRequest.onerror = function(event: any) {
                reject(Error("Error text"));
            };

            dbRequest.onupgradeneeded = function(event: any) {
                // Objectstore does not exist. Nothing to load
                event.target.transaction.abort();
                reject(Error('Not found'));
            };

            dbRequest.onsuccess = function(event: any) {
                var database      = event.target.result;
                var transaction   = database.transaction([tableName]);
                var objectStore   = transaction.objectStore(tableName);
                var objectRequest = objectStore.getAll();

                objectRequest.onerror = function(event: any) {
                    reject(Error('Error text'));
                };

                objectRequest.onsuccess = function(event: any) {
                    if (objectRequest.result) resolve(objectRequest.result);
                    else reject(Error('object not found'));
                };
            };
        }
    );
}


function loadFromIndexedDB(storeName: string, tableName: string, id: string, defaultvalue?: any){
    id = id.toString()
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
                var transaction   = database.transaction([tableName]);
                var objectStore   = transaction.objectStore(tableName);
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


function saveToIndexedDB(storeName: string, tableName: string, object: any, id?: string){
    return new Promise(
        function(resolve, reject) {
            var dbRequest = indexedDB.open(storeName);

            dbRequest.onerror = function(event: any) {
                reject(Error("IndexedDB database error"));
            };

            dbRequest.onupgradeneeded = function(event: any) {
                var database    = event.target.result;
                var objectStore = database.createObjectStore(tableName)
            };

            dbRequest.onsuccess = function(event: any) {
                var database      = event.target.result;
                var transaction   = database.transaction([tableName], 'readwrite');
                var objectStore   = transaction.objectStore(tableName);
                var objectRequest = objectStore.put(object, (id || object.id).toString()); // Overwrite if exists


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


export {saveToIndexedDB, deleteFromIndexedDB, loadFromIndexedDB, getValuesFromIndexedDB}