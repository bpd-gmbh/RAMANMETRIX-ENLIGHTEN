from requests import post
from time import sleep
import json
import numpy as np
import subprocess
import logging
import ctypes
import os

from EnlightenPlugin import EnlightenPluginBase, \
    EnlightenPluginResponse, \
    EnlightenPluginField, \
    EnlightenPluginConfiguration

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


class RAMANMETRIX(EnlightenPluginBase):
    _ramanmetrix_exe = None
    _ramanmetrix_config_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), "RAMANMETRIX.json")
    _ramanmetrix_config = dict()

    def _ramanmetrix_config_default(self):
        return {
            "back_url": "http://localhost",
            "port": 5006,
            "exe_path": os.path.join(os.getenv("LOCALAPPDATA"),
                                     r"Programs\RAMANMETRIX\server\ramanmetrix_backend.exe"),
            "model": os.path.join(os.getenv("USERPROFILE"),
                                  r"Documents\EnlightenSpectra\plugins\bpd\model_RAMANMETRIX.pkl"),
            "sid": "ENLIGHTEN_session"
        }

    def _update_config(self):
        log.debug("RAMANMETRIX._update_config")
        log.debug(self._ramanmetrix_config_file)
        if os.path.exists(self._ramanmetrix_config_file):
            with open(self._ramanmetrix_config_file, "r") as fp:
                conf_json = json.load(fp)
            conf_def = self._ramanmetrix_config_default()
            for k in conf_def.keys():
                v = conf_json.get(k)
                self._ramanmetrix_config[k] = v if v else conf_def[k]
        with open(self._ramanmetrix_config_file, "w") as fp:
            json.dump(self._ramanmetrix_config, fp, indent=2)

    @staticmethod
    def _raise_exception(e, fun, ask=False, info=None, error_callback=lambda: None):
        text = f"{repr(e)}\n\n{info}" if info else repr(e)
        text = f"ERROR in {fun}:\n{text}\n\nTry editing RAMANMETRIX.json to fix the plugin configuration"
        if ask:
            answ = ctypes.windll.user32.MessageBoxW(0, text, "RAMANMETRIX plugin error", 5)
            if answ == 2:
                error_callback()
                raise e
        else:
            ctypes.windll.user32.MessageBoxW(0, text, "RAMANMETRIX plugin error", 0)
            error_callback()
            raise e

    def _ramanmetrix_api(self, api_name, file=None, json=None):
        args = {}
        if file is not None:
            args["files"] = {"file": file}
        if json is not None:
            args["json"] = json
        url = "{}:{}/api/{}".format(self._ramanmetrix_config["back_url"], self._ramanmetrix_config["port"], api_name)
        cookies = {"session_ramanmetrix_" + str(self._ramanmetrix_config["port"]): self._ramanmetrix_config["sid"]}
        response = post(url=url, cookies=cookies, timeout=5, **args)
        response.raise_for_status()
        response = response.json()
        if response.get("error"):
            self._raise_exception(response["error"], api_name, True, info=url)
        return response

    def _ramanmetrix_exe_kill(self):
        if self._ramanmetrix_exe is not None:
            if self._ramanmetrix_exe.poll() is None:
                self._ramanmetrix_exe.kill()

    def _ramanmetrix_exe_start(self):
        if self._ramanmetrix_exe is not None:
            if self._ramanmetrix_exe.poll() is None:
                return None

        while True:
            try:
                self._update_config()
                args = [self._ramanmetrix_config["exe_path"], str(self._ramanmetrix_config["port"])]
                self._ramanmetrix_exe = subprocess.Popen(args, creationflags=subprocess.CREATE_NEW_CONSOLE)
                sleep(2)
                break
            except Exception as e:
                info = f"exe_path: {self._ramanmetrix_config.get('exe_path')}\n" \
                       f"back_url: {self._ramanmetrix_config.get('back_url')}:{self._ramanmetrix_config.get('port')}"
                self._raise_exception(e, "ramanmetrix_exe_start", True, info, self._ramanmetrix_exe_kill)

        retry_n = 10

        info = f"model: {self._ramanmetrix_config['model']}\n" \
               f"url: {self._ramanmetrix_config.get('back_url')}:{self._ramanmetrix_config['port']}"
        while True:
            try:
                self._update_config()
                with open(self._ramanmetrix_config["model"], 'rb') as f:
                    self._ramanmetrix_api("defaults")
                    self._ramanmetrix_api("model_upload", file=f)
                break
            except ConnectionError as e:
                if retry_n:
                    retry_n -= 1
                    sleep(2)
                else:
                    self._raise_exception(e, "ramanmetrix_exe_start", True, info, self._ramanmetrix_exe_kill)
            except Exception as e:
                self._raise_exception(e, "ramanmetrix_exe_start", True, info, self._ramanmetrix_exe_kill)

    def get_configuration(self):
        log.debug("RAMANMETRIX.get_configuration")
        self._update_config()
        fields = [
            EnlightenPluginField(name="Prediction", direction="output", datatype=str, initial="None",
                                 tooltip="What the plugin outputs")
        ]
        return EnlightenPluginConfiguration(name="RAMANMETRIX",
                                            has_other_graph=True,
                                            streaming=True,
                                            is_blocking=False,
                                            fields=fields,
                                            series_names=['Preprocessed'])

    def connect(self, *args, **kwargs):
        log.debug("RAMANMETRIX.connect")
        self._ramanmetrix_exe_start()
        return super().connect(*args, **kwargs)

    def process_request(self, request):
        log.debug("RAMANMETRIX.process_request.START")
        try:
            x_axis_unit = self.ctl.graph.get_x_axis_unit()
        except Exception:
            log.debug("Cannot get `self.ctl.graph.get_x_axis_unit()` trying older implementation with "
                      "`self.enlighten_info.get_x_axis_unit()`")
            x_axis_unit = self.enlighten_info.get_x_axis_unit()

        spectra = {"x": request.settings.wavenumbers,
                   "y": [request.processed_reading.processed.tolist()]}
        self._ramanmetrix_exe_start()
        pred = self._ramanmetrix_api("predict_json", json=spectra)
        outputs = {"Prediction": pred.get("predictions", [pred.get("error", "unknown error")])[0]}
        spectra_pp = pred.get("preprocessed", {})
        series = spectra_pp.get("y")
        if series:
            x_pp = spectra_pp["x"]
            if x_axis_unit == "nm" and request.settings.has_excitation():
                x_pp = (1 / (1 / request.settings.excitation() - np.asarray(x_pp) / 10000000)).tolist()
            elif x_axis_unit != "cm":
                x_pp = [i for i in range(1, len(x_pp) + 1)]
            series = {
                "Preprocessed": {
                    "x": x_pp,
                    "y": series[0],
                }
            }
        else:
            series = {}
        log.debug("RAMANMETRIX.process_request.END {}".format(outputs))
        resp = EnlightenPluginResponse(request, series=series, outputs=outputs)
        return resp

    def disconnect(self, *args, **kwargs):
        log.debug("RAMANMETRIX.disconnect")
        self._ramanmetrix_exe_kill()
        return super().disconnect(*args, **kwargs)
