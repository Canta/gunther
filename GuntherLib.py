# -*- coding: utf-8 -*-
import httplib, urllib, urlparse, json, urllib2, os
from cStringIO import StringIO

class Model(object):
    def __init__(self, obj):
        self.__obj = obj
    
    def get(self, campo):
        try:
            return str("".join(self.__obj["datos"]["fields"][campo.upper()]["data"]["valor"]))
        except Exception as e:
            return ""

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

def AddTransmision(url, nombre='Günther Stream', descripcion = 'RadioFyL Streaming', id_servidor = 0, id_formato_stream = 2):
    #a = 'url=http://giss.tv:8000/radiocefyl1.ogg&id_formato_stream=2&descripcion=testing&id_servidor=1'
    #a = 'url='+url+'&id_formato_stream='+str(id_formato_stream)+'&descripcion='+descripcion+'&id_servidor='+str(id_servidor)+"&nombre="+nombre
    data = {"url":url,"nombre":nombre,"descripcion":descripcion, "id_formato_stream":str(id_formato_stream), "id_servidor":str(id_servidor)}
    a = urllib.urlencode(data)
    #print 'http://www.radiofyl.com.ar/api/add_transmision.php?'+a
    b = GetJson('http://www.radiofyl.com.ar/api/add_transmision.api.php?'+a, 'get')
    return b

def FinalizeTransmision(jash):
    # c = 'hash='+str(b["data"]["hash"])
    c = 'hash='+jash
    d = GetJson('http://www.radiofyl.com.ar/api/finalize_transmision.api.php?'+c, 'get')
    return d

def GetServersFromWeb(url):
    #URL se supone que sea una dirección con la aplicación montada.
    #De ese modo, dada esa URL, se accede al api.
    if not url.endswith("/"):
        url = url + "/"
    url = url + "api/get_servidores_disponibles.api.php"
    servidores = []
    try:
        servidores = GetModels(url)
    except Exception as e:
        #print e.args
        #self.mostrar_error("El origen de datos no es válido :(")
        raise e
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
