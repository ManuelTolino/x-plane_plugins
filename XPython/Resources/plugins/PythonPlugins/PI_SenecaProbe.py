"""
PI_SENECAProbe.py

Simulador Seneca FNPT II

**Escuela Superior de Ingeniería**
**Universidad de Cádiz**

Envía por UDP coordenadas globales de punto superficie del terreno bajo el avión.
El paquete son 3 datos float, el segundo valor es el de la elevación del terreno.

25/02/2021
Autor: Manuel Tolino Contreras
"""

import os
import xp
from XPLMScenery import xplm_ProbeY
from XPLMGraphics import XPLMWorldToLocal, XPLMLocalToWorld
from XPLMScenery import XPLMCreateProbe, XPLMDestroyProbe, XPLMProbeTerrainXYZ
import socket
import struct

class PythonInterface:
    def XPluginStart(self):
        self.Name = "SenecaProbe"
        self.Sig = "Manuel Tolino C."
        self.Desc = "Envía por UDP coordenadas globales de punto superficie del terreno bajo el avión."

        #Crear probe
        self.probe = XPLMCreateProbe(xplm_ProbeY)

        # Datarefs de posición local del avión
        self.PlaneX = xp.findDataRef("sim/flightmodel/position/local_x")
        self.PlaneY = xp.findDataRef("sim/flightmodel/position/local_y")
        self.PlaneZ = xp.findDataRef("sim/flightmodel/position/local_z")

        #Función que se ejecuta cada 0.001 s
        xp.registerFlightLoopCallback(self.FlightLoopCallback, 0.01, 0)

        # Dirección y puerto para el socket
        # Debería ser la dirección de Dynamics
        self.localaddr = ("192.168.1.43", 19750)
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        return self.Name, self.Sig, self.Desc


    def XPluginStop(self):
        xp.unregisterFlightLoopCallback(self.FlightLoopCallback, 0)
        self.udp_socket.close()

    def XPluginEnable(self):
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return 1

    def XPluginDisable(self):
        self.udp_socket.close()
        pass

    def FlightLoopCallback(self, elapsedMe, elapsedSim, counter, refcon):

        #Obtener posición instantánea del avión
        x = xp.getDataf(self.PlaneX)
        y = xp.getDataf(self.PlaneY)
        z = xp.getDataf(self.PlaneZ)

        #Muestreo del terreno
        info = XPLMProbeTerrainXYZ(self.probe, x, y, z)

        #Posición en el globo de la colisión probeta-terreno
        (lat, lng, elev) = XPLMLocalToWorld(info.locationX, info.locationY, info.locationZ)

        paquete = [lat, elev, lng]
        send_msg = struct.pack( "3f" , *paquete)
        try:
            self.udp_socket.sendto(send_msg, self.localaddr)
        except:
            print("Fallo al enviar el mensaje")
            pass
        return 0.01