"""
TimedProcessing.c

Ported to Python by Sandy Barbour - 28/04/2005
Ported to XPPython3 by Peter Buckner - 2-Aug-2020

This example plugin demonstrates how to use the timed processing callbacks
to continuously record sim data to disk.

This technique can be used to record data to disk or to the network.  Unlike
UDP data output, we can increase our frequency to capture data every single
sim frame.  (This example records once per second.)

Use the timed processing APIs to do any periodic or asynchronous action in
your plugin.
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

        self.Planelat = xp.findDataRef("sim/flightmodel/position/latitude")
        self.Planelon = xp.findDataRef("sim/flightmodel/position/longitude")
        self.Planealt = xp.findDataRef("sim/flightmodel/position/elevation") 

        self.Planephi = xp.findDataRef("sim/flightmodel/position/phi")
        self.Planetheta = xp.findDataRef("sim/flightmodel/position/theta")
        self.Planepsi = xp.findDataRef("sim/flightmodel/position/psi")

        self.PlaneOverride = xp.findDataRef("sim/operation/override/override_planepath")
        print("Iniciando")


        # Socket Tx
        self.dynamicsAddr = ("192.168.1.43", 19777)
        # Socket Rx
        self.dirIP = "0.0.0.0"
        self.addrPort = 19777
        self.bufferSize = 1024
        self.allAddr = (self.dirIP, self.addrPort)
        self.socketTx = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socketTx.bind(self.allAddr)
        self.socketTx.settimeout(0.001)

        #self.socketRxPos = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        overrideList = [0] * 20
        overrideList[0] = 1
        xp.setDatavi(self.PlaneOverride, overrideList,0,20)

        #Función que se ejecuta cada 0.001 s
        #xp.registerFlightLoopCallback(self.FlightLoopCallback, 0.05, 0)
        xp.registerFlightLoopCallback(self.FlightLoopCallback, 0.005, 0)
        return self.Name, self.Sig, self.Desc

    def XPluginStop(self):
        xp.unregisterFlightLoopCallback(self.FlightLoopCallback, 0)
        self.socketTx.close()
        #self.socketTx.close()
        overrideList = [0] * 20
        overrideList[0] = 0
        xp.setDatavi(self.PlaneOverride, overrideList,0,20)

    def XPluginEnable(self):
        #Variables de prueba para posicionar avion
        self.latTEST = 36.7351732497892
        self.lonTEST = -6.064718923871927
        self.elevTEST = 40.045
        # RX y TX
        #self.socketRxPos = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        #self.socketRxPos.bind((self.dirIP, self.addrPort))
        overrideList = [0] * 20
        overrideList[0] = 1
        xp.setDatavi(self.PlaneOverride, overrideList,0,20)
        return 1

    def XPluginDisable(self):
        self.socketTx.close()
        #self.socketTx.close()

        overrideList = [0] * 20
        overrideList[0] = 0
        xp.setDatavi(self.PlaneOverride, overrideList,0,20)
        pass

    def XPluginReceiveMessage(self, inFromWho, inMessage, inParam):
        pass

    def FlightLoopCallback(self, elapsedMe, elapsedSim, counter, refcon):
        #            print("Llamada callback")
        try:
            #           print("ComienzoBucle")
            #self.socketRxPos.connect((self.dirIP, self.addrPort))
            # RX de Bytes para posición del avión
            msgFromClient       = "Hello UDP Server"
            bytesToSend         = str.encode(msgFromClient)
            #self.socketTx.sendto(bytesToSend, self.dynamicsAddr)
            #self.socketTx.settimeout(0.01)
            bytesAddressPair = self.socketTx.recvfrom(self.bufferSize)
            Rx_message = bytesAddressPair[0]
            # address = bytesAddressPair[1] - Dirección del emisor
            recv_msg_decode = struct.unpack("dddfff", Rx_message)
            #    print(recv_msg_decode)
            # Conversion a coordenadas OpenGL (locales)
            (xpos, ypos, zpos) = XPLMWorldToLocal(recv_msg_decode[0], recv_msg_decode[1], recv_msg_decode[2])
            # Mover avion
            xp.setDatad(self.PlaneX, xpos)
            xp.setDatad(self.PlaneY, ypos)
            xp.setDatad(self.PlaneZ, zpos)
            xp.setDataf(self.Planephi, recv_msg_decode[3])
            xp.setDataf(self.Planetheta, recv_msg_decode[4])
            xp.setDataf(self.Planepsi, recv_msg_decode[5])
        except:
            #     print("ERROR")
            pass
            #Muestreo del terreno
            #info = XPLMProbeTerrainXYZ(self.probe, xpos, ypos, zpos)
            #print(info.locationZ)
            #(lat, lng, elev) = XPLMLocalToWorld(info.locationX, info.locationY, info.locationZ)
            #paqueteTx = [lat, elev, lng]
            #paqueteTx = [1,1,1]
            
            # Tx Feedback de elevación del terreno
            #try:
            #    Tx_msg = struct.pack( "3f" , *paqueteTx)
            #    self.socketTx.sendto(Tx_msg, self.dynamicsAddr)
            #except:
            #    print("Error de envio")
            #    pass
        return 0.005
