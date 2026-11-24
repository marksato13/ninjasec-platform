# Respaldos de PostgreSQL

Un contenedor propio que vuelca la base, la comprime, **verifica que el
volcado sirve** y borra los viejos. Arranca con el resto del stack de
producción.

Hasta ahora `./backups` era un punto de montaje declarado en el compose
**sin nada que escribiera dentro**.

## Qué hace, y cada cuánto

| | Por defecto | Variable |
| --- | --- | --- |
| Intervalo | 24 h | `RESPALDO_INTERVALO_HORAS` |
| Retención | 14 días | `RESPALDO_RETENCION_DIAS` |
| Destino | `./backups` del anfitrión | `RESPALDO_DESTINO` |

Hace uno **al arrancar**, además del ciclo. Si el contenedor se reinicia no
esperas 24 horas al primero, y si la configuración está mal te enteras ya.

## Las tres decisiones que hacen que esto sirva de algo

**1. La contraseña nunca va en la línea de comandos.** Va por `PGPASSWORD`,
porque los argumentos de un proceso se leen con `ps` desde cualquier otra
sesión del servidor.

**2. Cada respaldo se verifica.** Un `pg_dump` que falla a medias deja un
archivo que *parece* correcto: tiene tamaño y se abre. Se comprueban tres
cosas: que supera un tamaño mínimo, que el gzip está íntegro, y que el
volcado **termina con la marca de cierre que escribe PostgreSQL**. Esa
tercera es la que caza el truncado, que es el fallo que pasa desapercibido.

Mientras se escribe, el archivo lleva extensión `.parcial` y solo se
renombra al terminar y verificar. Si el proceso muere a mitad queda un
`.parcial` que se ignora, en vez de un `.sql.gz` roto que parece bueno.

**3. Si falla, no borra nada.** La limpieza de antiguos corre **solo después
de un respaldo nuevo verificado**. Así un fallo repetido nunca te deja sin
ninguno.

## Restaurar

Probado de extremo a extremo: original y restaurada quedaron idénticas en
tablas y filas.

```bash
# 1. Ver qué hay
ls -lh backups/

# 2. Crear una base nueva. NUNCA restaurar encima de la que está en uso
#    sin haber hecho antes un volcado de esa.
docker exec ninjasec-postgres psql -U "$POSTGRES_USER" \
  -c "CREATE DATABASE ninjasec_restaurada;"

# 3. Restaurar
gzip -dc backups/ninjasec-AAAAMMDD-HHMMSS.sql.gz | \
  docker exec -i ninjasec-postgres psql -U "$POSTGRES_USER" -d ninjasec_restaurada

# 4. Comprobar que llegó todo, antes de confiar en ello
docker exec ninjasec-postgres psql -U "$POSTGRES_USER" -d ninjasec_restaurada \
  -tAc "select 'tablas='||(select count(*) from information_schema.tables where table_schema='public')||'  usuarios='||(select count(*) from users);"
```

Compara ese conteo con el de la base original. Si no cuadra, **el respaldo
no sirve y hay que saberlo antes de necesitarlo**, no después.

## Comprobar que está funcionando

```bash
docker logs ninjasec-respaldos --tail 20
ls -lh backups/
```

Si no hay ningún `.sql.gz` de las últimas 24 horas, algo falla. Los `.parcial`
sueltos son respaldos abortados: se pueden borrar.

## 🔴 Lo que esto NO resuelve

**Los respaldos viven en el mismo servidor que la base.** Si ese disco
muere, o alguien borra la máquina, se van los dos juntos. Eso no es una
copia de seguridad: es una copia local.

Para que lo sea de verdad hace falta sacarlos fuera —a otro proveedor, a un
disco distinto, a donde sea que no sea esa máquina—. No está hecho, y es el
siguiente paso.

Es especialmente urgente si el despliegue va sobre una prueba gratuita: al
acabar los 90 días de Google Cloud, **los datos de Compute Engine se marcan
para borrado** y hay 30 días de gracia. Un respaldo dentro de esa misma
máquina desaparece con ella.
