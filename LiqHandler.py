# -*- coding: utf-8 -*-

import telnetlib
import threading
import os
import sys
import subprocess
import time
from lxml import etree
from PyQt4 import QtCore, QtGui
import gunther
import datetime
import GuntherLib
import urllib
from urlparse import urlparse
import random

class UrlGetter(QtCore.QThread):
    def __init__(self, url = "", handler = None):
        super(UrlGetter, self).__init__()
        self.__url = url
        self.__handler = handler
    
    def run(self):
        a = urllib.urlopen(self.__url)
        meta = a.read()
        self.__handler.SetMetadata(meta)

class MetaObject(object):
    def __init__(self):
        self.__debug = 0
        
    def setDebugValue(self, value):
        self.__debug = value
    def debug(self, texto):
        if self.__debug > 0:
            tiempo = QtCore.QString(str(datetime.datetime.now()))
            try:
                print "["+tiempo+"] - " + texto
            except Exception as e:
                try:
                    print "["+tiempo+"] - " + QtCore.QString(texto)
                except Exception as e2:
                    print u"["+unicode(tiempo)+"] - " + unicode(texto)

class Input(QtCore.QThread):
    #Esta clase se usa para que LiqBuilder sepa construir un script
    def __init__(self, nombre = "", handler = None):
        super(Input, self).__init__()
        self.__nombre = nombre
        self.__codigo = ""
        self.__tickIntervalStatus = 1000
        self.__handler = handler
        self.__index = 0 #para persistir el índice en el mixer, que debería ser el mismo que en los arrays de objetos
        self.__separador = "/"
        self.__newline = "\n"
        if "win" in sys.platform:
            self.__separador = "\\"
            self.__newline = "\r\n"
        self.__datos = {}
    def GetDatos(self):
        return self.__datos
    def SetDatos(self,obj):
        self.__datos = obj
    def GetSeparador(self):
        return self.__separador
    def GetNewline(self):
        return self.__newline
    def GetNombre(self, limpio = False):
        if (limpio == False):
            return self.__nombre
        else:
            return self.ClearString(self.__nombre)
    def GetCodigo(self):
        return self.__codigo
    def SetCodigo(self, codigo):
        self.__codigo = codigo
    def ClearString(self,texto):
        #print unicode(texto)
        texto2 = texto#.decode('utf8')
        texto2 = texto2.replace(" ", "")
        texto2 = texto2.replace(u"á", "a")
        texto2 = texto2.replace(u"é", "e")
        texto2 = texto2.replace(u"í", "i")
        texto2 = texto2.replace(u"ó", "o")
        texto2 = texto2.replace(u"ú", "u")
        texto2 = texto2.replace("/", "")
        texto2 = texto2.replace("?", "")
        texto2 = texto2.replace("!", "")
        texto2 = texto2.replace(u"ü", "u")
        texto2 = texto2.replace(u"ñ", "n")
        texto2 = texto2.replace("#", "")
        texto2 = texto2.replace("&", "")
        texto2 = texto2.replace("\"", "")
        texto2 = texto2.replace("?", "_")
        texto2 = texto2.replace(",", "")
        texto2 = texto2.replace("-", "")
        return texto2
    def setIntervalStatus(self,interval = 1000):
        self.__tickIntervalStatus = interval
    def getIntervalStatus(self):
        return self.__tickIntervalStatus
    def checkStatus(self):
        pass
    def getHandler(self):
        return self.__handler
    def tickRMS(self):
        #consigo la información del servidor LiquidSoap
        ret = self.GetDatos()
        h = self.getHandler()
        #primero los rms del sonido
        rms = h.SendComando("vm" + self.GetNombre(True)+".rms")
        rms = rms.replace(self.GetNewline(),"")
        try:
            ret["rms"] = rms
        except:
            h.debug("Input.tickStatus(): Error al internet obtener los RMS. Nombre del input: " + self.GetNombre(True))
        self.SetDatos(ret)

    def tickEstado(self):
        ret = self.GetDatos()
        h = self.getHandler()
        stats = h.SendComando("mixer.status "+str(self.getIndex()))
        #debería devolver algo como esto:
        #ready=true selected=true single=false volume=100% remaining=194.30
        #la proceso para acomodarla en un array
        for item in stats.replace(self.GetNewline(),"").split(" "):
            item_separado = item.split("=")
            try:
                ret[item_separado[0]] = item_separado[1]
            except:
                pass
        self.SetDatos(ret)
    def tickStatus(self):
        self.tickRMS()
        self.emit( QtCore.SIGNAL('updateStatus(PyQt_PyObject)'), self.GetDatos())
    def run(self):
        #defino los timers
        self.__timerStatus = QtCore.QTimer()
        self.__timerEstado = QtCore.QTimer()
        #conecto funciones a slots de los timers
        QtCore.QObject.connect(self.__timerStatus, QtCore.SIGNAL("timeout()"), self.tickStatus)
        QtCore.QObject.connect(self.__timerEstado, QtCore.SIGNAL("timeout()"), self.tickEstado)
        QtCore.QMetaObject.connectSlotsByName(self)
        #y ejecuto todo
        #print "start " + str( self.getIntervalStatus())
        self.__timerStatus.start(self.getIntervalStatus())
        self.__timerEstado.start(3000)
        self.exec_()
    def setIndex(self, valor = 0):
        self.__index = valor
    def getIndex(self):
        return self.__index
class Output(QtCore.QThread):
    #Clase para que LiqBuilder sepa construir un script
    def __init__(self, nombre = "", handler = None):
        super(Output, self).__init__()
        self.__nombre = nombre
        self.__codigo = ""
        self.__tickIntervalStatus = 1000
        self.__handler = handler
        self.__separador = "/"
        self.__newline = "\n"
        if "win" in sys.platform:
            self.__separador = "\\"
            self.__newline = "\r\n"
    def GetSeparador(self):
        return self.__separador
    def GetNewline(self):
        return self.__newline
    def run(self):
        self.exec_()
    def GetHandler(self):
        return self.__handler
    def ActivateOnline(self):
        pass
    def Finalize(self):
        pass
    def GetNombre(self):
        return self.__nombre
    def GetCodigo(self):
        return self.__codigo
    def SetCodigo(self, codigo):
        self.__codigo = codigo
    def ClearString(self,texto):
        #print unicode(texto)
        texto2 = texto#.decode('utf8')
        texto2 = texto2.replace(" ", "")
        texto2 = texto2.replace(u"á", "a")
        texto2 = texto2.replace(u"é", "e")
        texto2 = texto2.replace(u"í", "i")
        texto2 = texto2.replace(u"ó", "o")
        texto2 = texto2.replace(u"ú", "u")
        texto2 = texto2.replace("/", "")
        texto2 = texto2.replace("?", "")
        texto2 = texto2.replace("!", "")
        texto2 = texto2.replace(u"ü", "u")
        texto2 = texto2.replace(u"ñ", "n")
        texto2 = texto2.replace("#", "")
        texto2 = texto2.replace("&", "")
        texto2 = texto2.replace("\"", "")
        texto2 = texto2.replace("?", "")
        texto2 = texto2.replace(",", "")
        texto2 = texto2.replace("-", "")
        return texto2
    def setIntervalStatus(self,interval = 1000):
        self.__tickIntervalStatus = interval
    def getIntervalStatus(self):
        return self.__tickIntervalStatus
    def checkStatus(self):
        pass

class Evento(MetaObject):
    def __init__(self):
        self.__callables = []
    def __call__(self):
        for c in self.__callables:
            c.call()
    def addHandler(self, funcion = None):
        if (funcion != None):
            try:
                self.__callables[id(funcion)]
            except IndexError:
                self.__callables[id(funcion)] = funcion
    def removeHandler(self, funcion = None):
        if (function != None):
            try:
                self.__callables[id(funcion)]
            except IndexError:
                self.__callables[id(funcion)] = None
        else:
            #si no paso una función, saco el último item ingresado
            if (len(self.__callables) > 0):
                self.__callables.pop()
                

class MicIn(Input):
    #Entrada directa de micrófono
    def __init__(self,nombre, handler = None):
        super(MicIn,self).__init__(nombre, handler)
        tmpCodigo = self.ClearString(str(self.GetNombre()))+" = in(id=\""+self.ClearString(self.GetNombre())+"\", fallible=true)\n"
        tmpCodigo += self.ClearString(str(self.GetNombre()))+" = server.rms(id=\"vm"+self.ClearString(str(self.GetNombre()))+"\", "+self.ClearString(str(self.GetNombre()))+")\n"
        self.SetCodigo(tmpCodigo)
        
class LineIn(Input):
    #Line-In
    pass

class Playlist(Input):
    #Lista de temas en el disco.
    def __init__(self,nombre, handler = None):
        super(Playlist,self).__init__(nombre, handler)
        tmpCodigo = self.ClearString(str(self.GetNombre()))+" = playlist(\""+self.ClearString(self.GetNombre())+"\")\n"
        tmpCodigo += self.ClearString(str(self.GetNombre()))+" = fallback([request.equeue(id=\""+self.ClearString(self.GetNombre())+"-tracks\"), "+self.ClearString(self.GetNombre())+"])\n"
        tmpCodigo += self.ClearString(str(self.GetNombre()))+" = server.rms(id=\"vm"+self.ClearString(str(self.GetNombre()))+"\", "+self.ClearString(str(self.GetNombre()))+")\n"
        self.SetCodigo(tmpCodigo)
        self.__archivos = []
    def GetArchivos(self):
        return self.__archivos
    def AgregarArchivo(self, arch):
        self.__archivos.append(arch)
    def QuitarArchivo(self,indice = None):
        if (indice == None):
            self.__archivos.pop()
        else:
            del self.__archivos[indice]

    def tickMetadata(self):
        ret = self.GetDatos()
        h = self.getHandler()
        #y ahora la metadata.
        #Para eso se usa el comando metadata, que funciona con una serie de RIDs autónomos
        #Los RIDs de metadata se obtienen con el comando "alive", que devuelve una lista de temas actualmente transmitiendo.
        #Eso es así porque se puede usar RIDs viejos, de temas que ya no están transmitiendo.
        #Una vez con los RIDs actuales, busco el que corresponde a cada Input.
        rids = h.SendComando("request.alive")
        rids = rids.replace(self.GetNewline(),"").split(" ")
        meta = []
        for rid in rids:
            meta = h.SendComando("request.metadata " + str(rid))
            if "source=\""+self.GetNombre(True)+"\"" in meta:
                for item in meta.split("\n"):
                    separado = item.split("=")
                    if len(separado) > 1:
                        ret[separado[0]] = separado[1]
                break
        self.SetDatos(ret)

    def run(self):
        self.__timerMetadata = QtCore.QTimer()
        #conecto funciones a slots de los timers
        QtCore.QObject.connect(self.__timerMetadata, QtCore.SIGNAL("timeout()"), self.tickMetadata)
        QtCore.QMetaObject.connectSlotsByName(self)
        #y ejecuto todo
        self.__timerMetadata.start(5000)
        super(Playlist,self).run()

class PlaylistEstatico(Playlist):
    #Lista de temas en el disco.
    def __init__(self,nombre, handler = None, archivos = [], rand = "si", lup = "si"):
        super(PlaylistEstatico,self).__init__(nombre, handler)
        #Un playlist estático, necesito cargarlo de un archivo.
        #Para eso, lo creo siempre.
        f = open("tmp-playlist-"+self.ClearString(self.GetNombre())+".pls","w")
        for a in archivos:
            self.AgregarArchivo(a)
            if "win" in sys.platform:
                f.write(a.encode("iso-8859-1")+self.GetNewline())
            else:
                f.write(a.encode("utf-8")+self.GetNewline())
        f.close()
        
        tmp_mode = ""
        tmp_input = ""
        
        if (lup == "no"):
            tmp_input = "playlist.once"
            if (rand == "no"):
                tmp_mode = "random=false"
            else:
                tmp_mode = "random=true"
        else:
            tmp_input = "playlist"
            if (rand == "no"):
                tmp_mode = "mode=\"normal\""
            else:
                tmp_mode = "mode=\"random\""
        
        
        pls_path = sys.path[0].replace(self.GetSeparador() + "library.zip","")+self.GetSeparador()+"tmp-playlist-"+self.ClearString(self.GetNombre())
        tmpCodigo = self.ClearString(str(self.GetNombre()))+" = "+tmp_input+"(id=\""+self.ClearString(self.GetNombre())+"\", "+tmp_mode+", \"file://"+pls_path.replace("\\","/")+".pls\")\n"
        tmpCodigo += self.ClearString(str(self.GetNombre()))+" = server.rms(id=\"vm"+self.ClearString(str(self.GetNombre()))+"\", "+self.ClearString(str(self.GetNombre()))+")\n"
        self.SetCodigo(tmpCodigo)

class Stream(Input):
    #Un stream directo desde internet.
    def __init__(self,nombre, uri, handler = None):
        super(Stream,self).__init__(nombre, handler)
        tmpCodigo = self.ClearString(self.GetNombre())+" = input.http(id=\""+self.ClearString(self.GetNombre())+"\", \""+uri+"\")\n"
        tmpCodigo += self.ClearString(str(self.GetNombre()))+" = server.rms(id=\"vm"+self.ClearString(str(self.GetNombre()))+"\", "+self.ClearString(str(self.GetNombre()))+")\n"
        self.SetCodigo(tmpCodigo)

class Archivo(Output):
    #Output a un archivo.
    def __init__(self, nombre, uri, handler = None):
        super(Archivo,self).__init__(nombre, handler)
        if (uri.strip() == "" or uri.strip() == "."):
            tmp = os.path.abspath(__file__).split(os.sep)
            uri = os.sep.join(tmp[0:-1]) + os.sep
        self.__path = uri
        self.__date = datetime.datetime.now()
        data = handler.GetDataTransmision()
        nombre = data["nombre"]
        if nombre == "":
            nombre = "Gunther Record"
        print self.__date.strftime("%Y-%m-%d_%H-%M-%S")
        print nombre
        self.__filename = "["+self.__date.strftime("%Y-%m-%d_%H-%M-%S") +"] - "+nombre+".mp3"
        tmpCodigo = self.ClearString(self.GetNombre())+" = output.file(id=\""+self.ClearString(self.GetNombre())+"\", fallible=true, %mp3(bitrate=96,stereo=false,samplerate=22050), \""+uri+self.__filename+"\",mean(mixer))\n"
        self.SetCodigo(tmpCodigo)
    
    def Finalize(self):
        #print "Subiendo podcast..."
        #print GuntherLib.UploadPodcast(self.__filename)
        try:
            data = self.GetHandler().GetDataTransmision()
            nombre = data["nombre"]
            desc = data["descripcion"]
            os.system("python uploader.py -a \""+self.GetFullPath()+"\" -n \""+nombre+"\" -d \""+desc+"\" ")
        except Exception as e:
            print e
        #print "...Podcast subido."
        pass
        
    def GetPath(self):
        return self.__path
    def GetFilename(self):
        return self.__filename
    def GetFullPath(self):
        return self.__path + self.__filename

class Soundcard(Output):
    def __init__(self, nombre, handler = None):
        super(Soundcard,self).__init__(nombre, handler)
        tmpCodigo = self.ClearString(str(self.GetNombre()))+" = output.prefered(id=\""+self.ClearString(self.GetNombre())+"\", mixer)\n"
        #tmpCodigo += "ignore(server.rms(id=\"vm"+self.ClearString(str(self.GetNombre()))+"\", "+self.ClearString(str(self.GetNombre()))+"))\n"
        self.SetCodigo(tmpCodigo)

class Broadcast(Output):
    #Stream remoto: icecast o shoutcast.
    def __init__(self, nombre, host, password, username="source", puerto=8000, mount="", formato="%ogg", handler = None):
        super(Broadcast,self).__init__(nombre, handler)
        self.__host = unicode(host)
        self.__port = unicode(puerto)
        self.__user = unicode(username)
        self.__pass = unicode(password)
        self.__mount = unicode(mount)
        self.__formato = self.FixFormato(formato)
        self.__hash = ""
        self.__metadata = ""
        self.__metadataUpdater = UrlGetter(self.GetURL(),self)
        #print([nombre, host, password, username, puerto, mount, formato])
        #tmpCodigo = self.ClearString(str(self.GetNombre()))+" = server.rms(id=\"vm"+self.ClearString(str(self.GetNombre()))+"\", mixer)\n"
        tmpCodigo = self.ClearString(str(self.GetNombre()))+" = output.icecast(id=\""+self.ClearString(str(self.GetNombre()))+"\", mount=\""+self.__mount+"\", description=\"Gunther radio!\", url=\"http://www.radiofyl.com.ar\", fallible=true, host=\""+self.__host+"\", port="+self.__port+",user=\""+self.__user+"\", password=\""+self.__pass+"\", "+self.__formato+", mean(mixer))\n"
        self.SetCodigo(tmpCodigo)
    def GetHost(self):
        return self.__host
    def GetPuerto(self):
        return self.__port
    def GetUser(self):
        return self.__user
    def GetPass(self):
        return self.__pass
    def GetMountpoint(self):
        return self.__mount
    def FixFormato(self, formato):
        #dado un formato, lo arregla de modo tal que se pueda usar en liquidsoap
        ret = formato
        if (formato == "mp3" or formato == "%mp3"):
            ret = "%mp3(samplerate=22050, bitrate=96, stereo=false)"
        elif (formato == "ogg" or formato == "%ogg"):
            ret = "%ogg(%vorbis.cbr(samplerate=44100, bitrate=128, channels=1))"
        return ret
    def ActivateOnline(self):
        url = self.GetURL() + self.GetMountpoint()
        handler = self.GetHandler()
        data = handler.GetDataTransmision()
        handler.debug("url: "+url)
        handler.debug("data: "+str(len(url)) + " campos.")
        #print data
        try:
            tmp = GuntherLib.AddTransmision(url, data["nombre"], data["descripcion"])
            #self.debug("obtenido:" + tmp)
            self.__hash = str(tmp["data"]["hash"])
            #self.debug("hash:" + self.__hash)
        except Exception as e:
            handler.debug('Error al intentar registrar online la transmision:')
            raise e
        
    def Finalize(self):
        try:
            tmp = GuntherLib.FinalizeTransmision(self.__hash)
            return tmp
        except Exception as e:
            self.debug('Error al intentar registrar online la transmision:')
    
    def GetURL(self):
        ret = "http://" + self.GetHost() + ":" + str(self.GetPuerto())
        return ret
    
    def SetMetadata(self, metadata):
        self.__metadata = metadata
        
    def GetMetadata(self):
        return self.__metadata
    
    def UpdateMetadata(self):
        #acá me tengo que conectar al servidor, leer la metadata, y guardarla en un string.
        self.__metadataUpdater.exit(0)
        self.__metadataUpdater.start()
        
    
    def run(self):
        self.__timerMetadata = QtCore.QTimer()
        #conecto funciones a slots de los timers
        QtCore.QObject.connect(self.__timerMetadata, QtCore.SIGNAL("timeout()"), self.UpdateMetadata)
        QtCore.QMetaObject.connectSlotsByName(self)
        #y ejecuto todo
        self.__timerMetadata.start(random.randint(30000,40000))
        super(Broadcast,self).run()

class LiqBuilder(MetaObject):
    #Este clase de se encarga de, dados una serie de objetos
    #"Input" y "Output", que se pasan en array por parámetro
    #generar un script de Liquidsoap acorde a las configuraciones.
    def __init__(self):
        pass
    def GenerarCodigo(self, inputs = [], outputs = []):
        tmp_input = ""
        tmp_mixer = "mixer = mix(id=\"mixer\",["
        #tmp_selects = ""
        c=0
        for i in inputs:
            tmp_input += i.GetCodigo()
            tmp_mixer += i.ClearString(i.GetNombre())
            #tmp_selects += "mixer.select " + str(c) + " true\n"
            if (len(inputs) != c):
                tmp_mixer += ", "
            c = c + 1
            
        tmp_mixer += "blank(id=\"silencio\")])\n"
        tmp_output = ""
        for o in outputs:
            tmp_output += o.GetCodigo()
        return tmp_input + tmp_mixer + tmp_output #+ tmp_selects
    
class LiqHandler(MetaObject):
    #Defino un componente telnet para la clase.
    #Se va a encargar de la ida y vuelta de comandos a liquidsoap
    def __init__(self, _debug = 0):
        super(LiqHandler,self).__init__()
        self.setDebugValue(_debug);
        self.__telnet = None
        self.__conectado = False
        self.__builder = LiqBuilder()
        self.__separador = "/"
        self.__newline = "\n"
        if "win" in sys.platform:
            self.__separador = "\\"
            self.__newline = "\r\n"
        self.__server_commandline = "liquidsoap.exe"
        self.__server_script = "tmp.liq"
        self.__server_subprocess = None
        self.__inputs = []
        self.__outputs = []
        self.__xml = None
        #manejo de eventos
        self.onTickStatus = Evento()
        self.timerStatus = threading.Timer(1, self.tickStatus())
        self.onConnect = Evento()
        self.onDisconnect = Evento()

    def GetNewline(self):
        return self.__newline
    def isConnected(self):
        return self.__conectado
    def getInputs(self):
        return self.__inputs
    def getOutputs(self):
        return self.__outputs
    def tickStatus(self):
        if (self.__conectado == True):
            self.onTickStatus()
    
    def Conectar(self):
        try:
            self.__telnet = telnetlib.Telnet("localhost", 1234)
        except:
            self.__conectado = False
            self.debug(u"LiqHandler.conectar(): No se pudo conectar a liquidsoap. Buscando texto de diagnóstico...")
            #try:
            #    out,err = self.__server_subprocess.communicate()
            #    self.debug("\nstdout: " + str(out)+"\nstderr: " + str(err)+"\n")
            #except:
            #    pass
            self.debug(u"...fín del texto de diagnóstico de Liquidsoap.")
        else:
            self.debug(u"Conectado a Liquidsoap vía Telnet. Ejecutando onConnect()...")
            self.__conectado = True
            self.onConnect()
            self.debug(u"onConnect() ejecutado.")
    
    def SendComando(self, comando):
        command_output = ""
        #primero me aseguro de que el newline sea \n
        comando = comando.replace(self.GetNewline(),"").replace("\n","").replace("\r","")
        if (unicode(QtCore.QString(comando)).endswith("\n") == False):
            comando = comando + "\n"
        #Ahora, ejecuto el comando (si corresponde), y leo hasta 
        if (self.__conectado == True):
            try:
                self.__telnet.write(QtCore.QString(comando).toAscii())
                self.debug(u"LiqHandler.SendComando(): \""+comando+"\" .")
                command_output = QtCore.QString(self.__telnet.read_until(self.GetNewline() + "END"))
                self.debug(u"LiqHandler.SendComando(): Respuesta: \""+command_output+"\" .")
            except Exception as e:
                print e
                self.debug(u"LiqHandler.SendComando(\""+comando+"\"): error al intentar ejecutar el comando. Se reconectará a Liquidsoap.")
                self.Conectar()
                
        return unicode(command_output).replace(self.GetNewline() + "END","")

    def EjecutarServer(self):
        self.debug("Ejecutando liquidsoap...")
        try:
            f = open("tmp.liq", "w")
            print>>f, self.GetCodigo()
            f.close()
            
            if "win" in sys.platform:
                #de acuerdo al ticket #6, implemento primero una detección del directorio de ejecución de Liquidsoap.
                self.debug(u"Se detectó Windows como plataforma.")
                directorio = None
                if os.path.exists("c:\\liquidsoap\\liquidsoap.exe"):
                    directorio = "c:\\liquidsoap"
                for path in os.environ.get('PATH', '').split(';'):
                    if os.path.exists(os.path.join(path, "liquidsoap.exe")) and not os.path.isdir(os.path.join(path, "liquidsoap.exe")):
                        self.debug(u"Se ubicó a liquidsoap en el directorio \""+path+"\".")
                        directorio = path
                if directorio == None:
                    self.debug(u"No se encontró el directorio de liquidsoap. Se establecerá el directorio de ejecución como el mismo de Gunther.")
                    directorio = "."
                self.debug(u"El directorio encontrado es \""+directorio+"\"")
                self.debug(u"Se ejecutará "+directorio + "\\" + self.__server_commandline + " -t -v \"" + sys.path[0].replace(self.__separador + "library.zip","")+self.__separador+self.__server_script + "\"")
                self.__server_subprocess = subprocess.Popen([directorio + "\\" + self.__server_commandline, "-t", "-v", sys.path[0].replace(self.__separador + "library.zip","")+self.__separador+self.__server_script], shell=False , cwd=directorio)
                self.debug(u"Ejecutado")
            else:
                self.debug(u"La plataforma NO es Windows.")
                #self.__server_subprocess = subprocess.Popen(["wine" , self.__server_commandline, "--enable-telnet", self.__server_script], shell=False , stdout=subprocess.PIPE)
                self.__server_subprocess = subprocess.Popen(["liquidsoap" , "--enable-telnet", "-v", self.__server_script], shell=False )#, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # aviso al sitio web de las transmisiones activas
            self.debug("Avisando al sitio web de las transmisiones activas")
            for outp in self.__outputs:
                try:
                    self.debug(outp.GetNombre())
                    outp.ActivateOnline()
                except Exception as e1:
                    self.debug("No se pudo activar online '"+outp.GetNombre()+"'")
                    raise e1
        except Exception as e:
            #raise Exception("Error al intentar ejecutar liquidsoap")
            raise e
            
        
    def DetenerServer(self):
        try:
            self.__server_subprocess.terminate()
            self.debug("Finalizando componentes...")
            for outp in self.__outputs:
                try:
                    self.debug(outp.GetNombre())
                    outp.Finalize()
                except Exception as e1:
                    self.debug(u"No se pudo desactivar '"+outp.GetNombre()+"'")
        except:
            self.debug(u"Error al intentar detener server. Se ignorará la excepción.")
            pass
    def GetCodigo(self):
        #print self.__inputs
        #print self.__outputs
        return self.__builder.GenerarCodigo(self.__inputs, self.__outputs)
    
    def GetXML(self):
        return self.__xml
    
    def GetDataTransmision(self):
        #data que más tarde uso para pasársela a los inputs y outputs
        tmpxml = self.__xml
        data = tmpxml.xpath("//data/*")
        ret = {}
        for campo in data:
            ret[campo.tag] = etree.tostring(campo,method="html").replace("<"+campo.tag+">","").replace("</"+campo.tag+">","")
        return ret
        
    
    def AgregarInput(self, a):
        self.__inputs.append(a)
        #persiste el valor del índice, para después usarlo al controlar el mixer
        self.__inputs[len(self.__inputs) - 1].setIndex(len(self.__inputs) - 1)
    def AgregarOutput(self, a):
        self.__outputs.append(a)
        
    def LoadXML(self, strXml):
        #dado un XML en formato ".gun", lee los inputs y outputs
        tmpxml = etree.XML(strXml)
        tmpref = self
        self.__xml = tmpxml #lo persisto para posibles futuros usos
        
        #primero los inputs
        xml_inputs = tmpxml.xpath("//input")
        for inp in xml_inputs:
            #necesito ubicar qué tipo de input es.
            tipo = inp.get("tipo")
            tmp_input = None
            
            #LISTA FIJA
            if tipo == "Lista Fija":
                archivos = []
                xml_archivos = inp.xpath("archivo")
                for a in xml_archivos:
                    archivos.append(a.get("nombre"))
                tmp_input = PlaylistEstatico("Lista Fija",tmpref, archivos, inp.get("random"), inp.get("loop"))
            
            #LISTA DINÁMICA
            if tipo == "Lista Dinamica":
                tmp_input = Playlist(inp.get("nombre"), tmpref)
            
            #MICROFONO
            if tipo == "Microfono":
                tmp_input = MicIn(inp.get("nombre"), tmpref)
            
            #TRANSMISION ONLINE
            if tipo == "Transmision Online":
                tmp_input = Stream(inp.get("nombre"),inp.get("url"), tmpref)
            
            if tmp_input != None:
                self.AgregarInput(tmp_input)
                
        #luego los outputs
        xml_outputs = tmpxml.xpath("//output")
        for out in xml_outputs:
            tipo = out.get("tipo")
            tmp_output = None
            
            #SERVIDOR REMOTO
            if tipo == "Servidor Remoto":
                tmp_output = Broadcast(out.get("nombre"), out.get("url"), out.get("contrasenia"), out.get("usuario"), out.get("puerto"), out.get("mountpoint"), out.get("formato"), tmpref)
            
            #SERVIDOR AUTOMATICO
            if tipo == "Servidor Automatico":
                print "Cargando servidores desde la web..."
                servers = GuntherLib.GetServersFromWeb(out.get("url"))
                print "...servidores cargados."
                servidor = servers[0]
                tmp = urlparse(servidor.get("url"))
                url = str(tmp.hostname)
                puerto = str(tmp.port)
                formato = "ogg"
                usuario = servidor.get("user_transmision")
                password = servidor.get("pass_transmision")
                mount = servidor.get("mount_point")
                tmp_output = Broadcast(servidor.get("nombre"), url, password, usuario, puerto, mount, formato, tmpref)
            
            
            #ARCHIVO
            if tipo == "Archivo":
                tmp_output = Archivo("Archivo de salida", out.get("nombre"), tmpref)
            
            #PARLANTES DE LA COMPUTADORA
            if tipo == "Parlantes":
                tmp_output = Soundcard("Parlantes", tmpref)
            
            if tmp_output != None:
                self.AgregarOutput(tmp_output)
