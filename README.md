# RAMANMETRIX plugin for ENLIGHTEN

The plugin gives ENLIGHTEN a live view with preprocessed spectra and predictions, using models built in RAMANMETRIX.

## Prerequisites

- Wasatch Photonics spectrometer controlled by ENLIGHTEN software (see https://wasatchphotonics.com/product-category/software/).
- RAMANMETRIX (with a valid license) must be installed on the same computer (see https://docs.ramanmetrix.eu/documentation/Desktop.html).
- A model created in a compatible vwrsion of RAMANMETRIX (either before or after version 0.5.0).

## Usage

After installing ENLIGHTEN, place the plugin and the model files from `plugins/bpd` in the respective Documents subfolder:
```
%USERPROFILE%\Documents\EnlightenSpectra\plugins\bpd\RAMANMETRIX.py
%USERPROFILE%\Documents\EnlightenSpectra\plugins\bpd\model_RAMANMETRIX.pkl
```
In the ENLIGHTEN software select plugin `bpd.RAMANMETRIX` and click on `Connect` checkbox.

The provided example `model_RAMANMETRIX.pkl` includes the preprocessing pipeline and a PLS model for predicting the ethanol persentage in ethanol-water mixture.
The model file can be replaced by any classification or regression model (with preprocessing included) created in RAMANMETRIX.

## Troubleshooting

If RAMANMETRIX is installed in a different from default user location or the model has a name different from the default,
you will face errors. The correct locations can be adjusted in the configuration file, which is generated on the first run of the plugin:
```
%USERPROFILE%\Documents\EnlightenSpectra\plugins\bpd\RAMANMETRIX.json
```

