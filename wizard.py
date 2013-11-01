# -*- coding: utf-8 -*-

from PyQt4 import QtCore, QtGui, uic
from array import array
from struct import unpack, pack
import pyaudio, struct, math
import wave
import os
import httplib, urllib, json
from urlparse import urlparse
from lxml import etree
import random
import GuntherLib
import ui_rc

class GuntherWizard(QtGui.QWizard):
    Page_Bienvenida = 0
    Page_CargarArchivo = 1
    Page_Inputs = 2
    Page_PlaylistEstatico = 3
    Page_PlaylistDinamico = 4
    Page_Portaudio = 5
    Page_HTTP = 6
    Page_Outputs = 7
    Page_Icecast = 8
    Page_Grabar = 9
    Page_Parlantes = 10
    Page_Resumen = 11
    inputs = []
    outputs = []
    
    def __init__(self, parent = None):
        super(GuntherWizard,self).__init__(parent)
        self.ui = uic.loadUi("ui/wizard.ui",self)
        self.audioTester = AudioTester()
        self.audioTester.progressBar = self.progressBar
    
    def paintEvent(self,event):
        img = QtGui.QImage(QtCore.QString(":/wizard/superfondo-640.png"))
        bru = QtGui.QBrush(img)
        painter=QtGui.QPainter(self)
        painter.setBrush(bru)
        painter.drawRect(0,0,640,480)
        painter.end()
    
    def reject(self):
        exit(0)
    
    def nextId(self):
        id = self.currentId()
        self.GenerarXML()
        
        if id == self.Page_Bienvenida:
            return self.Page_CargarArchivo
        elif id == self.Page_CargarArchivo:
            if self.TextboxArchivoLoad.text().isEmpty():
                return self.Page_Inputs
            elif not os.path.isfile(self.TextboxArchivoLoad.text()):
                self.mostrar_error("El nombre del archivo es inválido.")
                return id #me quedo en la misma página
            else:
                return self.Page_Resumen
        elif id == self.Page_Inputs:
            self.set_inputs()
            if len(self.inputs) > 0:
                return self.inputs[0]
            else:
                return id
        elif id > self.Page_Inputs and id < self.Page_Outputs:
            if id in self.inputs:
                del self.inputs[self.inputs.index(id)]
            if len(self.inputs) == 0:
                return self.Page_Outputs
            else:
                return self.inputs[0]
                
        elif id == self.Page_Outputs:
            self.set_outputs()
            if len(self.outputs) > 0:
                return self.outputs[0]
            else:
                return id
        elif id > self.Page_Outputs and id < self.Page_Resumen:
            if id in self.outputs:
                del self.outputs[self.outputs.index(id)]
            if len(self.outputs) == 0:
                return self.Page_Resumen
            else:
                return self.outputs[0]
        elif id == self.Page_Resumen:
            self.GenerarTree()
            return -1
    
    def mostrar_error(self, mensaje):
        m = QtGui.QMessageBox()
        m.setWindowTitle("Error")
        m.setText(QtCore.QString.fromUtf8(mensaje))
        m.setIcon(QtGui.QMessageBox.Critical)
        m.exec_()
    
    def set_inputs(self):
        self.inputs = []
        if self.CheckboxPlaylistEstatico.isChecked():
            self.inputs.append(self.Page_PlaylistEstatico)
        if self.CheckboxPlaylistDinamico.isChecked():
            self.inputs.append(self.Page_PlaylistDinamico)
        if self.CheckboxPortaudio.isChecked():
            self.inputs.append(self.Page_Portaudio)
        if self.CheckboxHTTP.isChecked():
            self.inputs.append(self.Page_HTTP)
    
    def set_outputs(self):
        self.outputs = []
        if self.CheckboxIcecast.isChecked():
            self.outputs.append(self.Page_Icecast)
        if self.CheckboxGrabar.isChecked():
            self.outputs.append(self.Page_Grabar)
        if self.CheckboxParlantes.isChecked():
            self.outputs.append(self.Page_Parlantes)
    
    
    def setupUi(self):
        QtCore.QObject.connect(self.ButtonBrowseLoad, QtCore.SIGNAL("clicked()"), self.TextboxArchivoLoad.setFocus)
        QtCore.QObject.connect(self.ButtonBrowseLoad, QtCore.SIGNAL("clicked()"), self.LoadArchivo)
        QtCore.QObject.connect(self.ButtonAgregarArchivo, QtCore.SIGNAL("clicked()"), self.AgregarArchivoListaEstatica)
        QtCore.QObject.connect(self.ButtonQuitarArchivo, QtCore.SIGNAL("clicked()"), self.QuitarArchivoListaEstatica)
        QtCore.QObject.connect(self.horizontalSlider, QtCore.SIGNAL("valueChanged(int)"), self.setCantidadListasDinamicas)
        QtCore.QObject.connect(self.ButtonTestPortaudio, QtCore.SIGNAL("clicked()"), self.TestAudioInput)
        #QtCore.QObject.connect(self.ButtonRefreshServers, QtCore.SIGNAL("clicked()"), self.getServersFromWeb)
        #QtCore.QObject.connect(self.ButtonAgregarServerDeLista, QtCore.SIGNAL("clicked()"), self.agregarServerDesdeCombo)
        QtCore.QObject.connect(self.RadioButtonObtenerServer, QtCore.SIGNAL("clicked()"), self.ToggleOpcionTransmitir)
        QtCore.QObject.connect(self.RadioButtonConfigurarManualmente, QtCore.SIGNAL("clicked()"), self.ToggleOpcionTransmitir)
        QtCore.QObject.connect(self.ButtonBrowseDir, QtCore.SIGNAL("clicked()"), self.SeleccionarDondeGuardar)
        QtCore.QObject.connect(self.ButtonGuardarArchivo, QtCore.SIGNAL("clicked()"), self.SaveArchivo)
        
        self.TextPathGrabarArchivo.setText(GuntherLib.GetMyDocuments() + os.sep);
        
        QtCore.QMetaObject.connectSlotsByName(self)
    
    def LoadArchivo(self):
        archivo = QtGui.QFileDialog.getOpenFileName(None,"Elegí un archivo:", ".","*.gun")
        self.TextboxArchivoLoad.setText(archivo)
    def SaveArchivo(self):
        self.GenerarXML()
        archivo = QtGui.QFileDialog.getSaveFileName(None,"Elegí un nombre para el archivo:", ".","*.gun")
        try:
            f = open(archivo,"w")
            f.write(etree.tostring(self.xml))
            f.close()
        except:
            msgbox = QtGui.QMessageBox.critical(self, "Error", "Error al guardar el archivo \""+archivo+"\" :(", QtGui.QMessageBox.Ok)
    
    def ToggleOpcionTransmitir(self):
        self.TextURLListaServers.setEnabled(self.RadioButtonObtenerServer.isChecked())
        self.TableServidores.setEnabled(not self.RadioButtonObtenerServer.isChecked())
    
    def AgregarArchivoListaEstatica(self):
        archivos = QtGui.QFileDialog.getOpenFileNames(None,"Elegí archivos para la lista:", ".","*.*")
        #self.ListviewListaFija.clear()
        for nombre in archivos:
            self.ListviewListaFija.insertItem(self.ListviewListaFija.count(), QtCore.QString(nombre))
    
    def QuitarArchivoListaEstatica(self):
        self.ListviewListaFija.takeItem(self.ListviewListaFija.currentRow())
    
    def setCantidadListasDinamicas(self,a):
        self.TextCantidadListasDinamicas.setText(str(a))
        t = self.TablaNombresListasDinamicas
        while t.rowCount() < self.horizontalSlider.maximum():
            t.insertRow(t.rowCount())
        while t.rowCount() > self.horizontalSlider.maximum():
            t.removeRow(t.rowCount())
    
    def getServersFromWeb(self):
        #exije xml
        url = str(self.TextURLListaServers.text())
        if not url.endswith("/"):
            url = url + "/"
        url = url + "aapi/get_servidores_disponibles.php"
        self.servidores = []
        self.ComboServidores.clear()
        try:
            #tmp = etree.parse(urllib.urlopen(url))
            #tmp = json.load(urllib.urlopen(url))
            #self.servidores = tmp.xpath("//server")
            #self.servidores = tmp
            #print tmp[0]["datos"]["fields"]["NOMBRE"]["data"]["valor"]
            self.servidores = GuntherLib.GetModels(url)
        except Exception as e:
            #print e.args
            self.mostrar_error("El origen de datos no es válido :(")
            
        for servidor in self.servidores:
            self.ComboServidores.addItem(servidor.get("nombre"))
    
    def agregarServerDesdeCombo(self):
        #dado un item del combo, lo busca en self.servidores y lo carga a la lista
        for servidor in self.servidores:
            if self.ComboServidores.currentText() == servidor.get("nombre"):
                break
        
        current_row = 0
        for x in range(0,self.TableServidores.rowCount()-1):
            item = self.TableServidores.item(x,0)
            if item == None or item.text() == "":
                current_row = x
                break
        tmp = urlparse(servidor.get("url"))
        url = QtGui.QTableWidgetItem(str(tmp.hostname),0)
        url.setToolTip(servidor.get("nombre"))
        puerto = QtGui.QTableWidgetItem(str(tmp.port),0)
        formato = QtGui.QTableWidgetItem("ogg",0) #servidor.get("formato"),0)
        usuario = QtGui.QTableWidgetItem(servidor.get("user_transmision"),0)
        password = QtGui.QTableWidgetItem(servidor.get("pass_transmision"),0)
        mount = QtGui.QTableWidgetItem(servidor.get("mount_point"),0)
        
        self.TableServidores.setItem(current_row,0,url)
        self.TableServidores.setItem(current_row,1,puerto)
        self.TableServidores.setItem(current_row,2,formato)
        self.TableServidores.setItem(current_row,3,usuario)
        self.TableServidores.setItem(current_row,4,password)
        self.TableServidores.setItem(current_row,5,mount)
        
    
    def SeleccionarDondeGuardar(self):
        directorio = str(QtGui.QFileDialog.getExistingDirectory(None, "Select Directory",self.TextPathGrabarArchivo.text()))
        if directorio != "":
            self.TextPathGrabarArchivo.setText(directorio)
    
    def GenerarXML(self):
        #Genera un XML de uso interno, que persiste en el wizard.
        #Más tarde, ese XML se carga en el tree y/o se exporta
        tmp_xml = None
        if (os.path.isfile(self.TextboxArchivoLoad.text())):
            tmp_xml = etree.parse(str(self.TextboxArchivoLoad.text()))
        else:
            #genero el XML a mano, de acuerdo las opciones del wizard.
            tmp_xml = etree.Element("GunterConfig")
            inputs = etree.SubElement(tmp_xml, "inputs")
            #primero los inputs
            #1) cargar los items de la lista fija
            if (self.CheckboxPlaylistEstatico.isChecked()):
                tmploop = "loop=\"no\""
                tmprandom = "random=\"no\""
                if (self.CheckLoopListaFija.isChecked()):
                    tmploop = "loop=\"si\""
                if (self.CheckRandomListaFija.isChecked()):
                    tmprandom = "random=\"si\""
                tmp_str = "<input tipo=\"Lista Fija\" "+tmploop+" "+tmprandom+" >\n"
                for i in range(0,self.ListviewListaFija.count() ):
                    item = self.ListviewListaFija.item(i)
                    tmp_str = tmp_str + "<archivo nombre=\""+str(item.text().toUtf8())+"\" />\n"
                tmp_str = tmp_str + "</input>\n"
                input_fijo = etree.XML(tmp_str.decode("utf-8"))
                inputs.append(input_fijo)
            #2) cargar las listas dinámicas
            if (self.CheckboxPlaylistDinamico.isChecked()):
                for i in range(0,int(str(self.TextCantidadListasDinamicas.text()))):
                    item = self.TablaNombresListasDinamicas.item(i,0)
                    if (item != None):
                        tmp_str = "<input tipo=\"Lista Dinamica\" nombre=\""+str(item.text())+"\" />\n"
                        input_dinamico = etree.XML(tmp_str.decode("utf-8"))
                        inputs.append(input_dinamico)
            #3) el micrófono
            if (self.CheckboxPortaudio.isChecked()):
                tmp_str = "<input tipo=\"Microfono\" nombre=\"Microfono / Line-In\" />\n"
                input_mic = etree.XML(tmp_str.decode("utf-8"))
                inputs.append(input_mic)
            #4) retransmisión
            if (self.CheckboxHTTP.isChecked()):
                for i in range(0,self.tableWidget.rowCount()):
                    tmpnombre = ""
                    tmpurl = ""
                    if (self.tableWidget.item(i,0) != None):
                        tmpnombre = str(self.tableWidget.item(i,0).text())
                    if (self.tableWidget.item(i,1) != None):
                        tmpurl = str(self.tableWidget.item(i,1).text())
                    if tmpnombre != "" and tmpurl != "":
                        tmp_str = "<input tipo=\"Transmision Online\" nombre=\""+tmpnombre+"\" url=\""+tmpurl+"\" />\n"
                        input_http = etree.XML(tmp_str.decode("utf-8"))
                        inputs.append(input_http)
            
            #luego los outputs
            outputs = etree.SubElement(tmp_xml, "outputs")
            #1) Transmitir por internet
            if (self.CheckboxIcecast.isChecked()):
                if (self.RadioButtonConfigurarManualmente.isChecked()):
                    for i in range(0,self.TableServidores.rowCount()):
                        tmpnombre=""
                        tmpurl = ""
                        tmppuerto = ""
                        tmpformato = ""
                        tmpusuario = ""
                        tmpcontrasenia = ""
                        tmpmountpoint = ""
                        if (self.TableServidores.item(i,0) != None):
                            tmpurl = str(self.TableServidores.item(i,0).text())
                            tmpnombre = str(self.TableServidores.item(i,0).toolTip())
                            if ((tmpnombre == "") or (tmpnombre == None)):
                                tmpnombre = "Servidor remoto #" + str(random.randint(1000,9999))
                        if (self.TableServidores.item(i,1) != None):
                            tmppuerto = str(self.TableServidores.item(i,1).text())
                        if (self.TableServidores.item(i,2) != None):
                            tmpformato = str(self.TableServidores.item(i,2).text())
                        if (self.TableServidores.item(i,3) != None):
                            tmpusuario = str(self.TableServidores.item(i,3).text())
                        if (self.TableServidores.item(i,4) != None):
                            tmpcontrasenia = str(self.TableServidores.item(i,4).text())
                        if (self.TableServidores.item(i,5) != None):
                            tmpmountpoint = str(self.TableServidores.item(i,5).text())
                        if (tmpurl != ""):
                            tmp_str = "<output tipo=\"Servidor Remoto\" nombre=\""+tmpnombre+"\" url=\""+tmpurl+"\" puerto=\""+tmppuerto+"\" formato=\""+tmpformato+"\" usuario=\""+tmpusuario+"\" contrasenia=\""+tmpcontrasenia+"\" mountpoint=\""+tmpmountpoint+"\"/>\n"
                            output_http = etree.XML(tmp_str.decode("utf-8"))
                            outputs.append(output_http)
                else:
                    tmp_str = "<output tipo=\"Servidor Automatico\" url=\""+unicode(self.TextURLListaServers.text())+"\"/>\n"
                    output_http = etree.XML(tmp_str.decode("utf-8"))
                    outputs.append(output_http)
            #2) Grabar en archivo
            if (self.CheckboxGrabar.isChecked()):
                tmp_str = "<output tipo=\"Archivo\" nombre=\""+str(self.TextPathGrabarArchivo.text())+"\" />\n"
                output_archivo = etree.XML(tmp_str.decode("utf-8"))
                outputs.append(output_archivo)
            #3) Escuchar por los parlantes
            if (self.CheckboxParlantes.isChecked()):
                tmp_str = "<output tipo=\"Parlantes\" nombre=\"Parlantes o auriculares conectados a la computadora\" />\n"
                output_parlantes = etree.XML(tmp_str.decode("utf-8"))
                outputs.append(output_parlantes)
            
            #Y por último, la información de la transmisión
            data = etree.SubElement(tmp_xml, "data")
            tmp_str = u"<nombre>"+unicode(self.TextNombreTransmision.text())+u"</nombre>\n"
            data.append(etree.XML(tmp_str))
            tmp_str = u"<descripcion>"+unicode(self.TextDescripcionTransmision.text())+u"</descripcion>\n"
            data.append(etree.XML(tmp_str))
            
        self.xml = tmp_xml
    
    def GenerarTree(self):
        #print etree.tostring(self.xml, pretty_print=True)
        self.TreeResumenConfiguraciones.clear()
        
        #primero los inputs
        inputs = QtGui.QTreeWidgetItem()
        inputs.setText(0,QtCore.QString("inputs"))
        xml_inputs = self.xml.xpath("//input")
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
        xml_outputs = self.xml.xpath("//output")
        for out in xml_outputs:
            tmp_output = QtGui.QTreeWidgetItem()
            tmp_output.setText(0,out.get("tipo"))
            hijos = out.xpath("./*")
            for element in hijos:
                tmp_output2 = QtGui.QTreeWidgetItem()
                tmp_output2.setText(0, element.get("nombre"))
                tmp_output.addChild(tmp_output2)
            outputs.addChild(tmp_output)
        
        self.TreeResumenConfiguraciones.addTopLevelItems([inputs,outputs])
        try:
            self.TextNombreTransmision.setText(self.xml.xpath("//data/nombre")[0].text)
            self.TextDescripcionTransmision.setText(self.xml.xpath("//data/descripcion")[0].text)
        except Exception as e:
            pass
    
    def TestAudioInput(self):
        for i in range(250):
            self.audioTester.listen()
        self.progressBar.setValue(0)
        
        
INITIAL_TAP_THRESHOLD = 0.010
FORMAT = pyaudio.paInt16 
SHORT_NORMALIZE = (1.0/32768.0)
CHANNELS = 1
RATE = 22050  
INPUT_BLOCK_TIME = 0.05
INPUT_FRAMES_PER_BLOCK = int(RATE*INPUT_BLOCK_TIME)
# if we get this many noisy blocks in a row, increase the threshold
OVERSENSITIVE = 15.0/INPUT_BLOCK_TIME                    
# if we get this many quiet blocks in a row, decrease the threshold
UNDERSENSITIVE = 120.0/INPUT_BLOCK_TIME 
# if the noise was longer than this many blocks, it's not a 'tap'
MAX_TAP_BLOCKS = 0.15/INPUT_BLOCK_TIME


class AudioTester(object):
    def __init__(self):
        self.pa = pyaudio.PyAudio()
        self.stream = self.open_mic_stream()
        self.tap_threshold = INITIAL_TAP_THRESHOLD
        self.noisycount = MAX_TAP_BLOCKS+1 
        self.quietcount = 0 
        self.errorcount = 0
        self.progressBar = None

    def stop(self):
        self.stream.close()
    
    def get_rms(self, block):
        # RMS amplitude is defined as the square root of the 
        # mean over time of the square of the amplitude.
        # so we need to convert this string of bytes into 
        # a string of 16-bit samples...

        # we will get one short out for each 
        # two chars in the string.
        count = len(block)/2
        format = "%dh"%(count)
        shorts = struct.unpack( format, block )

        # iterate over the block.
        sum_squares = 0.0
        for sample in shorts:
            # sample is a signed short in +/- 32768. 
            # normalize it to 1.0
            n = sample * SHORT_NORMALIZE
            sum_squares += n*n

        return math.sqrt( sum_squares / count )
    
    def find_input_device(self):
        device_index = None            
        for i in range( self.pa.get_device_count() ):     
            devinfo = self.pa.get_device_info_by_index(i)   
            print( "Device %d: %s"%(i,devinfo["name"]) )

            for keyword in ["mic","input"]:
                if keyword in devinfo["name"].lower():
                    print( "Found an input: device %d - %s"%(i,devinfo["name"]) )
                    device_index = i
                    return device_index

        if device_index == None:
            print( "No preferred input found; using default input device." )

        return device_index

    def open_mic_stream( self ):
        device_index = self.find_input_device()

        stream = self.pa.open(   format = FORMAT,
                                 channels = CHANNELS,
                                 rate = RATE,
                                 input = True,
                                 input_device_index = device_index,
                                 frames_per_buffer = INPUT_FRAMES_PER_BLOCK)

        return stream
    
    
    
    def listen(self):
        try:
            block = self.stream.read(INPUT_FRAMES_PER_BLOCK)
        except IOError, e:
            # dammit. 
            self.errorcount += 1
            print( "(%d) Error recording: %s"%(self.errorcount,e) )
            self.noisycount = 1
            return

        amplitude = self.get_rms( block )
        print amplitude
        self.progressBar.setValue(amplitude * 100)
