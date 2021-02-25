"""
PI_SENECAPos.py

Simulador Seneca FNPT II

**Escuela Superior de Ingeniería**
**Universidad de Cádiz**

Plugin para recibir datos de Dynamics y representar la aeronave en vuelo.
Ajustar la IP y el puerto correspondiente.

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
        self.Name = "Seneca - Visual"
        self.Sig = "Manuel Tolino C."
        self.Desc = "Recepción de datos de Dynamics y posicionamiento de la aeronave"

        # Probe para obtener elevación del terreno
        self.probe = XPLMCreateProbe(xplm_ProbeY)

        # Datarefs de posición local del avión
        self.PlaneX = xp.findDataRef("sim/flightmodel/position/local_x")
        self.PlaneY = xp.findDataRef("sim/flightmodel/position/local_y")
        self.PlaneZ = xp.findDataRef("sim/flightmodel/position/local_z")

        # Datarefs de orientación local del avión
        self.Planephi = xp.findDataRef("sim/flightmodel/position/phi")
        self.Planetheta = xp.findDataRef("sim/flightmodel/position/theta")
        self.Planepsi = xp.findDataRef("sim/flightmodel/position/psi")

        self.PlaneOverride = xp.findDataRef("sim/operation/override/override_planepath")
        print("Iniciando")

        # Socket Rx
        self.dirIP = "0.0.0.0"
        #self.dirIP = "192.168.1.43"
        self.addrPort = 19777
        self.bufferSize = 64
        self.allAddr = (self.dirIP, self.addrPort)

        # Desactivar motor de físicas de XPlane
        overrideList = [0] * 20
        overrideList[0] = 1
        xp.setDatavi(self.PlaneOverride, overrideList,0,20)

        #Función bucle que se ejecuta cada 0.005 s
        xp.registerFlightLoopCallback(self.FlightLoopCallback, 0.01, 0)
        return self.Name, self.Sig, self.Desc

    def XPluginStop(self):
        # Vuelve a activar las físicas de XPlane (debería)
        xp.unregisterFlightLoopCallback(self.FlightLoopCallback, 0)
        self.socketTx.close()
        overrideList = [0] * 20
        overrideList[0] = 0
        xp.setDatavi(self.PlaneOverride, overrideList,0,20)

    def XPluginEnable(self):
        # Desactivar motor de físicas de XPlane
        overrideList = [0] * 20
        overrideList[0] = 1
        xp.setDatavi(self.PlaneOverride, overrideList,0,20)
        return 1

    def XPluginDisable(self):
        # Vuelve a activar las físicas de XPlane (debería)
        self.socketTx.close()
        overrideList = [0] * 20
        overrideList[0] = 0
        xp.setDatavi(self.PlaneOverride, overrideList,0,20)
        pass

    def XPluginReceiveMessage(self, inFromWho, inMessage, inParam):
        pass

    """
    Bucle función principal, el valor de return
    es el tiempo que solicita llamarse de nuevo, debería ser
    mayor que el timeout del socket.
    """
    def FlightLoopCallback(self, elapsedMe, elapsedSim, counter, refcon):
        try:
            self.socketTx = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socketTx.bind(self.allAddr)
            bytesAddressPair = self.socketTx.recvfrom(self.bufferSize)
            self.socketTx.settimeout(0.009)
            Rx_message = bytesAddressPair[0]
            self.socketTx.close()
            # address = bytesAddressPair[1] - Dirección del emisor
            recv_msg_decode = struct.unpack("dddfff", Rx_message)
            # Conversion a coordenadas OpenGL (locales)
            (xpos, ypos, zpos) = XPLMWorldToLocal(recv_msg_decode[0], recv_msg_decode[1], recv_msg_decode[2])
            # Mover avion:
            xp.setDatad(self.PlaneX, xpos)
            xp.setDatad(self.PlaneY, ypos)
            xp.setDatad(self.PlaneZ, zpos)
            xp.setDataf(self.Planephi, recv_msg_decode[3])
            xp.setDataf(self.Planetheta, recv_msg_decode[4])
            xp.setDataf(self.Planepsi, recv_msg_decode[5])
        except:
            self.socketTx.close()
            #     print("ERROR")  DEBUG
            pass
        return 0.01