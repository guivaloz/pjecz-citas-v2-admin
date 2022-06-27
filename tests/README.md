# Tests

Ayuda del comando click

    citas --help

Ayuda del programa de migracion

    python tests/migracion_bd_v1.py --help

## Migracion en Diana

0) Verifique que este corriendo RQ para hacer tareas en el fondo

    screen -ls
    screen rq worker pjecz_citas_v2

1) Eliminar todos los datos de la base de datos

    citas db reiniciar

2) Agregue los servicios de la categoria COMUN a todos los distritos

    citas cit_oficinas_servicios asignar-todos-distritos COMUN
    tail -f cit_oficinas_servicios.log

3) Pruebe primero, ejecute luego, la migracion de clientes

    python tests/migracion_bd_v1.py --cli
    python tests/migracion_bd_v1.py --cli -x

4) Pruebe primero, ejecute luego, la migracion de citas

    python tests/migracion_bd_v1.py --cit
    python tests/migracion_bd_v1.py --cit -x

## Respaldar la base de datos en Diana

Ingrese y ejecute

    cd ~/Downloads/Minerva/pjecz_citas_v2/
    pg_dump -F t pjecz_citas_v2 > pjecz_citas_v2-2022-06-27-1558.tar
    gzip pjecz_citas_v2-2022-06-27-1558.tar

Copie el archivo tar.gz a su equipo, descomprima y restablezca

    gunzip pjecz_citas_v2-2022-06-27-1558.tar.gz
    pg_restore -F t -d pjecz_citas_v2 ~/Downloads/Minerva/pjecz_citas_v2/pjecz_citas_v2-2022-06-27-1558.tar
