# -*- coding: utf-8 -*-
import httplib, urllib, urlparse, json, urllib2, os, sys
from cStringIO import StringIO

class Model(object):
    def __init__(self, obj):
        self.__obj = obj
        self.datos = obj["datos"]
    
    def get(self, campo):
        try:
            return str("".join(self.__obj["datos"]["fields"][campo.upper()]["data"]["valor"]))
        except Exception as e:
            return ""

def GetMyDocuments():
    if "win" in sys.platform:
        dll = ctypes.windll.shell32
        buf = ctypes.create_string_buffer(300)
        dll.SHGetSpecialFolderPathA(None, buf, 0x0005, False)
        return buf.value
    else:
        return os.path.expanduser("~")

def GetJson(url, method = 'get', data = '', headers = {}):
    resp = GetURL(url, method, data, headers)    
    return json.load(resp)

def GetURL(url, method = 'get', data = None, headers = {}):
    if (method.lower() == 'post'):
        #si es post, agrego el header de form
        esta_el_header = False
        for a in headers:
            if "content-type" in a[0].lower() and "form-urlencoded" in a[1].lower():
                esta_el_header = True
        if esta_el_header == False:
            headers.update({"Content-type": "application/x-www-form-urlencoded"})
    
    tmp = urlparse.urlparse(url)
    h = None
    if "https" in url:
        h = httplib.HTTPSConnection(tmp.hostname)
    else:
        h = httplib.HTTPConnection(tmp.hostname)
    
    h.request(method.upper(), tmp.path + "?" + tmp.query, data, headers)
    resp = h.getresponse()
    #print resp.status
    #print resp.reason
    return resp

def GetModels(url , method = 'get', data = ''):
    j = GetJson(url,method,data)
    r = [Model(i) for i in j]
    return r

def ParseModels(arr):
    r = [Model(i) for i in arr]
    return r

def PrepareURLForAPI(url):
    if not url.endswith("/"):
        url = url + "/"
    if not "api/index.php" in url:
        url = url + "api/index.php"
    return url

def AddTransmision(url, nombre='Günther Stream', descripcion = 'RadioFyL Streaming', id_servidor = 0, id_formato_stream = 2, host="http://www.radiofyl.com.ar/"):
    #a = 'url=http://giss.tv:8000/radiocefyl1.ogg&id_formato_stream=2&descripcion=testing&id_servidor=1'
    #a = 'url='+url+'&id_formato_stream='+str(id_formato_stream)+'&descripcion='+descripcion+'&id_servidor='+str(id_servidor)+"&nombre="+nombre
    data = {"verb":"add_transmision","url":url,"nombre":nombre,"descripcion":descripcion, "id_formato_stream":str(id_formato_stream), "id_servidor":str(id_servidor)}
    a = urllib.urlencode(data)
    #print 'http://www.radiofyl.com.ar/api/add_transmision.php?'+a
    #b = GetJson(host+'api/index.php?'+a, 'get')
    host = PrepareURLForAPI(host)
    b = API(data, host).Call()
    if b.success:
        return b.data
    else:
        return {"hash":""}

def FinalizeTransmision(jash, url="http://www.radiofyl.com.ar/"):
    # c = 'hash='+str(b["data"]["hash"])
    url = PrepareURLForAPI(url)
    c = {'hash':jash,"verb":"finalize_transmision"}
    #d = GetJson(url+'api/index.php?'+c, 'get')
    d = API(c, url).Call()
    return d

def GetServersFromWeb(url="http://www.radiofyl.com.ar/"):
    #URL se supone que sea una dirección con la aplicación montada.
    #De ese modo, dada esa URL, se accede al api.
    url = PrepareURLForAPI(url)
    servidores = []
    #try:
    r = API({"verb":"get_servidores_disponibles"},url).Call()
    if r.success:
        for s in r.data["servidores"]:
            servidores.append(s)
    else:
        print "GetServersFromWeb: " + r.data["message"]
    #except Exception as e:
        #print e.args
        #self.mostrar_error("El origen de datos no es válido :(")
        #raise e
    return servidores


def ParseIcecastMetadata(meta, mountpoint):
    secciones = meta.split("<div class=\"roundtop\">")
    ret = []
    seccion = None
    for seccion in secciones:
        if mountpoint in seccion:
            break
    
    if seccion != None:
        #encontró la sección con el mountpoint.
        #ahora separo las propiedades
        tprops = seccion.split("<table border=\"0\" cellpadding=\"4\">")
        props = tprops[1].split("<tr>")
        for prop in props:
            p = prop.split("</tr>")
            p = p[0].replace("<td>","").replace("</td>","").split("<td class=\"streamdata\">")
            ret.append(p)
    return ret

class APIResponse(object):
    def __init__(self, success=True, message="Operation finished"):
        self.success = (success == True)
        self.data = {"message":message}

    def Fail(message = "Operation failed."):
        return APIResponse(False, message)
    Fail = staticmethod(Fail)
    
    def Parse(json = {}):
        ar = None
        try:
            ar = APIResponse(json["success"])
            ar.data = json["data"]
        except:
            ar = APIResponse.Fail("APIResponse.Parse: invalid json object")
        return ar
    Parse = staticmethod(Parse)

class API(object):
    def __init__(self,data={}, endpoint = "http://localhost/api/"):
        try:
            data["verb"] = data["verb"]
        except:
            raise(Exception("API Class: a verb is required in the data dict."))
        self.response = APIResponse.Fail("Operation not executed")
        self.data = data
        self.endpoint = endpoint

    def Call(self, success=None, fail=None):
        import simplejson
        #print "endpoint:" + self.endpoint
        try:
            #resp = GetURL(self.endpoint,"post",urllib.urlencode(self.data))
            #print "resp:"
            #print resp
            #resp = resp.read()
            #print "resp string:"
            #print resp
            #json = simplejson.loads(resp)
            #print "json:"
            #print json
            self.response = APIResponse.Parse(GetJson(self.endpoint,"post",urllib.urlencode(self.data)))
        except Exception as e:
            print "API.Call:"
            print e
            pass
        for item in self.response.data:
            try:
                self.response.data[item] = simplejson.loads(self.response.data[item])
            except Exception as e:
                pass
        return self.response

