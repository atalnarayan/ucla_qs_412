############################################################
#
# A pulse sequence suitable for performing a
# pulse and collect experiment.
#
# pulse - delay - acq
#
############################################################

procedure(pulse_program,dir,mode,pars)

# Expose parameters for FX3 implementation
   if(nrArgs == 3)
      assignlist(pars)
   endif

# Interface description (name, label, x, y, ctrl, vartype)
  interface = ["nucleus",         "Nucleus",                    "tb",  "readonly_string";
               "b1Freq1H",        "1H frequency (MHz)",         "tb",  "freq";
               "centerFreqPPM1H",   "Centre frequency 1H (ppm)",     "tb",  "float";
               "centerFreqPPM13C",  "Centre frequency 13C (ppm)",    "tb", "float";
               "90Amplitude1H",   "Pulse amplitude 1H (dB)",       "tb",  "pulseamp";
               "90Amplitude13C",  "Pulse amplitude 13C (dB)",      "tb",  "pulseamp";
               "pulseLength1H",   "Pulse length 1H (us)",          "tb",  "pulselength";
               "pulseLength13C",   "Pulse length 13C (us)",          "tb",  "pulselength";
               "b1Freq13C",       "13C frequency (MHz)",        "tb",  "freq";
               "shiftPoints",     "Number of points to shift",  "tb",  "float,[-100,100]";
               "repTime",         "Repetition time (ms)",       "tb",  "reptime"]


# Relationships to determine remaining variable values
   relationships = ["b1Freq        = b1Freq1H",
                    "nPnts         = nrPnts",
                    "a90H           = 90Amplitude1H",
                    "a90C          = 90Amplitude13C",
                    "d90H           = pulseLength1H",
                    "d180H = pulseLength1H*2",
                    "d90C           = pulseLength13C",
                    "d180C = pulseLength13C*2",
                    "dAcq          = ucsUtilities:getacqDelay(pulseLength1H,shiftPoints,dwellTime)",
                    "offFreq1H     = (centerFreqPPM1H-wvPPMOffset1H)*b1Freq1H",
                    "offFreq13C   =  (centerFreqPPM13C-wvPPMOffset13C)*b1Freq13C",
                    "O1            = offFreq1H",
                    "fTx1H         = double(b1Freq)+double(offFreq1H/1e6d)",
                    "fTx13C        = double(b1Freq13C)+double(offFreq13C/1e6d)",
                    "totPnts       = nrPnts",
                    "totTime       = acqTime"]

# Define the pulse programs parameter groups and their order
   groups = ["Pulse_sequence","Acquisition",
             "Processing_Std","Display_Std","File_Settings"]

# These parameters will be changed between experiments
   variables = [""]

# Pulse sequence
   initpp(dir) # Reset internal parameter list                 


  # Your pulse program goes here
############# DJ_f1_1H (Identity) #############
    ## DJ Pre 1H ##
    pulse(2, a90C, p4, d90C, fTx13C)
    delay(0.5)
    pulse(1, a90H, p2, d90H, fTx1H)
    delay(0.5)
    ###############
    ## DJ Post 1H ##
    pulse(2, a90C, p2, d90C, fTx13C)
    delay(0.5)
    pulse(1, a90H, p4, d90H, fTx1H)
    ################
#################################################
  
  delay(0.5)
  
   
  # Acquisition pulse
  pulse(1, a90H, p1, d90H)
  # Acquire
   delay(dAcq)
   acquire("overwrite", nPnts)

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
      return(null)
   endif
   assignlist(specPar)

   modelPar = ucsUtilities:getModelBasedParameters("1H",specPar)

   par = ["b1Freq13C       = $Frequency_X$",
          "pulseLengthC180 = $Pulse_length_X*4$",
          "decoupleAmp     = $Power_level_X - 6$",
          "rxGain          = $modelPar->rxGain$",
          "b1Freq1H        = $Frequency_1H$"         
]

endproc(par)
