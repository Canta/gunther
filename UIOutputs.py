# -*- coding: utf-8 -*-

from PyQt4 import QtCore, QtGui, uic
import random
import threading
import time
import sys
import urllib
import GuntherLib
import os
import ui_rc

class Broadcast(QtGui.QGroupBox):
    def setupUi(self, o = None, handler = None):
        uic.loadUi("ui/broadcast.ui", self)
        self.LOutput = o #persiste el output de LiquidSoap
        self.LHandler = handler #referencia al handler del parent
        
        if (o != None):
            try:
                nombre = self.LOutput.GetNombre()
            except:
                nombre = "Broadcast" + str(random.randint(100,999))
        self.setObjectName(nombre)
        self.setWindowTitle(nombre)
        self.setTitle(nombre)
        self.LabelURL.setText(self.LOutput.GetURL() + self.LOutput.GetMountpoint())
        
        self.metadataUpdater = QtCore.QTimer()
        
        QtCore.QObject.connect(self.metadataUpdater, QtCore.SIGNAL("timeout()"), self.UpdateMetadata)
        #QtCore.QObject.connect(self.LInput, QtCore.SIGNAL("updateStatus(PyQt_PyObject)"), self.updateStatus)
        QtCore.QMetaObject.connectSlotsByName(self)
        
        self.metadataUpdater.start(5000)
        self.LOutput.exit(0)
        self.LOutput.start()
    
    def UpdateMetadata(self):
        self.LabelStatus.setText("STATUS: CHEQUEANDO...")
        self.LabelStatus.setStyleSheet("color:#0000FF;font-family:Jura;")
        met = self.ParseMetadata()
        if (len(met) == 0):
            self.LabelStatus.setText("STATUS: OFFLINE")
            self.LabelStatus.setStyleSheet("color:#FF0000;font-family:Jura;")
        else:
            self.LabelStatus.setText("STATUS: ONLINE")
            self.LabelStatus.setStyleSheet("color:#00FF00;font-family:Jura;")
            self.TableInformacion.clear()
            titulos = QtCore.QStringList()
            titulos.append(QtCore.QString("Nombre"))
            titulos.append(QtCore.QString("Valor"))
            self.TableInformacion.setHorizontalHeaderLabels(titulos)
            c = 0
            for m in met:
                if len(m) > 1:
                    nombre = QtGui.QTableWidgetItem(QtCore.QString(m[0]),0)
                    nombre.setToolTip(m[0])
                    valor = QtGui.QTableWidgetItem(QtCore.QString(m[1]),0)
                    valor.setToolTip(m[1])
                    self.TableInformacion.setItem(c,0,nombre)
                    self.TableInformacion.setItem(c,1,valor)
                    c = c + 1


    def ParseMetadata(self):
        #Necesito ubicar, de acuerdo al tipo de server, los datos de la transmisión actual
        meta = self.LOutput.GetMetadata()
        mount = str(self.LOutput.GetMountpoint())
        ret = []
        if "icecast" in meta.lower():
            ret = GuntherLib.ParseIcecastMetadata(meta, mount)
        else:
            #print "no se encontró icecast en: " + meta
            pass
        
        return ret

class Archivo(QtGui.QGroupBox):
    def setupUi(self, o = None, handler = None):
        uic.loadUi("ui/archivo.ui", self)
        self.LOutput = o #persiste el output de LiquidSoap
        self.LHandler = handler #referencia al handler del parent
        
        if (o != None):
            try:
                nombre = self.LOutput.GetNombre()
            except:
                nombre = "Archivo" + str(random.randint(100,999))
        self.setObjectName(nombre)
        self.setWindowTitle(nombre)
        self.setTitle(nombre)
        
        self.TextFileName.setText(self.LOutput.GetFullPath())
        
        self.metadataUpdater = QtCore.QTimer()
        QtCore.QObject.connect(self.metadataUpdater, QtCore.SIGNAL("timeout()"), self.UpdateMetadata)
        QtCore.QMetaObject.connectSlotsByName(self)
        
        self.metadataUpdater.start(5000)
        self.LOutput.exit(0)
        self.LOutput.start()
    
    def UpdateMetadata(self):
        tamanio = 0
        archivo = self.LOutput.GetFullPath()
        if os.path.exists(archivo):
            try:
                tamanio = os.path.getsize(archivo)
            except:
                print "Error al obtener el tamaño del archivo \""+archivo+"\"."
                pass
            self.LabelBytesGrabados.setText(str(tamanio/1000) + " KB ")
        else:
            print "No existe el archivo: \""+archivo+"\"."

class Generico(QtGui.QGroupBox):
    def setupUi(self, o = None, handler = None):
        uic.loadUi("ui/generico.ui", self)
        self.LOutput = o #persiste el output de LiquidSoap
        self.LHandler = handler #referencia al handler del parent
        
        if (o != None):
            try:
                nombre = self.LOutput.GetNombre()
            except:
                nombre = "Generico" + str(random.randint(100,999))
        self.setObjectName(nombre)
        self.setWindowTitle(nombre)
        self.setTitle(nombre)
        
        self.metadataUpdater = QtCore.QTimer()
        QtCore.QObject.connect(self.metadataUpdater, QtCore.SIGNAL("timeout()"), self.UpdateMetadata)
        QtCore.QMetaObject.connectSlotsByName(self)
        
        self.metadataUpdater.start(5000)
        self.LOutput.exit(0)
        self.LOutput.start()
    
    def UpdateMetadata(self):
        pass
