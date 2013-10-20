#! /usr/bin/python
# -*- coding: utf-8 -*-

from PyQt4 import QtCore, QtGui, uic
import sys, getopt
import LiqHandler
from array import array
from struct import unpack, pack
import pyaudio
import wave
import os, time, datetime
import httplib, urllib, json
from urlparse import urlparse
from lxml import etree
import wizard
import UIInputs
import UIOutputs
import GuntherLib
import ui_rc

class GuntherWindow(QtGui.QMainWindow):
    def __init__(self, parent = None):
        super(GuntherWindow,self).__init__(parent)
        self.ui = uic.loadUi("ui/gunther.ui",self)
        self.inputs = []
        self.outputs = []
        self.__xml = None
        
        #cargo el HTML de "acerca de..."
        f = open("about.html", "r")
        aboutText = f.read()
        f.close()
        self.TextAbout.setHtml(QtCore.QString(aboutText))
        
    def loadInput(self, i):
        #acá convierto cada input en un objeto de la pantalla
        tipo = type(i).__name__
        if (tipo == "PlaylistEstatico"):
            self.tmp = UIInputs.BandejaFija()
        if (tipo == "Playlist"):
            self.tmp = UIInputs.Bandeja()
        if (tipo == "MicIn"):
            self.tmp = UIInputs.Mic()
        if (tipo == "Stream"):
            self.tmp = UIInputs.Stream()
        self.tmp.setupUi(i, self.handler)
        self.inputs.append(self.tmp)
        #si está conectado el handler, activo el input
        if (self.handler.isConnected() == True):
            self.handler.SendComando("mixer.select " + str(len(self.inputs) - 1 ) + " true")
            i.start()
        #acomodo la pantalla
        suma = 0
        for i2 in self.inputs:
            suma += i2.geometry().width() + 10
        
        self.contenidoInputs.resize(QtCore.QSize(suma, self.contenidoInputs.geometry().height()))
        self.tmp.setSizePolicy(QtGui.QSizePolicy.Ignored,QtGui.QSizePolicy.Ignored)
        self.LayoutInputs.addWidget(self.tmp)
    
    def loadOutput(self, o):
        #acá convierto cada output en un objeto de la pantalla
        tipo = type(o).__name__
        tmp = None
        if (tipo == "Broadcast"):
            tmp = UIOutputs.Broadcast()
        if (tipo == "Archivo"):
            tmp = UIOutputs.Archivo()
        
        if tmp == None:
            tmp = UIOutputs.Generico()
        
        tmp.setupUi(o)
        self.outputs.append(tmp)
        suma = 0
        for o2 in self.outputs:
            suma += o2.geometry().width()
        
        self.contenidoOutputs.resize(QtCore.QSize(suma, self.contenidoOutputs.geometry().height()))
        tmp.setSizePolicy(QtGui.QSizePolicy.Ignored,QtGui.QSizePolicy.Ignored)
        self.LayoutOutputs.addWidget(tmp)
    
    def loadData(self):
        xml = self.__xml
        try:
            nombre = xml.xpath("//data/nombre")
            desc = xml.xpath("//data/descripcion")
            self.LabelNombreTransmision.setText(u"Nombre:\n" + nombre[0].text)
            self.LabelDescripcionTransmision.setText(u"Descripción:\n" + desc[0].text)
        except:
            print "Error al intentar cargar la data de la transmisión."
            
    def GenerarTree(self):
        
        self.TreeData.clear()
        
        #primero los inputs
        inputs = QtGui.QTreeWidgetItem()
        inputs.setText(0,QtCore.QString("inputs"))
        xml_inputs = self.__xml.xpath("//input")
        for inp in xml_inputs:
            tmp_input = QtGui.QTreeWidgetItem()
            tmp_str = inp.get("tipo").encode("iso-8859-1")
            if (inp.get("nombre") != None):
                tmp_str = tmp_str + " - \"" + inp.get("nombre").encode("iso-8859-1")+"\""
            tmp_input.setText(0,tmp_str)
            hijos = inp.xpath("./*")
            for element in hijos:
                #print etree.tostring(element)
                tmp_input2 = QtGui.QTreeWidgetItem()
                tmp_input2.setText(0, element.get("nombre"))
                tmp_input.addChild(tmp_input2)
            inputs.addChild(tmp_input)
        #luego, los outputs
        outputs = QtGui.QTreeWidgetItem()
        outputs.setText(0,QtCore.QString("outputs"))
        xml_outputs = self.__xml.xpath("//output")
        for out in xml_outputs:
            tmp_output = QtGui.QTreeWidgetItem()
            tmp_output.setText(0,out.get("tipo"))
            hijos = out.xpath("./*")
            for element in hijos:
                tmp_output2 = QtGui.QTreeWidgetItem()
                tmp_output2.setText(0, element.get("nombre"))
                tmp_output.addChild(tmp_output2)
            outputs.addChild(tmp_output)
        
        self.TreeData.addTopLevelItems([inputs,outputs])
    
    def scrollInputs(self, valor):
        #el rango de visión tiene que ser igual al ancho mínimo del contenedor
        x = self.tab_inputs.scrollbar.oldvalor - valor
        self.tab_inputs.contenido.scroll(x,0)
        #guardo el valor para comparar con uno próximo
        self.tab_inputs.scrollbar.oldvalor = valor
    
    def scrollOutputs(self, valor):
        #el rango de visión tiene que ser igual al ancho mínimo del contenedor
        x = self.tab_outputs.scrollbar.oldvalor - valor
        self.tab_outputs.contenido.scroll(x,0)
        #guardo el valor para comparar con uno próximo
        self.tab_outputs.scrollbar.oldvalor = valor
    
    def setupUi(self):
        if (self.handler == None):
            self.handler = LiqHandler.LiqHandler()
        
        ii = []
        if (self.handler != None): 
            ii = self.handler.getInputs()
            for i in ii:
                self.loadInput(i)
            oo = self.handler.getOutputs()
            for o in oo:
                self.loadOutput(o)
        
        self.__xml = self.handler.GetXML()
        self.loadData()
        self.GenerarTree()
        
        self.GuntherTabs.setCurrentIndex(3)
        #QtCore.QObject.connect(self.tab_inputs.scrollbar, QtCore.SIGNAL("sliderMoved(int)"), self.scrollInputs)
        QtCore.QMetaObject.connectSlotsByName(self)
        
def ayuda():
    print "uso: python gunther.py [opciones] [nombre del archivo]\n"
    print "opciones:\n"
    print "-d, --debug:\n\tMuestra en la consola información útil para el diagnóstico de problemas.\n"
    print "-h, --help:\n\tMuestra este texto de ayuda.\n"

def debug(texto):
    if _debug > 0:
        tiempo = str(datetime.datetime.now())
        print "["+tiempo+"] - "+ texto

if __name__ == "__main__":
    global _debug
    _debug = 0
    try:                                
        opts, args = getopt.getopt(sys.argv[1:], "hg:d", ["help", "debug"])
    except getopt.GetoptError:
        print "opciones invalidas"
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            ayuda()
            sys.exit()
        elif opt in ("-d", "--debug"):
            _debug = 1
    
    app = QtGui.QApplication(sys.argv)
    xml = ""
    #si se indicó un nombre de archivo en los argumentos, se lo trata de cargar como xml
    #caso contrario, se instancia un wizard.
    for arc in args:
        if not os.path.isfile(arc):
            print "\""+arc+"\" no es un nombre de archivo válido.\n"
            ayuda()
            sys.exit(2)
        xml = etree.tostring(etree.parse(arc))
    if xml == "":
        W = wizard.GuntherWizard()
        W.setupUi()
        W.show()
        ret = app.exec_()
        W.GenerarXML()
        xml = etree.tostring(W.xml)
    #instancio un Günther
    Gunther = GuntherWindow()
    Gunther.handler = LiqHandler.LiqHandler(_debug)
    Gunther.handler.LoadXML(xml)
    Gunther.handler.EjecutarServer()
    limite = 30
    while not Gunther.handler.isConnected() and limite > 0:
        debug("Intentando conectar con LiquidSoap... (quedan "+str(limite)+" intentos)")
        Gunther.handler.Conectar()
        limite = limite -1
        time.sleep(2)
    if limite <= 0:
        print "La conexión con liquidsoap falló. No se puede continuar."
        Gunther.handler.DetenerServer()
        sys.exit(1)
    Gunther.setupUi()
    Gunther.show()
    ret = app.exec_()
    Gunther.handler.DetenerServer()
    sys.exit(ret)
