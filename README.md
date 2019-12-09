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
    all_files --> lista de todos los archivos publicados hasta el momento (esta lista
      está particionada en varias listas por cuestiones de optimización en la replicación)

En particular, para la DHT tomamos como guía [este paper](http://pdos.csail.mit.edu/papers/chord:sigcomm01/chord_sigcomm.pdf) para realizar una implementación de Chord , dado que esta permite realizar consultas eficientemente y garantiza que la información esté replicada y no exista un punto de falla única. Para lograr la comunicación entre los nodos en Chord usamos la biblioteca Pyro4.

`$>python dht.py`  - crear una topología inicial de 3 nodos Chord e insertar información básica necesaria para el funcionamiento de la aplicación.  
`$>python CreateNode.py` -  generar un nodo Chord de forma automática y añadirlo a la red existente.

Para el autodescubrimiento de los nodos en la red usamos multicast, donde los nodos Chord están anunciando su IP y puerto a la dirección multicast 239.255.4.3:1234 y los nodos Chord que quieran unirse a la red se subscriben a esta dirección para descubrir a los nodos Chord existentes.

* Comunicación entre Cliente y Tracker

Para el Cliente es transparente la existencia de una DHT como Tracker. La clase Cliente contiene en su interior una instancia de una clase Comunicator sirviendo de middleware entre dicho cliente y la DHT. El Comunicator se va a encargar de realizar a la DHT todas las consultas que necesite el Cliente y proveerle los resultados, pues es el que conoce cómo se van a guardar y setear las llaves. Al crearse cada cliente es necesario instanciar su Comunicator con el ip y puerto de algún nodo Chord, esta dirección es obtenida al subscribirse el cliente a la dirección multicast, para descubrir los nodos Chord que se están anunciando en todo momento. Las consultas del Comunicator a la DHT se realizan con Pyro4.

* Cliente

Todo cliente será identificado con un id numérico, asignado por el tracker la primera vez que ejecuta la aplicación. Como el cliente puede conectarse al tracker por direcciones distintas en dependencia de la interfaz que esté usando, el tracker conoce para cada id de un cliente la dirección actual por donde está escuchando peticiones de otros clientes. Este id se actualiza cada vez que el cliente acceda al sitio y es persistido en una carpeta nombrada Storage que tendrá cada cliente para almacenar los archivos publicados y descargados y también los .torrents de cada uno de ellos. Los clientes al iniciarse tienen una dirección por donde van a estar escuchando peticiones en otro hilo de ejecución, esta dirección está dada por un ip local asignado automáticamente y un puerto libre dentro del rango (7000-7999).

  --Flujo de la descarga:

  Si un cliente desea realizar la descarga de un archivo, esta es encapsulada en una clase Download, donde se particiona el archivo en pieces y se le asigna a cada piece el nodo cliente(attendant) del cual será descargado. Cada piece tiene los siguientes atributos: id, offset, size, attendant. Las descargas y envíos de pieces entre clientes son manejadas a través de transacciones de tipo "dwn" y "send" respectivamente, las cuales tienes un file descriptors de lectura y otro de escritura en dependencia de su tipo.
  Cuando un cliente `A` va a descargar un piece de `B` ocurre lo siguiente:

  - `A` crea una transacción de tipo "dwn" cuyo fd de lectura es el socket por el cual se está conectando a `B` y su fd de escritura es el fichero donde va a guardar la descarga del piece
  - `B` crea una transacción de tipo "send" cuyo fd de lectura es el archivo del cual se comenzará a enviar el piece y su fd de escritura es el socket que retornó el accept que le hace `B` a `A` cuando `A` se conecta

  Notar que cada piece es descargado(enviado) por medio de una transacción, pero estas no son creadas de una vez por todas al crear la descarga, pues inicialmente comienzan a ejecutarse las primeras k transacciones y en el momento en que finalice la transacción encargada del piece i se crea la transacción correspondiente al piece con id = i + k .

  La concurrencia entre descargas se simula a través de select, función que se mantiene esperando hasta que uno o más fd estén listos para algún tipo de I/O. La entrada al select son los fd tanto de lectura como de escritura de aquellas transacciones que estén pendientes, o sea, que no han fallado ni han finalizado. Cuando estos fd estén listos, ya sea para leer o escribir se atiende en correspondencia con el tipo de transacción de la cual él forma parte. Utilizar select nos permite conocer y controlar en todo momento el flujo de la descarga, tanto en el lado del cliente que envía como en el que está descargando, logrando incluso reiniciar la descarga de un piece fallido o detectar errores de timeout en los sockets.

* Aplicación gráfica

Se provee una aplicación para interactuar con el sistema la cual desarrollamos usando django como framework. Cuenta con las siguientes funcionalidades:

1. Listar archivos disponibles: Muestra todos los archivos que han sido publicados para los cuales se brinda la opción de descargar solo el .torrent asociado o el archivo.
2. Descargas realizadas: Permite ver un historial de las descargas realizadas desde que se entró por última vez a la aplicación así como pausar, reanudar o cancelar las descargas que estén en curso, reintentar las descargas fallidas y acceder desde el navegador a los archivos que fueron descargados con éxito.
3. Listar archivos descargados y publicados: Muestra tanto los archivos que se han publicado o los que se han descargado exitosamente que también son publicados y se pueden abrir dichos archivos desde el navegador. 
4. Publicar archivos: Se ofrece una ventana en la que se puede seleccionar el archivo que se desea publicar y automáticamente se crea el .torrent correspondiente

Para ejecutar la aplicación es necesario usar el comando en "./untitled":

`$>python manage.py runserver [ip:port]`