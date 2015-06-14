__author__ = 'kevinis'
import csv
import sys
import matplotlib.pyplot as plt
import datetime
from dateutil import parser
import random
import math

def calcTemps (combos, atticTemp, outsideTemp, insideDate, electricityUsage):
    combo = combos[-1]
    calculatedTemp = []
    sqrerror_total = 0

    atticU = combo[0]
    outsideU = combo[1]
    intrinsicHeat = combo[2]
    tempPerKWattH = combo[3]

    calculatedTemp.append(insideTemp[0])
    index = 0
    for calcDate in insideDate[1:-1]:
        index = index + 1

        indexPrev = max(index-1,0)
        indexCurrent = min(index, len(insideDate)-1)

        atticTempAve = (atticTemp[indexPrev] + atticTemp[indexCurrent]) / 2
        atticDelta = atticTempAve - calculatedTemp[index-1]

        outsideTempAve = (outsideTemp[indexPrev] + outsideTemp[indexCurrent]) /2
        outsideDelta = outsideTempAve - calculatedTemp[indexPrev]

        hoursDelta = (insideDate[indexCurrent] - insideDate[indexPrev]) / 3600
        delta = ((atticDelta/atticU) + (outsideDelta/outsideU) + intrinsicHeat) * hoursDelta

        calculatedValue = calculatedTemp[indexPrev] + delta

        # add in the electrical component
        calculatedValue = calculatedValue + electricityUsage[indexCurrent] * hoursDelta * tempPerKWattH

        calculatedTemp.append(calculatedValue)

    for index in range(len(calculatedTemp)-1):
        err = insideTemp[index] - calculatedTemp[index]
        sqrerror_total = sqrerror_total + err * err

    combo.append(sqrerror_total)
    combo.append(calculatedTemp)

def interpolateArray(origTemps, origDates, insideDates):
    intValues = []
    origEarlierIndex = 0
    origLateIndex = 0

    summedValue = 0
    usingave = False

    for calcDate in insideDates:
        while (origEarlierIndex + 2) < len(origDates) and origDates[origEarlierIndex + 1] < calcDate:
            origEarlierIndex = origEarlierIndex + 1
        origLateIndex = origEarlierIndex + 1

        timeDelta = origDates[origLateIndex] - origDates[origEarlierIndex]

        laterWeight = (origDates[origLateIndex] - calcDate) / timeDelta
        weightedLaterTemp =  origTemps[origLateIndex] * laterWeight

        earlierWeight = (calcDate - origDates[origEarlierIndex]) / timeDelta
        weightedEarlierTemp =  origTemps[origEarlierIndex] * earlierWeight

        interpolatedValue = weightedLaterTemp + weightedEarlierTemp
        if (calcDate - origDates[origEarlierIndex]) > (3600 * 2): # for values that are too old, use the average value.
            interpolatedValue = summedValue / len(intValues)
            if not usingave :
                print "using ave value"
                usingave = True
        else:
            usingave = False

        summedValue = summedValue + interpolatedValue
        intValues.append(interpolatedValue)

    return intValues

def readTemps():
    f = open('/Users/kevinis/Downloads/weather_data.csv', 'rt')
    pg = open('/Users/kevinis/Downloads/pge_electric.csv', 'rt')
    try:
        reader = csv.reader(f)
        pg_reader = csv.reader(pg)
        atticDate = []
        atticTemp = []
        insideTemp = []
        insideDate = []
        outsideTemp = []
        outsideDate = []
        for row in reader:
            if len(row) == 0:
                continue
            if (row[2] == "Attic"):
                date = (parser.parse(row[0])-datetime.datetime(1970,1,1)).total_seconds()
                atticDate.append(date)
                atticTemp.append(int(row[4]))
            if (row[2] == "Inside"):
                date = (parser.parse(row[0])-datetime.datetime(1970,1,1)).total_seconds()
                insideDate.append(date)
                insideTemp.append(int(row[4]))
            if (row[2] == "outside"):
                date = (parser.parse(row[0])-datetime.datetime(1970,1,1)).total_seconds()
                outsideDate.append(date)
                outsideTemp.append(int(row[4]))

        firstDate = max([atticDate[0], insideDate[0], outsideDate[0]]);
        lastDate = min([atticDate[-1], insideDate[-1], outsideDate[-1]]);

        while (insideDate[0] < firstDate):
            insideDate = insideDate[1:]
            insideTemp = insideTemp[1:]
        while (atticDate[0] < firstDate):
            atticDate = atticDate[1:]
            atticTemp = atticTemp[1:]
        while (outsideDate[0] < firstDate):
            outsideDate = outsideDate[1:]
            outsideTemp = outsideTemp[1:]

        while (insideDate[-1] > lastDate):
            insideDate = insideDate[0:-1]
            insideTemp = insideTemp[0:-1]
        while (atticDate[-1] > lastDate):
            atticDate = atticDate[0:-1]
            atticTemp = atticTemp[0:-1]
        while (outsideDate[-1] > lastDate):
            outsideDate = outsideDate[0:-1]
            outsideTemp = outsideTemp[0:-1]

        atticTemp = interpolateArray(atticTemp, atticDate, insideDate)
        outsideTemp = interpolateArray(outsideTemp, outsideDate, insideDate)

        electricityUsage = []
        electricityDate = []
        for row in pg_reader:
            if len(row) == 0:
                continue
            if row[0] == "Electric usage":
                usageTime = (parser.parse(row[1] + " " + row[2])-datetime.datetime(1970,1,1)).total_seconds()
                electricityUsage.append(float(row[4]))
                electricityDate.append(usageTime)

        electricityUsage = interpolateArray(electricityUsage, electricityDate, insideDate)
    finally:
        f.close()
        pg.close()

    return (atticTemp, outsideTemp, insideTemp, insideDate, electricityUsage)



atticTemp, outsideTemp, insideTemp, times, electricityUsage = readTemps()

combos = []
tries = 2000

combos = [[136.14047563817485, 75.18603614236163, 0.10293318203202655, 0.01580911358299062]]
calcTemps(combos, atticTemp, outsideTemp, times, electricityUsage)

previousError = combos[-1][4]

best = combos[-1][0:4]
print best
index = random.randint(0,2)
for i in range(tries):
    # calculate and save.
    calcTemps(combos, atticTemp, outsideTemp, times, electricityUsage)
    print combos[-1][0:5]

    err = combos[-1][4]

    if ( err < previousError ) :
         print "        better"
         best = combos[-1][0:4]
         previousError = err

    newCombo = best[0:4]

    for index in range(4):
        newCombo[index] = newCombo[index] + newCombo[index] * math.pow(10,random.randint(-3,-1)) * random.randint(-1,1)

    combos.append(newCombo)


best = combos[0]
for combo in combos[:-1]:
    if combo[4] < best[4]:
        best = combo

print best[0],best[1],best[2],best[3],best[4]

print best[0:4]

plt.plot(times, atticTemp)
plt.plot(times, insideTemp)
plt.plot(times, outsideTemp)
plt.plot(times[:-1], best[5])

for index, value in enumerate(electricityUsage):
    electricityUsage[index] = (value * 10) + 30
plt.plot(times, electricityUsage)
plt.show()

