#! /usr/bin/python
# -*- coding: utf-8 -*-

import git
import os
import sys, getopt

#chequeo si el directorio actual es un checkout del repo
repo = None
info = None
try:
    repo = git.Repo(".")
    info = repo.git.status("--porcelain")
except Exception as e:
    #g = git.cmd.Git(".")
    #g.clone("https://github.com/Canta/gunther", ".")
    #repo = git.Repo(".")
    #info = repo.git.status("--porcelain")
    print("Este directorio no está vinculado al repositorio de Günther.")
    print("Debe ejecutar nuevamente la instalación de Günther.")
    print("Imposible continuar.")
    exit(1);

#Borro cualquier cambio
repo.git.reset("--hard","HEAD")

#Actualizo la versión
repo.git.pull()

#Y ahora lanzo Günther
try:                                
    opts, args = getopt.getopt(sys.argv[1:], "hg:d", ["help", "debug"])
except getopt.GetoptError:
    print "opciones invalidas"
    sys.exit(2)
comando = "python ./gunther.py " #+ "".join(opts) + " " + "".join(args)
for opt, arg in opts:
    comando = comando + opt + " "
comando = comando + "".join(args)

os.system(comando)
