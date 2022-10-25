def extractParameters(message):
    msg = {}
    if "cam" in message: 
        msg = camParameters(message)
    elif "denm" in message:
        msg = denmParameters(message)

    return msg

def camParameters(message):
    msg = {}
    msg["stationID"]    = message["header"]["stationID"]
    msg["latitude"]     = message["cam"]["camParameters"]["basicContainer"]["referencePosition"]["latitude"] / 10000000
    msg["longitude"]    = message["cam"]["camParameters"]["basicContainer"]["referencePosition"]["longitude"] / 10000000
    msg["altitude"]     = message["cam"]["camParameters"]["basicContainer"]["referencePosition"]["altitude"]["altitudeValue"] / 100
    
    msg["heading"]      = message["cam"]["camParameters"]["highFrequencyContainer"][1]["heading"]["headingValue"] / 10

    if      msg["heading"] == 0:                                msg["heading"] = 90
    elif    msg["heading"] == 90:                               msg["heading"] = 0
    elif    msg["heading"] == 180:                              msg["heading"] = 270
    elif    msg["heading"] == 270:                              msg["heading"] = 180
    elif    msg["heading"] > 0      and msg["heading"] < 90:    msg["heading"] = -msg["heading"] % 90
    elif    msg["heading"] > 270    and msg["heading"] < 360:   msg["heading"] = (-msg["heading"] % 90) + 90
    elif    msg["heading"] > 180    and msg["heading"] < 270:   msg["heading"] = (-msg["heading"] % 90) + 180
    elif    msg["heading"] > 90     and msg["heading"] < 180:   msg["heading"] = (-msg["heading"] % 90) + 270

    msg["speed"]        = message["cam"]["camParameters"]["highFrequencyContainer"][1]["speed"]["speedValue"]/ 100
    msg["stationType"]  = message["cam"]["camParameters"]["basicContainer"]["stationType"]
    msg["proto"]        = "cam"

    msg["speed"] = round(msg["speed"], 2)
    msg["heading"] = round(msg["heading"], 2)

    return msg

def denmParameters(message):
    msg = {}
    msg["stationID"]    = message["header"]["stationID"]
    msg["latitude"]     = message["cam"]["camParameters"]["basicContainer"]["referencePosition"]["latitude"] / 10000000
    msg["longitude"]    = message["cam"]["camParameters"]["basicContainer"]["referencePosition"]["longitude"] / 10000000
    msg["altitude"]     = message["cam"]["camParameters"]["basicContainer"]["referencePosition"]["altitude"]["altitudeValue"]
    msg["heading"]      = message["cam"]["camParameters"]["highFrequencyContainer"][1]["heading"]["headingValue"]
    msg["speed"]        = message["cam"]["camParameters"]["highFrequencyContainer"][1]["speed"]["speedValue"]
    msg["stationType"]  = message["cam"]["camParameters"]["basicContainer"]["stationType"]
    msg["proto"] = "cam"

    return msg

def getImage(type, message):
    messageType = message["stationType"]
    if type == "cam":
        if      messageType == 1:       sourceImg = "Resources/img/cam/pedestrian.png"
        elif    messageType == 2:       sourceImg = "Resources/img/cam/bycicle.png"
        elif    messageType == 3:       sourceImg = "Resources/img/cam/moped.png"
        elif    messageType == 4:       sourceImg = "Resources/img/cam/motorcycle.png"
        elif    messageType == 5:       sourceImg = "Resources/img/cam/car.png"
        elif    messageType == 6:       sourceImg = "Resources/img/cam/bus.png"
        elif    messageType == 7:       sourceImg = "Resources/img/cam/lightTruck.png"
        elif    messageType == 8:       sourceImg = "Resources/img/cam/unknown.png"
        elif    messageType == 9:       sourceImg = "Resources/img/cam/trailer.png"
        elif    messageType == 10:      sourceImg = "Resources/img/cam/unknown.png"
        elif    messageType == 11:      sourceImg = "Resources/img/cam/tram.png"
        elif    messageType == 15:      sourceImg = "Resources/img/cam/rsu.png"
        else:                           sourceImg = "Resources/img/cam/unknown.png"

    return sourceImg


def getImage_list(type, message):
    messageType = message["stationType"]
    if type == "cam":
        if      messageType == 1:       sourceImg = "Resources/img/cam/list/pedestrian.png"
        elif    messageType == 2:       sourceImg = "Resources/img/cam/list/bycicle.png"
        elif    messageType == 3:       sourceImg = "Resources/img/cam/list/moped.png"
        elif    messageType == 4:       sourceImg = "Resources/img/cam/list/motorcycle.png"
        elif    messageType == 5:       sourceImg = "Resources/img/cam/list/car.png"
        elif    messageType == 6:       sourceImg = "Resources/img/cam/list/bus.png"
        elif    messageType == 7:       sourceImg = "Resources/img/cam/list/lightTruck.png"
        elif    messageType == 8:       sourceImg = "Resources/img/cam/unknown.png"
        elif    messageType == 9:       sourceImg = "Resources/img/cam/list/trailer.png"
        elif    messageType == 10:      sourceImg = "Resources/img/cam/unknown.png"
        elif    messageType == 11:      sourceImg = "Resources/img/cam/list/tram.png"
        elif    messageType == 15:      sourceImg = "Resources/img/cam/list/rsu.png"
        else:                           sourceImg = "Resources/img/cam/unknown.png"

    return sourceImg