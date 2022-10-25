import time
import binascii


'''
Function: GenerateCamMessage
Args:   Latitude
        Longitude
        Altitude
        camAsn: File to be used to encode CAM messages according to ASN1tools
    
Return: CAM encoded
'''

class GenerateMessage():
    latitude = 0
    longitude = 0
    altitude = 0
    camAsn = None
    station_id = 0

    heading = None
    speed = None

    flag = False

    index = 0

    def __init__(self, camAsn, lat, lon, heading, information):

        self.latitude = lat
        self.longitude = lon
        self.heading = heading
        self.station_id = information["stationId"]
        self.speed = information["speed"]

        self.camAsn = camAsn

    def message(self):

        # Basic Container

        stationType = 5

        # Basic Container - ReferencePosition

        semiMajorConfidence = 10 
        semiMinorConfidence = 10
        semiMajorOrientation =  10

        PositionConfidenceEllipse = {
            "semiMajorConfidence" : semiMajorConfidence,
            "semiMinorConfidence" : semiMinorConfidence,
            "semiMajorOrientation" : semiMajorOrientation
        }

        altitudeValue = 10
        altitudeConfidence = "alt-000-01"

        Altitude = {
            "altitudeValue" : int(altitudeValue),
            "altitudeConfidence" : altitudeConfidence
        }

        ReferencePosition = {
            "latitude" : int(self.latitude),
            "longitude" : int(self.longitude),
            "positionConfidenceEllipse" : PositionConfidenceEllipse,
            "altitude" : Altitude
        }

        BasicContainer = {
            "stationType" : stationType,
            "referencePosition" : ReferencePosition
        }

        # BasicVehicleContainerHighFrequency

        if stationType == 15 :

            # RSUContainerHighFrequency

            ProtectedCommunicationZonesRSU = {}

            RSUContainerHighFrequency = {
                "protectedCommunicationZoneRSU" : ProtectedCommunicationZonesRSU
            }

            HighFrequencyContainer = ("rsuContainerHighFrequency", RSUContainerHighFrequency)

        else : 
            headingValue = 0
            headingConfidence = 1

            Heading = {
                "headingValue" : self.heading,
                "headingConfidence" : headingConfidence
            }

            speedValue = 0
            speedConfidence = 1

            Speed = {
                "speedValue" : self.speed,
                "speedConfidence" : speedConfidence
            }

            driveDirection = "forward"

            vehicleLengthValue = 6000
            vehicleLengthConfidenceIndication = "noTrailerPresent"

            VehicleLength = {
                "vehicleLengthValue" : vehicleLengthValue,
                "vehicleLengthConfidenceIndication" : vehicleLengthConfidenceIndication
            }

            vehicleWidth = 40
            
            longitudinalAccelerationValue = 0
            longitudinalAccelerationConfidence = 1

            LongitudinalAcceleration = {
                "longitudinalAccelerationValue" : longitudinalAccelerationValue,
                "longitudinalAccelerationConfidence" :longitudinalAccelerationConfidence
            }

            curvatureValue = 0
            curvatureConfidence = "unavailable"

            Curvature = {
                "curvatureValue" : curvatureValue,
                "curvatureConfidence" : curvatureConfidence
            }

            curvatureCalculationMode = "yawRateNotUsed"

            yawRateValue = 0
            yawRateConfidence = "unavailable"

            YawRate = {
                "yawRateValue" : yawRateValue,
                "yawRateConfidence" : yawRateConfidence
            }

            accelerationControl = (bytes([0,0,0,0,0,0,0]), 7)

            lanePosition = 1

            steeringWheelAngleValue = 0
            steeringWheelAngleConfidence = 1

            SteeringWheelAngle = {
                "steeringWheelAngleValue" : steeringWheelAngleValue,
                "steeringWheelAngleConfidence" : steeringWheelAngleConfidence
            }

            lateralAccelerationValue = 0
            lateralAccelerationConfidence = 1

            LateralAcceleration = {
                "lateralAccelerationValue" : lateralAccelerationValue,
                "lateralAccelerationConfidence" : lateralAccelerationConfidence
            }

            verticalAccelerationValue = 0
            verticalAccelerationConfidence = 1

            VerticalAcceleration = {
                "verticalAccelerationValue" : verticalAccelerationValue,
                "verticalAccelerationConfidence" : verticalAccelerationConfidence
            }

            performanceClass = 0

            protectedZoneLatitude = 0
            protectedZoneLongitude = 0
            cenDsrcTollingZoneID = 0

            CenDsrcTollingZone = {
                "protectedZoneLatitude" : protectedZoneLatitude,
                "protectedZoneLongitude" : protectedZoneLongitude,
                "cenDsrcTollingZoneID" : cenDsrcTollingZoneID #Optional
            }

            # High Frequency Container

            BasicVehicleContainerHighFrequency = {
                "heading" : Heading,
                "speed" : Speed,
                "driveDirection" : driveDirection,
                "vehicleLength" : VehicleLength,
                "vehicleWidth" : vehicleWidth,
                "longitudinalAcceleration" : LongitudinalAcceleration,
                "curvature" : Curvature,
                "curvatureCalculationMode" : curvatureCalculationMode,
                "yawRate" : YawRate,
                "accelerationControl" : accelerationControl,                 #OPTIONAL
                "lanePosition" : lanePosition,                               #OPTIONAL
                "steeringWheelAngle" : SteeringWheelAngle,                   #OPTIONAL
                "lateralAcceleration" : LateralAcceleration,                 #OPTIONAL
                "verticalAcceleration" : VerticalAcceleration,               #OPTIONAL
                "performanceClass" : performanceClass,                       #OPTIONAL
                "cenDsrcTollingZone" : CenDsrcTollingZone                    #OPTIONAL
            }

            HighFrequencyContainer = ("basicVehicleContainerHighFrequency", BasicVehicleContainerHighFrequency)

        # BasicVehicleContainerLowFrequency

        vehicleRole = "default"
        
        exteriorLights = (bytes([0,0,0,0,0,0,0,0]), 0)

        deltaLatitude = 0
        deltaLongitude = 0
        deltaAltitude = 0

        PathPosition = {
            "deltaLatitude" : deltaLatitude,
            "deltaLongitude" : deltaLongitude,
            "deltaAltitude" : deltaAltitude
        }

        pathDeltaTime = 10

        PathPoint = {
            "pathPosition" : PathPosition,
            "pathDeltaTime" : pathDeltaTime
        }

        PathHistory = [PathPoint]


        BasicVehicleContainerLowFrequency = {
            "vehicleRole" : vehicleRole,
            "exteriorLights" : exteriorLights,
            "pathHistory" : PathHistory
        }

        LowFrequencyContainer = ("basicVehicleContainerLowFrequency", BasicVehicleContainerLowFrequency)

        #  SpecialVehicleContainer

        #SpecialVehicleContainer = ("", null)
        containerFlag = False

        if vehicleRole == "publicTransport":
            # PublicTransportContainer

            containerFlag = True

            embarkationStatus = False

            ptActivationType = 0
            ptActivationData = bytes([0, 0])

            PtActivation = {
                "ptActivationType" : ptActivationType,
                "ptActivationData" : ptActivationData
            }

            PublicTransportContainer = {
                "embarkationStatus": embarkationStatus,
                "ptActivation" : PtActivation
            }

            SpecialVehicleContainer = ("publicTransportContainer" , PublicTransportContainer)

        elif vehicleRole == "specialTransport":
            # SpecialTransportContainer
            containerFlag = True

            specialTransportType = (bytes([0,0,0,0]), 0)
            lightBarSirenInUse = (bytes([0,0]),0)

            SpecialTransportContainer = {
                "specialTransportType" : specialTransportType,
                "lightBarSirenInUse" : lightBarSirenInUse
            }

            SpecialVehicleContainer = ("specialTransportContainer" , SpecialTransportContainer)

        elif(vehicleRole =="dangerousGoods"):
            # DangerousGoodsContainers
            containerFlag = True

            dangerousGoodsBasic = "explosives1"

            DangerousGoodsContainer = {
                "dangerousGoodsBasic" : dangerousGoodsBasic
            }

            SpecialVehicleContainer = ("dangerousGoodsContainer" , DangerousGoodsContainer)

        elif(vehicleRole == "roadWork"):
            # RoadWorksContainerBasic
            containerFlag = True

            roadWorksSubCauseCode = 0
            lightBarSirenInUse = (bytes([0,0]),0)

            innerhardShoulderStatus = "availableForStopping"
            outterhardShoulderStatus = "availableForStopping"
            drivingLaneStatus = (bytes([0,0]),0)


            ClosedLanes = {
                "innerhardShoulderStatus" : innerhardShoulderStatus,
                "outterhardShoulderStatus" : outterhardShoulderStatus,
                "drivingLaneStatus" : drivingLaneStatus
            }

            RoadWorksContainerBasic = {
                "roadWorksSubCauseCode" : roadWorksSubCauseCode,
                "lightBarSirenInUse" : lightBarSirenInUse,
                "closedLanes" : ClosedLanes
            }

            SpecialVehicleContainer = ("roadWorksContainerBasic" , RoadWorksContainerBasic)
        
        elif(vehicleRole == "rescue"):

            # RescueContainer
            containerFlag = True

            lightBarSirenInUse = (bytes([0,0]),0)

            RescueContainer = {
                "lightBarSirenInUse" : lightBarSirenInUse
            }

            SpecialVehicleContainer = ("rescueContainer" , RescueContainer)

        elif(vehicleRole == "emergency"):

            # EmergencyContainer
            containerFlag = True

            lightBarSirenInUse = (bytes([0,0]),0)
            emergencyPriority = (bytes([0,0]),0)

            causeCodeType = 0
            subCauseCodeType = 0

            IncidentIndication = {
                "causeCode" : causeCodeType,
                "subCauseCode" : subCauseCodeType
            }


            EmergencyContainer = {
                "lightBarSirenInUse" : lightBarSirenInUse,
                "incidentIndication" : IncidentIndication,
                "emergencyPriority" : emergencyPriority
            }

            SpecialVehicleContainer = ("emergencyContainer" , EmergencyContainer)

        elif vehicleRole == "safetyCar":

            # SafetyContainer
            containerFlag = True

            lightBarSirenInUse = (bytes([0,0]), 0)

            causeCode = 0
            subCauseCode = 0

            trafficRule = "noPassing"
            speedLimit = 100

            IncidentIndication = {
                "causeCode" : causeCode,
                "subCauseCode" : subCauseCode
            }

            SafetyContainer = {
                "lightBarSirenInUse" : lightBarSirenInUse,
                "incidentIndication" : IncidentIndication,
                "trafficRule" : trafficRule,
                "speedLimit" : speedLimit
            }

            SpecialVehicleContainer = ("safetyCarContainer" , SafetyContainer)

        

        if containerFlag:
            CamParameters = {
                "basicContainer" : BasicContainer, 
                "highFrequencyContainer" : HighFrequencyContainer,
                "lowFrequencyContainer" : LowFrequencyContainer,    # Optional
                "specialVehicleContainer" : SpecialVehicleContainer # Optional
            }
        else :
            CamParameters = {
                "basicContainer" : BasicContainer, 
                "highFrequencyContainer" : HighFrequencyContainer,
                "lowFrequencyContainer" : LowFrequencyContainer    # Optional
            }

            
        # ItsPduHeader

        protocolVersion = 2
        messageID = 2
        stationID = self.station_id

        # CoopAwareness 

        generationDeltaTime = int((time.time()*1000) % 65535)

        # Campos da mensagem CAM

        ItsPduHeader = {"protocolVersion" : protocolVersion, "messageID" : messageID, "stationID" : stationID}

        CoopAwareness = {"generationDeltaTime" : generationDeltaTime, "camParameters" : CamParameters}

        # Mensagem CAM

        cam = { "header" : ItsPduHeader, "cam" : CoopAwareness } 

        message = self.camAsn.encode("CAM", cam)

        return binascii.hexlify(message).decode('ascii')