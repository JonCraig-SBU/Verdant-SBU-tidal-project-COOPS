import numpy as np
import warnings

def identifyTidalFlow(velMag, dir):
    """
    Algorithm:
     - Directions 180°-360° = flood tide (eastward flow, positive sign)
     - Directions 0°-180° = ebb tide (westward flow, negative sign)
    """

    # Ensures data type consistency
    velMag = np.asarray(velMag)
    dir = np.asarray(dir)

    if velMag.shape != dir.shape:
        raise ValueError("Velocity magnitude and direction vectors must be the same size")

    # Initialized arrays
    rowMag, colMag = velMag.shape
    binaryDir = np.zeros((rowMag, colMag))
    velMagSigned = np.zeros((rowMag, colMag))
    floodSign = np.zeros((rowMag, colMag), dtype=bool)
    ebbSign = np.zeros((rowMag, colMag), dtype=bool)

    for i in range(rowMag):
        for j in range(colMag):
            if 0 <= dir[i, j] and (dir[i, j] < 180 or dir[i, j] == 360):
                binaryDir[i, j] = -1
                ebbSign[i, j] = True
            elif 180 <= dir[i, j] < 360:
                binaryDir[i, j] = 1
                floodSign[i, j] = True

    # Exclusive vectors for ebb and flood
    floodVelMag = velMag * floodSign
    ebbVelMag = velMag * ebbSign

    floodVelDir = dir * floodSign
    ebbVelDir = dir * ebbSign

    # Preparation for principal flow
    floodVelMag_depthAvg = np.zeros((floodSign.shape[0], 1))
    floodVelDir_depthAvg = np.zeros((floodSign.shape[0], 1))
    ebbVelMag_depthAvg = np.zeros((ebbSign.shape[0], 1))
    ebbVelDir_depthAvg = np.zeros((ebbSign.shape[0], 1))
    floodSign_depthAvg = np.zeros((ebbSign.shape[0], 1))
    ebbSign_depthAvg = np.zeros((ebbSign.shape[0], 1))
    floodVelCount = 0
    ebbVelCount = 0

    for i in range(rowMag):
        for j in range(colMag):
            if floodSign[i, j]:
                floodVelMag_depthAvg[i] = floodVelMag_depthAvg[i] + velMag[i, j]
                floodVelDir_depthAvg[i] = floodVelDir_depthAvg[i] + dir[i, j]
                floodVelCount += 1
            elif ebbSign[i, j]:
                ebbVelMag_depthAvg[i] = ebbVelMag_depthAvg[i] + velMag[i, j]
                ebbVelDir_depthAvg[i] = ebbVelDir_depthAvg[i] + dir[i, j]
                ebbVelCount += 1
            else:
                warnings.warn(f"Tide at i = {i} and j = {j} is marked as neither ebb nor flood.\n")
                continue

        floodVelMag_depthAvg[i] = floodVelMag_depthAvg[i] / floodVelCount if floodVelCount != 0 else np.nan
        floodVelDir_depthAvg[i] = floodVelDir_depthAvg[i] / floodVelCount if floodVelCount != 0 else np.nan
        floodSign_depthAvg[i] = not np.isnan(floodVelDir_depthAvg[i])

        ebbVelMag_depthAvg[i] = ebbVelMag_depthAvg[i] / ebbVelCount if ebbVelCount != 0 else np.nan
        ebbVelDir_depthAvg[i] = ebbVelDir_depthAvg[i] / ebbVelCount if ebbVelCount != 0 else np.nan
        ebbSign_depthAvg[i] = not np.isnan(ebbVelDir_depthAvg[i])

        # Reset count for next row
        floodVelCount = 0
        ebbVelCount = 0

    floodSign_depthAvg = floodSign_depthAvg.astype(bool)
    ebbSign_depthAvg = ebbSign_depthAvg.astype(bool)
    velMagSigned = velMag * binaryDir

    return (floodVelMag, ebbVelMag, floodVelDir, ebbVelDir, floodVelMag_depthAvg,
            floodVelDir_depthAvg, ebbVelMag_depthAvg, ebbVelDir_depthAvg,
            floodSign, ebbSign, velMagSigned, ebbSign_depthAvg, floodSign_depthAvg)








