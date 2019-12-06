# D&D BitTorrent
## Dalianys Pérez Perera  ,  Dayany Alfaro González
### Sistemas Distribuidos, 4to año, Ciencias de la Computación, Universidad de La Habana

BitTorrent es un protocolo diseñado para el intercambio de archivos punto a punto (peer-to-peer) en Internet.

Son requeridos dos elementos: *Cliente* y *Tracker*

#### Cliente
Un cliente es un nodo de la red que sirve y descarga archivos. Un archivo en descarga o descargado debe estar disponible para el resto de los clientes.

#### Tracker
Un tracker es el elemento en el sistema que mantiene actualizado qué clientes poseen qué archivo. La información se publica y descarga a través de archivos torrent. Esto quiere decir que si un cliente quiere servir determinado archivo debe crear un archivo torrent que así lo declare y publicarlo en el tracker.  

#### Propuesta de Solución

* Tracker

Es 