#! /usr/bin/python
# -*- coding: utf-8 -*-

import git
import os
import sys, getopt

repo = git.Repo(".")
#chequeo si el directorio actual es un checkout del repo
info = None
try:
    info = repo.status("--porcelain")
except Exception as e:
    git.Repo.clone_from("https://github.com/Canta/gunther", ".")
    repo = git.Repo(".")
    info = repo.status("--porcelain")

#Borro cualquier cambio
svnclient.revert(".")

#Actualizo la versión
svnclient.update(".")

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
