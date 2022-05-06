# Respaldar base de datos en produccion

Pasos a seguir

1. Ingrese a Diana con `ssh pjecz-citas-v2@diana`
2. Cambiese al directorio `cd ~/Descargas/Minerva/pjecz_citas_v2`
3. Haga el respaldo `pg_dump -F t pjecz_citas_v2 > pjecz_citas_v2-2022-MM-DD-HHMM.tar`
4. Comprima el archivo TAR con `gzip pjecz_citas_v2-2022-MM-DD-HHMM.tar`
5. Copie a su equipo ese archivo tar.gz
6. Descomprima con `gunzip pjecz_citas_v2-2022-MM-DD-HHMM.tar.gz`
7. Para restablecer en su equipo local, elimine y ejecute pg_restore
