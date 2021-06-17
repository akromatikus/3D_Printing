"""
Created on Wed Jun  9 21:04:48 2021

@author: akromatikus

Copyright (c) 2021 akromatikus

"""

import math
from ..Script import Script
from cura.Settings.ExtruderManager import ExtruderManager
 
class AdaptiveRetraction(Script):
    
    #JSON Parameters
    def getSettingDataString(self):
        return """{
            "name": "Adaptive Retraction",
            "key": "AdaptiveRetraction",
            "metadata": {},
            "version": 2,
            "settings":
            {               
                "slope":
                {
                    "label": "Slope Steepness",
                    "description": "The steepness of the retraction distance per travel distance curve",
                    "type": "float",
                    "default_value": 4
                },
                
                "horizontal_shift":
                {
                    "label": "Horizontal Shift",
                    "description": "Controls when the most significant part of the retraction/travel curve takes place",
                    "type": "float",
                    "default_value": 3
                },
                
                "lower_stretch":
                {
                    "label": "Lower Stretch",
                    "description": "Increases or decreases retraction distance (up to the max set in Cura's profile settings), with longer travel moves being affected more than shorter ones",
                    "type": "float",
                    "default_value": 4
                }                                              
            }
        }"""
    
    #searches line for the desired string. If not found, countStep (int) will tell combLines to either search the next line or previous lines   
    def combLines(self, lineArray, linDat, linDex, strToFind, countStep, datOrDex):
        while linDat.count(strToFind) < 1 or linDat.count('Z') > 0:
            linDex += countStep
            linDat = lineArray[linDex]
        if datOrDex == 'dat':
            linDat += (' ')
            return linDat
        else:
            return linDex   
         
    def execute(self, data):
        rd = ExtruderManager.getInstance().getActiveExtruderStacks()[0].getProperty("retraction_amount", "value")
        rdStr = str(rd).rstrip('.0')
        s = self.getSettingValueByKey("slope")
        hs = self.getSettingValueByKey("horizontal_shift")
        ls = self.getSettingValueByKey("lower_stretch")
        rs = 60 * ExtruderManager.getInstance().getActiveExtruderStacks()[0].getProperty("retraction_speed", "value")
        rDex = []
        
        #while there are layers left to check
        for layer_number, layer in enumerate(data):
            
            #split each layer into a list of its Gcode lines
            lines = layer.split("\n")
            
            #while there are lines left to check for the current layer
            for line_number , line in enumerate(lines, 0): 
                
                #if the line contains a retract
                if line.count('E-' + rdStr) > 0:
                    
                    #store that line's index
                    rDex.append(line_number)
            
            #while there are retract lines left to alter
            for i in range( len(rDex) - 1): 
                
                #store adjacent line data and indeces for the current retract line
                # i = last line before retract, t = travel line, u = unretract line
                iDex = rDex[i] - 1 
                tDex = rDex[i] + 1  
                uDex = rDex[i] + 2 
                iDat = lines[iDex]
                tDat = lines[tDex] 
                uDat = lines[uDex]
                
                #check if adjacent lines correspond to the initial line before retraction, the travel line, and the unretract line, respectively. If not, go to the next line
                # where (int) countStep's sign and magnitude dictate which lines to check next.
                iDat = self.combLines(lines, iDat, iDex, 'G1', -1, 'dat')
                tDat = self.combLines(lines, tDat, tDex, 'G0', 1, 'dat')
                uDex = self.combLines(lines, uDat, uDex, 'E' + rdStr, 1, 'dex')
        
                iX = self.getValue(iDat, 'X')
                iY = self.getValue(iDat, 'Y')
                tX = self.getValue(tDat, 'X')
                tY = self.getValue(tDat, 'Y')          
        
                #calculate travel distance
                t = math.sqrt( pow(iX - tX, 2) + pow(iY - tY, 2) )
                
                #calculate the new retract distance
                r = max((rd - ls) / (1 + pow(s, -(.01 * (hs * rd) * t - rd)) ) + ls, 0)
                
                #replace the retract and unretract line with the new data
                lines[int(rDex[i])] = ('G1 F' + str(rs) + ' E-' + format( str(r), '.7') )                
                lines[uDex] = ('G1 F' + str(rs) + ' E' + format( str(r), '.7') )                           
            
            #join all lines for this new layer and update the gcode layer 
            new_layer = "\n".join(lines)
            data[layer_number] = new_layer            
            rDex.clear()

        print("Adaptive Retraction completed")                  
            
        return data
            