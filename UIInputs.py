# -*- coding: utf-8 -*-

from PyQt4 import QtCore, QtGui, uic
import random
import threading
import time
import sys
import ui_rc

class MetaBandeja(QtGui.QGroupBox):
    def updateStatus(self,arr):
        self.__dictStatus = arr
    
    def updateVUMetter(self):
        volume = self.prevVolume
        try:
            volume = float(self.__dictStatus["rms"])
        except:
            #print "error: " + str(self.__dictStatus["rms"])
            volume = self.prevVolume
        if (self.prevVolume == volume):
            volume = volume - 0.001
            if (volume < 0):
                volume = 0
        self.vumetter.setProperty("value", float(volume * 100))
        self.prevVolume = volume
    
    def updateRemaining(self):
        remaining = int(self.prevRemaining)
        try:
            if self.lastRemaining == 0 or self.lastRemaining - int(self.__dictStatus["remaining"].split(".")[0]) >= 60:
                remaining = int(self.__dictStatus["remaining"].split(".")[0])
                self.lastRemaining = remaining
            else:
                remaining = remaining - 1
        except:
            remaining = int(self.prevRemaining) - 1
        if remaining < 0:
            remaining = 0
        if remaining == 0:
            self.lastRemaining = 0
        self.lcdRemaining.display(remaining)
        self.prevRemaining = remaining
    
    def updateMetadata(self):
        interprete = self.prevInterprete
        tema = self.prevTema
        try:
            interprete = "Interprete: " + self.__dictStatus["artist"]
            tema = "Tema: " + self.__dictStatus["title"]
        except:
            interprete = self.prevInterprete
            tema = self.prevTema
        self.labelInterprete.setText(interprete)
        self.labelTema.setText(tema)
    
    def SetVolumen(self):
        #1) cambiar el volumen en Liquidsoap
        #2) mostrar el volumen en la bandeja
        self.labelVolumen.setText(str(self.volumen.value()) + "%")
    def comandoStop(self):
        self.LHandler.SendComando(self.LInput.GetNombre(True)+".stop")
        self.vumetter.setProperty("value", 0)
    def comandoPlay(self):
        self.LHandler.SendComando(self.LInput.GetNombre(True)+".play")
    def comandoEnable(self):
        self.LHandler.SendComando("mixer.select " + str(self.LInput.getIndex()) +" true")
    def comandoDisable(self):
        self.LHandler.SendComando("mixer.select " + str(self.LInput.getIndex()) +" false")
    def comandoToggled(self, prendido):
        if (prendido == True):
            self.comandoEnable()
        else:
            self.comandoDisable()
    def comandoVolumen(self,valor):
        #valor = self.volumen.getValue()
        self.LHandler.SendComando("mixer.volume " + str(self.LInput.getIndex()) +" " + str(valor))


class Bandeja(MetaBandeja):
    def setupUi(self, i = None, handler = None):
        uic.loadUi("ui/bandeja.ui", self)
        self.LInput = i #persiste el input de LiquidSoap
        self.LHandler = handler #referencia al handler del parent
        self.prevVolume = 0
        self.prevRemaining = 0
        self.lastRemaining = 0
        self.prevInterprete = ""
        self.prevTema = ""
        self.__dictStatus = {"volume": 0, "remaining":0, "artist": "", "title":""}
        
        if (i != None):
            try:
                nombre = self.LInput.GetNombre()
            except:
                nombre = "Bandeja" + str(random.randint(100,999))
        self.setObjectName(nombre)
        self.setWindowTitle(nombre)
        self.setTitle(nombre)
        
        self.vumetter.updater = QtCore.QTimer()
        self.metadataUpdater = QtCore.QTimer()
        self.lcdRemaining.updater = QtCore.QTimer()
        
        if (self.LInput.__class__.__name__ != "PlaylistEstatico"):
            #sólo si NO es un playlist estático
            QtCore.QObject.connect(self.buttonAgregarArchivos, QtCore.SIGNAL("clicked()"), self.SeleccionarArchivos)
            QtCore.QObject.connect(self.buttonQuitarArchivos, QtCore.SIGNAL("clicked()"), self.QuitarArchivo)
            QtCore.QObject.connect(self.botonPlay, QtCore.SIGNAL("clicked()"), self.Play)
            QtCore.QObject.connect(self.buttonStop, QtCore.SIGNAL("clicked()"), self.Stop)
            QtCore.QObject.connect(self.lista, QtCore.SIGNAL("itemDoubleClicked(QListWidgetItem *)"), self.PlayItem)
        
        QtCore.QObject.connect(self, QtCore.SIGNAL("toggled(bool)"), self.comandoToggled)
        QtCore.QObject.connect(self.volumen, QtCore.SIGNAL("valueChanged(int)"), self.SetVolumen)
        QtCore.QObject.connect(self.volumen, QtCore.SIGNAL("valueChanged(int)"), self.comandoVolumen)
        QtCore.QObject.connect(self.vumetter.updater, QtCore.SIGNAL("timeout()"), self.updateVUMetter)
        QtCore.QObject.connect(self.lcdRemaining.updater, QtCore.SIGNAL("timeout()"), self.updateRemaining)
        QtCore.QObject.connect(self.metadataUpdater, QtCore.SIGNAL("timeout()"), self.updateMetadata)
        QtCore.QObject.connect(self.LInput, QtCore.SIGNAL("updateStatus(PyQt_PyObject)"), self.updateStatus)
        QtCore.QMetaObject.connectSlotsByName(self)
        
        self.vumetter.updater.start(100)
        self.lcdRemaining.updater.start(1000)
        self.metadataUpdater.start(2000)
        self.LInput.exit(0)
        self.LInput.setIntervalStatus(random.randint(50,99))
        self.LInput.start()
    
    def SeleccionarArchivos(self):
        archivos = QtGui.QFileDialog.getOpenFileNames(None,"Elegí archivos para la lista:", ".","*.*")
        indice = self.lista.count() - 1
        for archivo in archivos:
            self.AgregarArchivo(archivo)
        self.UpdateCantidadArchivos()
        self.lista.setCurrentRow(indice +1)
        
    def AgregarArchivo(self, strArchivo):
        self.lista.insertItem(self.lista.count(), QtCore.QString(strArchivo))
        comando = QtCore.QString(self.LInput.GetNombre(True)+"-tracks.push " + unicode(self.lista.item(self.lista.count()-1).text()))
        if "win" in sys.platform:
            rid = self.__parseRID(self.LHandler.SendComando(comando.toAscii()))
        else:
            rid = self.__parseRID(self.LHandler.SendComando(comando.toUtf8()))
        self.lista.item(self.lista.count()-1).setStatusTip(str(rid)) #persisto el ID que le da liquidsoap
        #numero = self.lista.count() - 1
        #self.PlayItem(numero)
        
    
    def Stop(self):
        #borro todos los items de la lista
        i=0
        while i < self.lista.count():
            #acá tengo un error muy extraño con la concatenación normal
            #por alguna razón concatenaba el RID al principio.
            #lo arreglé así, ni me gasté en ponerme a leer qué pasó
            rid = self.lista.item(i).statusTip()
            if (rid == ""):
                rid = 0
            comando = []
            comando.append(str(self.LInput.GetNombre(True)))
            comando.append("-tracks.remove ")
            comando.append(str(int(rid)))
            ret = self.LHandler.SendComando(''.join(comando))
            i = i + 1
        comando = "mixer.skip " + str(self.LInput.getIndex()) 
        self.LHandler.SendComando(comando)
        ret = self.LHandler.SendComando("mixer.select " + str(self.LInput.getIndex()) + " false")
        #print ret
        
    def Play(self):
        #vuelvo a agregar los items a la lista.
        #pero a todos los que no sean el item seleccionado, les doy skip
        self.Stop()
        self.LHandler.SendComando("mixer.select " + str(self.LInput.getIndex()) + " true")
        i=0
        skipy = 0
        while i < self.lista.count():
            if i >= self.lista.currentRow():
                comando = QtCore.QString(self.LInput.GetNombre(True)+"-tracks.push " + unicode(self.lista.item(i).text()))
                if "win" in sys.platform:
                    rid = self.__parseRID(self.LHandler.SendComando(comando.toAscii()))
                else:
                    rid = self.__parseRID(self.LHandler.SendComando(comando.toUtf8()))
                self.lista.item(i).setStatusTip(str(rid)) #persisto el ID que le da liquidsoap
            i = i + 1
    
    def __parseRID(self, texto):
        #print "DEBUG: " + texto +"\n/DEBUG\n" 
        rid = texto.replace("\n","").replace("END","")
        try:
            tmp_rid = int(rid)
        except:
            #El RID no es un número. Error. 
            #En este caso, establezco un 0 para que no genere errores más tarde.
            rid = 0
        return rid
    
    def PlayItem(self, item):
        try:
            self.lista.setCurrentRow(item)
        except:
            pass
        self.Play()
    
    def QuitarArchivo(self):
        ret = self.LHandler.SendComando("mixer.skip " + str(self.LInput.getIndex()))
        ret = self.LHandler.SendComando(self.LInput.GetNombre(True)+"-tracks.remove "+self.lista.item(self.lista.currentRow()).statusTip())
        self.lista.takeItem(self.lista.currentRow())
        self.UpdateCantidadArchivos()
    
    def UpdateCantidadArchivos(self):
        self.labelCantidadArchivos.setText(str(self.lista.count()) + " archivos")

    def GetInput(self):
        return self.LInput
    
class BandejaFija(Bandeja):
    def setupUi(self, i = None, handler = None):
        super(BandejaFija,self).setupUi(i,handler)
        self.volumen.setGeometry(QtCore.QRect(0, 40, 31, 171))
        self.buttonAgregarArchivos.hide()
        self.buttonQuitarArchivos.hide()
        self.botonPlay.hide()
        self.buttonStop.hide()
        self.lista.setGeometry(QtCore.QRect(40, 40, 241, 201))
        aa = self.GetInput().GetArchivos()
        for a in aa:
            self.lista.insertItem(self.lista.count(), QtCore.QString(a))
        self.UpdateCantidadArchivos()

class Mic(MetaBandeja):
    def setupUi(self, i = None, handler = None):
        uic.loadUi("ui/mic.ui", self)
        self.LInput = i #persiste el input de LiquidSoap
        self.LHandler = handler #referencia al handler del parent
        self.__arrStatus = [0,"END"]
        self.prevVolume = 0.5
        self.__dictStatus = {"volume": 0}
        if (i != None):
            try:
                nombre = self.LInput.GetNombre()
            except:
                nombre = "Micrófono"
        
        self.setObjectName(nombre)
        self.setWindowTitle(nombre)
        self.setTitle(nombre)
        self.vumetter.updater = QtCore.QTimer()
        
        QtCore.QObject.connect(self.volumen, QtCore.SIGNAL("valueChanged(int)"), self.SetVolumen)
        QtCore.QObject.connect(self.volumen, QtCore.SIGNAL("valueChanged(int)"), self.comandoVolumen)
        QtCore.QObject.connect(self, QtCore.SIGNAL("toggled(bool)"), self.comandoToggled)
        QtCore.QObject.connect(self.vumetter.updater, QtCore.SIGNAL("timeout()"), self.updateVUMetter)
        QtCore.QObject.connect(self.LInput, QtCore.SIGNAL("updateStatus(PyQt_PyObject)"), self.updateStatus)
        QtCore.QMetaObject.connectSlotsByName(self)
        
        self.vumetter.updater.start(100)
        self.LInput.exit(0)
        self.LInput.setIntervalStatus(random.randint(80,250))
        self.LInput.start()
        
class Stream(MetaBandeja):
    def setupUi(self, i = None, handler = None):
        uic.loadUi("ui/mic.ui", self)
        self.LInput = i #persiste el input de LiquidSoap
        self.LHandler = handler #referencia al handler del parent
        self.__arrStatus = [0,"END"]
        self.prevVolume = 0.5
        self.__dictStatus = {"volume": 0}
        
        if (i != None):
            try:
                nombre = self.LInput.GetNombre()
            except:
                nombre = "Retransmisión" + str(random.randint(100,999))
        
        self.setObjectName(nombre)
        self.setWindowTitle(nombre)
        self.setTitle(nombre)
        self.vumetter.updater = QtCore.QTimer()
        
        QtCore.QObject.connect(self.volumen, QtCore.SIGNAL("valueChanged(int)"), self.SetVolumen)
        QtCore.QObject.connect(self.volumen, QtCore.SIGNAL("valueChanged(int)"), self.comandoVolumen)
        QtCore.QObject.connect(self, QtCore.SIGNAL("toggled(bool)"), self.comandoToggled)
        QtCore.QObject.connect(self.vumetter.updater, QtCore.SIGNAL("timeout()"), self.updateVUMetter)
        QtCore.QObject.connect(self.LInput, QtCore.SIGNAL("updateStatus(PyQt_PyObject)"), self.updateStatus)
        QtCore.QMetaObject.connectSlotsByName(self)
        
        self.vumetter.updater.start(100)
        self.LInput.exit(0)
        self.LInput.setIntervalStatus(random.randint(50,99))
        self.LInput.start()
