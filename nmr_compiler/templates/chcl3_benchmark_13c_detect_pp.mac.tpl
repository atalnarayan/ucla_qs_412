############################################################
#
# A pulse sequence suitable for performing a 13C
# pulse and collect experiment with NOE enhancement and
# Proton decoupling.
#
# NOE - delay - pulse - delay - acquire/decoupling
#
############################################################

procedure(pulse_program,dir,mode,pars)

# Expose parameters for FX3 implementation
   if(nrArgs == 3)
      assignlist(pars)
   endif

# Interface description (name, label, control, vartype)
  interface = ["nucleus",          "Nucleus",                   "tb", "readonly_string";
               "b1Freq13C",        "13C frequency (MHz)",       "tb", "freq";
               "centerFreqPPM1H",   "Centre frequency 1H (ppm)",     "tb",  "float";
               "centerFreqPPM13C",  "Centre frequency 13C (ppm)",    "tb", "float";
               "b1Freq1H",         "1H frequency (MHz)",        "tb", "freq";
               "amplitudeC90",     "13C 90 pulse amplitude (dB)",  "tb", "pulseamp";
               "pulseLengthC90",   "13C 90 pulse length (us)",     "tb", "pulselength";
               "amplitudeH90",     "1H 90 pulse amplitude (dB)",  "tb", "pulseamp";
               "pulseLengthH180Waltz", "Waltz 1H 180 pulse length (us)",  "tb", "pulselength";
               "pulseLengthH90",  "1H 90 pulse length (us)",  "tb", "pulselength";
               "noeDelay",         "NOE delay time (ms)",       "tb", "reptime";
               "noeAmp",           "NOE power (dB)",            "tb", "pulseamp";
               "repTime",          "Repetition time (ms)",      "tb", "reptime"]

# Relationships to determine remaining variable values
   relationships = ["waltzDuration = WALTZ16:duration(pulseLengthH180Waltz/2,pgo)",
                    "n1            = nrPnts",
                    "n2            = trunc(1000*acqTime/waltzDuration)+1",
                    "n3            = trunc(1000*noeDelay/waltzDuration)+1",
                    "a90C          = amplitudeC90",
                    "aNOE          = noeAmp",
                    "a90H          = amplitudeH90",
                    "d90C          = pulseLengthC90",
                    "d180C = pulseLengthC90*2",
                    "d45C          = pulseLengthC90/2",
                    "d90HWaltz     = pulseLengthH180Waltz/2",      # 90 degrees pulse duration
                    "d180HWaltz    = pulseLengthH180Waltz",        # 180 degree pulse duration
                    "d270HWaltz    = 3*pulseLengthH180Waltz/2",    # 270 degrees pulse duration
                    "d360HWaltz    = 2*pulseLengthH180Waltz",      # 360 degrees pulse duration
                    "d90H = pulseLengthH90",
                    "d180H = pulseLengthH90*2",
                    "dPreAcq       = ucsUtilities:getacqDelay(d90C,4,dwellTime)",
                    "offFreq1H     = (centerFreqPPM1H-wvPPMOffset1H)*b1Freq1H",
                    "offFreqX      = (centerFreqPPM13C-wvPPMOffset13C)*b1Freq13C",                    
                    "freqCh2       = double(b1Freq13C)+double(offFreqX/1e6d)",
                    "freqCh1       = double(b1Freq1H)+double(offFreq1H/1e6d)",
                    "f1H           = freqCh1",
                    "freqRx        = freqCh2",
                    "totPnts       = nrPnts",
                    "totTime       = acqTime"]

# Define the pulse program parameter groups and their order
   groups = ["Pulse_sequence","Acquisition",
             "Processing_Std","Display_Std","File_Settings"]

# These parameters will be changed between experiments
   variables = [""]

# Pulse sequence
   initpp(dir) # Reset internal parameter list

     # NOE transfer 1H->13C
     # loop(l2,n3)
     #    WALTZ16(1, aNOE, d90HWaltz, d180HWaltz, d270HWaltz, d360HWaltz, p2, p3)
     # endloop(l2)  
     # delay(20)
         
     # Your pulse program goes here
############ DJ_f1_13C (Identity) #############
    ## DJ Pre 13C ##
    pulse(2, a90C, p4, d90C, freqCh2)
    delay(0.5)
    pulse(1, a90H, p2, d90H, freqCh1)
    delay(0.5)
    ################
    ## DJ Post 13C ##
    pulse(2, a90C, p2, d90C, freqCh2)
    delay(0.5)
    pulse(1, a90H, p4, d90H, freqCh1)
    #################
#################################################
     delay(0.5)
      

     # Acquisition pulse
     pulse(2, a90C, p1, d90C)


  
     # Detection is done with 45 pulse on 13C
     #delay(20)           
     #pulse(2, a90C, p1, d45C, freqRx)  # 45 degree 13C RF pulse --> Atal: Didn't understand this. Why 45 degree pulse?

     # Acquire
      delay(dPreAcq)
      acquire("overwrite", n1)

    lst = endpp(0) # Return parameter list

# Phase cycle list
  phaseList = [0,2,0,2; # 90 phase
               1,3,1,3;
               2,0,2,0;
               3,1,3,1;
               0,2,0,2] # Acquire phase

endproc(lst,groups,interface,relationships,variables,null,phaseList)


#####################################################
# Assign those parameters which should take their 
# values from the factory defaults when making a 
# new experiment
#####################################################

procedure(getFactoryBasedParameters, par)

   specPar = gData->getXChannelParameters("13C")
   if(specPar == null)
      return(par)
   endif
   assignlist(specPar)

   modelPar = ucsUtilities:getModelBasedParameters("13C",specPar) 

   par = ["b1Freq13C       = $Frequency_X$",
          "pulseLengthC45  = $Pulse_length_X/2$",
          "amplitudeC45    = $Power_level_X$",
 "pulseLengthH180 = $PulseLength_1H_Decouple$",
          "decoupleAmp     = $PowerLevel_1H_Decouple$",
          "noeAmp          = $PowerLevel_1H_NOE$",
          "rxGain          = $modelPar->rxGain$",
          "dwellTime       = $modelPar->dwellTime$",
          "b1Freq1H        = $Frequency_1H$"]

endproc(par)