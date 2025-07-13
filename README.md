# pharmChart

## Project Purpose

`pharmChart` provides a desktop GUI to manage medication rounds using a Python interface built with PyQt6. A Three.js based frontend visualizes a 3D model of the medicine cart and is served via a small Node/Express server. Data is stored in a local SQLite database defined in `carrello.sql`.

## Prerequisites

- **Python**: version 3.10 or later. Install dependencies such as `PyQt6` via `pip install PyQt6`.
- **Node.js**: version 18+ (the Dockerfile uses Node 20). Run `npm install` in the project directory to fetch required packages.

## Building the Frontend

Compile the Three.js frontend and place the output in `public/`:

```bash
npm run build
```

The server can then be started with:

```bash
npm start
```

which serves the bundled files on [http://localhost:3000](http://localhost:3000).

## Running the GUI

With the Node server running, launch the PyQt6 application:

```bash
python main.py
```

The GUI embeds the web frontend through `QWebEngineView` and connects to the local SQLite database. The first launch initializes the database if needed.

## Optional Docker Usage

A `Dockerfile` and `docker-compose.yml` are provided. To build and run the Node server using Docker:

```bash
docker-compose up
```

This performs `npm run build` inside the container and exposes port `3000` on the host. You can still run `python main.py` locally to access the web component served by Docker.


## Cart Edge Services

A sample edge stack using Mosquitto and two lightweight Python services is under `opt/cart-edge/`.

```
opt/cart-edge/
├── docker-compose.yml
├── .env
├── mosquitto/
│   ├── mosquitto.conf
│   ├── bridge.conf
│   └── pwfile
├── consumer/
│   ├── Dockerfile
│   └── cart_event_consumer.py
├── sync/
│   ├── Dockerfile
│   └── cart_sync_service.py
├── db/
│   └── cart.db
└── schema.sql
```

`create_db.py` in the same directory initializes `db/cart.db` based on `schema.sql`.
