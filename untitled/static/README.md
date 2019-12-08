# D&D BitTorrent
## Dalianys Pérez Perera  ,  Dayany Alfaro González
### Sistemas Distribuidos, 4to año, Ciencias de la Computación, Universidad de La Habana

BitTorrent es un protocolo diseñado para el intercambio de archivos punto a punto (peer-to-peer) en Internet. Este proyecto propone una implementación en Python que simula el protocolo BitTorrent. 

Son requeridos dos elementos: *Cliente* y *Tracker*

#### Cliente
Un cliente es un nodo de la red que sirve y descarga archivos. Un archivo descargado debe estar disponible para el resto de los clientes.

#### Tracker
Un tracker es el elemento en el sistema que mantiene actualizado qué clientes poseen qué archivo. La información se publica y descarga a través de archivos torrent. Esto quiere decir que si un cliente quiere servir determinado archivo debe crear un archivo torrent que así lo declare y publicarlo en el tracker.  

#### Propuesta de Solución

* Tracker
  
Las funcionalidades del Tracker las simulamos a través del empleo de una DHT(*Distributed Hash Table*), que va a guardar las siguientes informaciones:

        nombre del archivo --> lista de peers que están sirviendo el archivo
        nombre del archivo.torrent --> información que guarda el .torrent asociado al archivo
        all_files --> lista de todos los archivos publicados hasta el momento (esta lista en realidad
         está particionada en varias listas por cuestiones de optimización en la replicación)

En particular, para la DHT tomamos como guía [este paper](http://pdos.csail.mit.edu/papers/chord:sigcomm01/chord_sigcomm.pdf) para realizar una implementación de Chord , dado que esta permite realizar consultas eficientemente y garantiza que la información esté replicada y no exista un punto de falla única. Para lograr la comunicación entre los nodos en Chord usamos la biblioteca Pyro4.

`$>python dht.py`  - crear una topología inicial de 3 nodos Chord e insertar información básica necesaria para el funcionamiento de la aplicación.  
`$>python CreateNode.py` -  generar un nodo Chord de forma automática y añadirlo a la red existente.

Para el autodescubrimiento de los nodos en la red usamos multicast, donde los nodos Chord están anunciando su IP y puerto a la dirección multicast 239.255.4.3:1234 y los nodos Chord que quieran unirse a la red se subscriben a esta dirección para descubrir a los nodos Chord existentes.

* Comunicación entre Cliente y Tracker

Para el Cliente es transparente la existencia de una DHT como Tracker. La clase Cliente contiene en su interior una instancia de una clase Comunicator que es quien se encarga de hacer a la DHT todas las consultas que necesite el Cliente y proveerle los resultados. Las consultas del Comunicator a la DHT se realizan con Pyro4.

* Cliente
El Cliente va a tener un indentificador numérico con el cual se le consulta al Tracker cual es la dirección por la que va a estar escuchando. Por convención cada cliente va a tener en su almacenamiento una carpeta Storage donde se van a guardar todos archivos descargados y publicados y los respectivos .torrent.


* Aplicación gráfica

Se provee una aplicación para interactuar con el sistema la cual desarrollamos usando django como framework. Cuenta con las siguientes funcionalidades:

1. Listar archivos disponibles: Muestra todos los archivos que han sido publicados para los cuales se brinda la opción de descargar solo el .torrent asociado o el archivo.
2. Descargas realizadas: Permite ver un historial de las descargas realizadas desde que se entró por última vez a la aplicación así como pausar, reanudar o cancelar las descargas que estén en curso, reintentar las descargas fallidas y acceder desde el navegador a los archivos que fueron descargados con éxito.
3. Listar archivos descargados y publicados: Muestra tanto los archivos que se han publicado o los que se han descargado exitosamente que también son publicados y se pueden abrir dichos archivos desde el navegador. 
4. Publicar archivos: Se ofrece una ventana en la que se puede seleccionar el archivo que se desea publicar y automáticamente se crea el .torrent correspondiente

Para ejecutar la aplicación es necesario usar el comando:

`$>python manage.py runserver [ip] [port]`