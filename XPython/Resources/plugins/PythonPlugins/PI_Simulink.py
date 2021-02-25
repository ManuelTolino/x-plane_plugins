import os
import xp
import socket
import struct
#import numpy
from XPLMGraphics import XPLMWorldToLocal

localaddr = ("127.0.0.1", 49003)
            
class PythonInterface:
    def XPluginStart(self):
        self.Name = "Simulink"
        self.Sig = "Manuel Tolino C."
        self.Desc = "Envía estados de la dinámica de la aeronave y posición. También posición en coordenadas locales de una baliza de referencia."

        # Open a file to write to.  We locate the X-System directory
        # and then concatenate our file name.  This makes us save in
        # the X-System directory.  Open the file.

        print("system path is {}".format(xp.getSystemPath()))
        self.outputPath = os.path.join(xp.getSystemPath(), "timedprocessing1.txt")
        self.OutputFile = open(self.outputPath, 'w')

        # Find the data refs we want to record.
        self.PlaneX = xp.findDataRef("sim/flightmodel/position/local_x")
        self.PlaneY = xp.findDataRef("sim/flightmodel/position/local_y")
        self.PlaneZ = xp.findDataRef("sim/flightmodel/position/local_z")
        self.Planelat = xp.findDataRef("sim/flightmodel/position/latitude")
        self.Planelon = xp.findDataRef("sim/flightmodel/position/longitude")
        self.Planealt = xp.findDataRef("sim/flightmodel/position/elevation")

        self.Planeu = xp.findDataRef("sim/flightmodel/position/indicated_airspeed")
        self.Planealpha = xp.findDataRef("sim/flightmodel/position/alpha")
        self.Planetheta = xp.findDataRef("sim/flightmodel/position/theta")
        self.Planeq = xp.findDataRef("sim/flightmodel/position/Qrad")

        self.Planebeta = xp.findDataRef("sim/flightmodel/position/beta")
        self.Planephi = xp.findDataRef("sim/flightmodel/position/phi")
        self.Planep = xp.findDataRef("sim/flightmodel/position/Prad")
        self.Planer = xp.findDataRef("sim/flightmodel/position/Rrad")

        """ Para Obtener la posición geográfica actual en el LOG
        Planelondat = xp.getDatad(self.Planelon)
        Planelatdat = xp.getDatad(self.Planelat)
        Planeelevdat = xp.getDatad(self.Planealt)
        print()
        print()
        print(Planelondat)
        print(Planelatdat)
        print(Planeelevdat)
        print()
        print()
        """

        self.latTEST = 36.7351732497892
        self.lonTEST = -6.064718923871927
        self.elevTEST = 29.045

        # Función bucle
        xp.registerFlightLoopCallback(self.FlightLoopCallback, 0.01, 0)

        #UDP Socket
        self.socketTx = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        return self.Name, self.Sig, self.Desc

    def XPluginStop(self):
        # Close Socket
        self.socketTx.close()
        # Unregister the callback
        xp.unregisterFlightLoopCallback(self.FlightLoopCallback, 0)

        # Close the file
        self.OutputFile.close()

    def XPluginEnable(self):
        return 1

    def XPluginDisable(self):
        pass

    def XPluginReceiveMessage(self, inFromWho, inMessage, inParam):
        pass

    def FlightLoopCallback(self, elapsedMe, elapsedSim, counter, refcon):
        # The actual callback.  First we read the sim's time and the data.
        elapsed = xp.getElapsedTime()
        PlaneXdat = xp.getDatad(self.PlaneX)
        PlaneYdat = xp.getDatad(self.PlaneY)
        PlaneZdat = xp.getDatad(self.PlaneZ)

        datPlaneu = xp.getDataf(self.Planeu)
        datPlanealpha = xp.getDataf(self.Planealpha)
        datPlanetheta =  xp.getDataf(self.Planetheta)
        datPlaneq=  xp.getDataf(self.Planeq)
        datPlanealt=  xp.getDatad(self.Planealt)

        datPlanebeta = xp.getDataf(self.Planebeta)
        datPlanephi = xp.getDataf(self.Planephi)
        datPlanep = xp.getDataf(self.Planep)
        datPlaner = xp.getDataf(self.Planer)

        (self.xbeacon, self.ybeacon, self.zbeacon) = XPLMWorldToLocal(self.latTEST, self.lonTEST, self.elevTEST)

        #vectAircraft = numpy.array([PlaneXdat, PlaneYdat, PlaneZdat])
        #vectBeacon = numpy.array([self.xbeacon, self.ybeacon, self.zbeacon])
        #relPosVect = vectAircraft - vectBeacon

        debugVector = [self.xbeacon,self.ybeacon,self.zbeacon,
                      PlaneXdat,PlaneYdat,PlaneZdat,
                      datPlaneu, datPlanealpha, datPlanetheta, datPlaneq, datPlanealt,
                      datPlanebeta, datPlanephi, datPlanep, datPlaner]

        # Write the data to a file.
        buf = "Time=%f, lat=%f,lon=%f,el=%f.\n" % (elapsed, PlaneXdat, PlaneYdat, PlaneZdat)
        # self.OutputFile.write(buf)
        try:
            #positions = [lat, lon, el]
            send_msg = struct.pack( "15f" , *debugVector)
            self.socketTx.sendto(send_msg, localaddr)
            #print("Message sent!")
        except:
            print("Unable to send message")
            pass
        # Return 1.0 to indicate that we want to be called again in 1 second.
        return 0.01
