# py RF WebLab

This is a python interface for [RF WebLab](http://dpdcompetition.com/rfweblab/)
state-of-the-art measurement setup.


# DPD competition

Please visit [RF WebLab/about](http://dpdcompetition.com/rfweblab/about/).


## Access Details: Common Restrictions

The following was taken verbatim from [RF WebLab/access-details](http://dpdcompetition.com/rfweblab/access-details/)

> In order to protect the amplifier and the system from being burned limitations on peak output power and rms output power from the vector signal generator are enforced. It is assumed that the system is a 50 ohm system. The maximum allowed peak power from the signal generator is -8 dBm. The maximum allowed rms power level (Pin,RMS) depends on the peak-to-average power ratio (PAPR) of the input signal and will ensure that the peaks of the input signals stay mostly below -8 dBm. Some more input RMS power is allowed for high PAPR signals. There is also a maximum peak-to-average power ratio of the IQ-data signal of 20 dB. If any of these limits are exceeded, the system will not perform the measurement. The output in these cases is a data-file that contains a single “-inf”-value.

> A maximum of 1 000 000 IQ-data samples are accepted as input. If a file with more than 1 000 000 samples is uploaded, only the first 1 000 000 samples are actually used. The number of samples in the output data file (csv or dat) is of the same length as the input signal (or 1 000 000 samples if the input signal was longer).

> The maximum sampling rate in both generator and analyzer is 200 MHz. The maximum useful bandwidth is 160 MHz. This means that any signal component you put outside of the frequency range [-80 80] MHz is removed before being sent from the signal generator. The signal that is received from the signal analyzer is also limited to 160 MHz bandwidth, i.e., use only the signal components in the range [-80 80] MHz because everything outside of this range is distorted by a filtering.
