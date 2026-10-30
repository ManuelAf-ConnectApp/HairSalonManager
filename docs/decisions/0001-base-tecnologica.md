# ADR 0001 — Base local y autenticación del incremento inicial

**Estado:** aceptada (supuesto técnico reversible) · **Fecha:** 2026-10-29

Se usa SQLite local con claves foráneas y WAL, ubicado en el directorio de datos del usuario. Es suficiente para un único gestor offline y no introduce un servidor que el MVP no necesita. El acceso a datos está encapsulado en `infrastructure.database`; un adaptador posterior podrá sustituirlo.

Las contraseñas se derivan con `hashlib.scrypt` (N=16384, r=8, p=1, sal aleatoria de 128 bits), disponible en Python estándar. Es una alternativa de memoria dura mientras se decide si se incorpora Argon2id como dependencia de distribución. No se guardan contraseñas ni códigos de recuperación. Los códigos tienen 160 bits de entropía, se muestran una única vez y se invalidan tras su uso.

La titularidad fiscal y la licencia de distribución siguen pendientes; no se infiere que el gestor sea el emisor fiscal definitivo. El alcance SIF/VERI*FACTU se ha resuelto posteriormente en la ADR 0002: esta distribución solo compone borradores y no implementa facturación real.
