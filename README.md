<picture>
  <source media="(prefers-color-scheme: dark)" srcset="public/icons/logo_full_dark.png">
  <source media="(prefers-color-scheme: light)" srcset="public/icons/logo_full.png">
  <img alt="Fallback image description" src="public/icons/logo_full.png">
</picture>

Foxtales is an ebook reader, written as a Progressive Web App.

## Current features

The project is in a very(!) early state and is not considered to be usable already. However, the following features
are prepared and considered during the development:

* Offline reading of selected books
* Ebook-Reader friendly
* Mobile friendly
* Installable Web-App
* Easy to self-host
* Sync of reading progress across devices
* Multiple users
* Support Calibre library format

## Supported file formats

* PDF
* EPUB
* CBZ
* MOBI
* KF8 (AZW3)
* FB2

## Technical stuff

The frontend is written in VueJS, using foliate-js to display the ebooks. 

The backend is written in Python, using FastAPI and calibredb to communicate with the shipped Calibre instance.

The Docker container is tested on a Raspberry Pi. 

## Roadmap and planned features

| Feature                                | Status   |
|----------------------------------------|----------|
| Provide Docker container               | Done     |
| Implement pagination for big libraries | Planned  |
| Sync reading progress                  | Prepared |
| Multi-User                             | Prepared |
| Implement search features              | Planned  |
| Browse books by tags                   | Planned  |
| Wishlist books                         | Planned  |
| Add book discovery                     | Planned  |
| Online Demo                            | Planned  |
| Annotations                            | Planned  |

## Contributions
* Based on https://github.com/jinhuan138/vue-book-reader
* Using https://github.com/johnfactotum/foliate-js
* Icons from www.svgrepo.com
