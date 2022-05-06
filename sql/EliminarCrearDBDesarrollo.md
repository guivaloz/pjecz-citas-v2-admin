# Eliminar y crear base de datos para desarrollo

Lo mas practico es crear un archivo SQL en `~/.sql/eliminar-y-crear-pjecz-citas-v2.sql`

    DROP SCHEMA IF EXISTS public CASCADE;
    CREATE SCHEMA public;
    GRANT ALL ON SCHEMA public TO public;
    GRANT ALL ON SCHEMA public TO adminpjeczcitasv2;

Y agregar estos aliases a `~/.bashrc.d/61-postgresql.sql`

    alias eliminar-y-crear-pjecz-citas-v2="psql -f ~/.sql/eliminar-y-crear-pjecz-citas-v2.sql pjecz_citas_v2"
    echo "-- PostgreSQL eliminar tablas"
    echo "   eliminar-y-crear-pjecz-citas-v2"
    echo

Asi puede ejecutar con su usuario con cuenta en postgresql de altos privilegios

    eliminar-y-crear-pjecz-citas-v2
