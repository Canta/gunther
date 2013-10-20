# -*- coding: utf-8 -*-

from PyQt4 import QtCore, QtGui, uic
import sys, getopt, os, time, datetime
import json
import ui_rc
import requests

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s



class Progress(object):
    def __init__(self):
        self._seen = 0.0
        print "Progress inicializado"

    def update(self, total, size, name):
        self._seen += size
        pct = (self._seen / total) * 100.0
        print '%s progress: %.2f' % (name, pct)

class file_with_callback(file):
    def __init__(self, path, mode, callback, *args):
        try:
            file.__init__(self, path, mode)
            self.seek(0, os.SEEK_END)
            self._total = self.tell()
            self.seek(0)
            self._callback = callback
            self._args = args
        except Exception as e:
            print e
            pass

    def __len__(self):
        return self._total

    def read(self, size=0):
        if (size==0):
            data = file.read(self)
        else:
            data = file.read(self, size)
        self._callback(self._total, len(data), *self._args)
        return data

class GuntherUploader(QtGui.QMainWindow):
    def __init__(self, parent = None):
        super(GuntherUploader,self).__init__(parent)
        self.ui = uic.loadUi("ui/uploader.ui",self)
        self.__url  = "https://api.mixcloud.com/upload/?access_token=97tHhxq78dH5APcpQHHx9Et3tNypqDXW"
    
    def SetNombrePodcast(self, n = u""):
        self.textPodcastName.setText(n)
    
    def SetDescripcionPodcast(self, d = u""):
        self.textDescripcion.setText(d)
    
    def setupUI(self, archivo, nombre, descripcion = ""):
        if not os.path.exists(archivo):
            print u"\""+archivo+"\" no existe. Imposible continuar con el upload."
            sys.exit(1)
        self.textStatus.setPlainText("")
        self.log(u"Archivo: \""+archivo+"\"")
        self.log(u"Presione \"Subir\" para continuar, o \"Cerrar\" para cancelar...")
        
        self.SetNombrePodcast(nombre)
        self.SetDescripcionPodcast(descripcion)
        self.__archivo = archivo
        
        QtCore.QObject.connect(self.buttonCerrar, QtCore.SIGNAL("clicked()"), self.cerrar)
        QtCore.QObject.connect(self.buttonOk, QtCore.SIGNAL("clicked()"), self.subir)
        QtCore.QMetaObject.connectSlotsByName(self)
    
    def cerrar(self):
        self.close()
    
    def subir(self):
        self.buttonOk.setEnabled(False)
        self.buttonCerrar.setEnabled(False)
        self.log(u"Iniciando upload.")
        self.upload()
        #self.buttonOk.setEnabled(True)
        self.buttonCerrar.setEnabled(True)
        pass
    
    def log(self, texto):
        tiempo = str(datetime.datetime.now())
        self.textStatus.setPlainText(self.textStatus.toPlainText() +"["+tiempo[:19]+"] - "+ texto + "\n")
        self.textStatus.moveCursor(11)
        self.textStatus.ensureCursorVisible()
        
    def upload(self):
        try:
            p = Progress()
            files = {"mp3":file_with_callback(self.__archivo, "rb", p.update, self.__archivo)}
            data = {"name":self.textPodcastName.text(), "description":self.textDescripcion.text()}
            r = requests.post(self.__url, files=files, data=data)
            self.log(u"Upload finalizado. Código de la respuesta: " + unicode(r.status_code))
            if r.status_code == 200:
                resp = json.loads(r.text)
                if resp["result"]["success"] == True:
                    self.log(u"Ya podés escuchar y compartir tu podcast en http://www.mixcloud.com" + resp["result"]["key"])
                else:
                    self.log(u"Ocurrió un error: "+ resp["result"]["message"])
            else:
                self.log(u"Error #"+unicode(r.status_code)+": "+ resp["result"]["message"])
        except Exception as e:
            self.log(u"Error: " + unicode(e))
            pass

if __name__ == "__main__":
    nombre = u"Günther Cloudcast"
    desc   = u"Transmisión de RadioCEFyL grabada con Günther."
    archivo = None
    try:                                
        opts, args = getopt.getopt(sys.argv[1:], "a:n:d:", ["archivo=","nombre=", "descripcion="])
    except getopt.GetoptError as e:
        print e
        print "opciones invalidas"
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-n", "--nombre"):
            nombre = arg.decode("utf-8","replace")
        elif opt in ("-d", "--descripcion"):
            desc = arg.decode("utf-8","replace")
        elif opt in ("-a", "--archivo"):
            archivo = arg.decode("utf-8","replace")
    
    if archivo == None:
        print "Debe especificar un archivo."
        sys.exit(2)
    app = QtGui.QApplication(sys.argv)
    GU = GuntherUploader()
    GU.setupUI(archivo, nombre, desc)
    GU.show()
    sys.exit(app.exec_())

