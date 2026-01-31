const dbs = {
  books: {
    version: 5,
    upgrades: {
      0: function (database, storename, tablename) {},
      1: function (database, storename, tablename) {},
      2: function (database, storename, tablename) {
        database.createObjectStore('books')
      },
      3: function (database, storename, tablename) {
        database.createObjectStore('db_updates')
      },
      4: function (database, storename, tablename) {
        database.createObjectStore('annotations')
      },
    },
  },
  cover: {
    version: 1,
    upgrades: {
      0: function (database, storename, tablename) {
        database.createObjectStore('cover')
      },
    },
  },
  data: {
    version: 1,
    upgrades: {
      0: function (database, storename, tablename) {
        database.createObjectStore('data')
      },
    },
  },
}

const upgradeFn = (storeName: string, tableName: string) =>
  function (event: any) {
    console.log('Run upgrade', event.oldVersion, event.newVersion)
    const database = event.target!.result
    for (
      let version = event.oldVersion;
      version < event.newVersion;
      version++
    ) {
      console.log(`Upgrading version: ${version} for ${storeName}`)
      dbs[storeName].upgrades[version.toString()](
        database,
        storeName,
        tableName,
      )
    }
  }

function deleteFromIndexedDB(
  storeName: string,
  tableName: string,
  identifier: string,
) {
  return new Promise(function (resolve, reject) {
    var dbRequest = indexedDB.open(storeName, dbs[storeName].version)

    dbRequest.onerror = function (event) {
      reject(Error('IndexedDB database error'))
    }

    dbRequest.onupgradeneeded = upgradeFn(storeName, tableName)

    dbRequest.onsuccess = function (event: any) {
      // @ts-ignore
      var database = event.target.result
      var transaction = database.transaction([tableName], 'readwrite')
      var objectStore = transaction.objectStore(tableName)
      // @ts-ignore
      var objectRequest = objectStore.delete(identifier)

      objectRequest.onerror = function (event: any) {
        reject(
          Error(`Failed to delete ${storeName} / ${tableName} / ${identifier}`),
        )
      }

      objectRequest.onsuccess = function (event: any) {
        resolve('OK')
      }
    }
  })
}

function getValuesFromIndexedDB(storeName: string, tableName: string) {
  return new Promise(function (resolve, reject) {
    var dbRequest = indexedDB.open(storeName, dbs[storeName].version)

    dbRequest.onerror = function (event: any) {
      reject(Error('Error text'))
    }

    dbRequest.onupgradeneeded = upgradeFn(storeName, tableName)

    dbRequest.onsuccess = function (event: any) {
      var database = event.target.result
      var transaction = database.transaction([tableName])
      var objectStore = transaction.objectStore(tableName)
      var objectRequest = objectStore.getAll()

      objectRequest.onerror = function (event: any) {
        reject(Error('Error text'))
      }

      objectRequest.onsuccess = function (event: any) {
        if (objectRequest.result) resolve(objectRequest.result)
        else reject(Error('object not found'))
      }
    }
  })
}

function loadFromIndexedDB(
  storeName: string,
  tableName: string,
  id: string,
  defaultvalue?: any,
) {
  id = id.toString()
  return new Promise(function (resolve, reject) {
    var dbRequest = indexedDB.open(storeName, dbs[storeName].version)

    dbRequest.onerror = function (event: any) {
      reject(Error('Error text'))
    }

    dbRequest.onupgradeneeded = upgradeFn(storeName, tableName)

    dbRequest.onsuccess = function (event: any) {
      var database = event.target.result
      var transaction = database.transaction([tableName])
      var objectStore = transaction.objectStore(tableName)
      var objectRequest = objectStore.get(id)

      objectRequest.onerror = function (event: any) {
        if (defaultvalue) {
          return resolve(defaultvalue)
        } else {
          reject(Error('Error text'))
        }
      }

      objectRequest.onsuccess = function (event: any) {
        if (objectRequest.result) resolve(objectRequest.result)
        else if (defaultvalue !== undefined) {
          resolve(defaultvalue)
        } else reject(Error('object not found'))
      }
    }
  })
}

function getKeysFromIndexedDb(storeName: string, tableName: string) {
  return new Promise(function (resolve, reject) {
    var dbRequest = indexedDB.open(storeName, dbs[storeName].version)

    dbRequest.onerror = function (event: any) {
      reject(Error(event.message))
    }

    dbRequest.onupgradeneeded = upgradeFn(storeName, tableName)

    dbRequest.onsuccess = function (event: any) {
      var database = event.target.result
      var transaction = database.transaction([tableName])
      var objectStore = transaction.objectStore(tableName)
      var objectRequest = objectStore.getAllKeys()

      objectRequest.onerror = function (event: any) {
        reject(Error(event.message))
      }

      objectRequest.onsuccess = function (event: any) {
        if (objectRequest.result) resolve(objectRequest.result)
        else reject(Error('object not found'))
      }
    }
  })
}

function saveToIndexedDB(
  storeName: string,
  tableName: string,
  object: any,
  id?: string,
) {
  return new Promise(function (resolve, reject) {
    var dbRequest = indexedDB.open(storeName, dbs[storeName].version)

    dbRequest.onerror = function (event: any) {
      reject(event)
    }

    dbRequest.onupgradeneeded = upgradeFn(storeName, tableName)

    dbRequest.onsuccess = function (event: any) {
      var database = event.target.result
      var transaction = database.transaction([tableName], 'readwrite')
      var objectStore = transaction.objectStore(tableName)
      var objectRequest = objectStore.put(object, (id || object.id).toString()) // Overwrite if exists

      objectRequest.onerror = function (event: any) {
        reject(Error('Error text'))
      }

      objectRequest.onsuccess = function (event: any) {
        resolve('Data saved OK')
      }
    }
  })
}

function loadFromBookDb(
  tableName: string,
  id: string,
  defaultValue?: any,
): any {
  return loadFromIndexedDB('books', tableName, id, defaultValue)
}

function saveToBookDb(tableName: string, object: any, id?: string) {
  return new Promise(function (resolve, reject) {
    var dbRequest = indexedDB.open('books', dbs.books.version)

    dbRequest.onupgradeneeded = upgradeFn('books', tableName)

    dbRequest.onerror = function (event: any) {
      reject(event)
    }

    dbRequest.onsuccess = function (event: any) {
      var database = event.target.result
      var transaction = database.transaction([tableName], 'readwrite')
      var objectStore = transaction.objectStore(tableName)
      var objectRequest = objectStore.put(object, (id || object.id).toString()) // Overwrite if exists

      objectRequest.onerror = function (event: any) {
        reject(Error('Error text'))
      }

      objectRequest.onsuccess = function (event: any) {
        resolve('Data saved OK')
      }
    }
  })
}

export {
  getKeysFromIndexedDb,
  saveToIndexedDB,
  deleteFromIndexedDB,
  loadFromIndexedDB,
  getValuesFromIndexedDB,
  saveToBookDb,
  loadFromBookDb,
}
