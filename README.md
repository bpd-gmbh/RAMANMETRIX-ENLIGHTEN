# Plugin for Enlighten

## Prerequisites

RAMANMETRIX (with a valid license) must be installed on the same computer.

The model format should be compatible with the RAMANMETRIX version (either before or after version 0.5.0).

## Usage

The plugin and model files are expected to be placed in the Documents folder rather than in Program Files:
```
%USERPROFILE%\Documents\EnlightenSpectra\plugins\bpd\RAMANMETRIX.py
%USERPROFILE%\Documents\EnlightenSpectra\plugins\bpd\model_RAMANMETRIX_v05.pkl
```

If RAMANMETRIX is installed in a different location or the model has a name different from the default,
the correct locations can be adjusted in the configuration file, which is generated on the first run of the plugin:
```
%USERPROFILE%\Documents\EnlightenSpectra\plugins\bpd\RAMANMETRIX.json
```