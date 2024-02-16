from typing import Any
import cq_centrifugal_fan.errors as cf_errors

import cqkit as ck

try:
    import ocp_vscode
    has_ocp_vscode = True
except Exception:
    print("Failed to import ocp_vscode")

try:
    import jupyter_cadquery as jq
    has_jupyter_cadquery = True
except Exception:
    print("Failed to import jupyter_cadquery")


class Monitor:
    def __init__(self) -> None:
        pass

    def show_object(self, *args, **kwargs):
        raise cf_errors.NotImplementedError("show_object")

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        return self.show_object(*args, **kwds)


class NoOpMonitor(Monitor):
    def __init__(self) -> None:
        pass

    def show_object(self, *args, **kwargs):
        pass


class ModuleBasedMonitor(Monitor):
    def __init__(self, module) -> None:
        self.module = module

    def on_call(self):
        pass

    def show_object(self, *args, **kwargs):
        self.on_call("show_object", *args, **kwargs)
        return self.module.show_object(*args, **kwargs)


class OcpMonitor(ModuleBasedMonitor):
    def __init__(self, port=3939, defaults_kwargs=None, lazy_init=True) -> None:
        super().__init__(ocp_vscode)
        if defaults_kwargs is None:
            defaults_kwargs = {"reset_camera": ocp_vscode.Camera.CENTER}
        self.defaults_kwargs = defaults_kwargs
        self.port = port
        self.is_initialized = False
        if not lazy_init:
            self.initialize()

    def on_call(self, _func_name, *_args, **_kwargs):
        if not has_jupyter_cadquery:
            raise cf_errors.DependencyError("OcpMonitor requires ocp_vscode")
        if not self.is_initialized:
            self.initialize()

    def initialize(self):
        self.is_initialized = True
        ocp_vscode.set_port(self.port)
        ocp_vscode.set_defaults(**self.defaults_kwargs)


class JupyterMonitor(ModuleBasedMonitor):
    def __init__(self) -> None:
        super().__init__(jq)
    
    def on_call(self, _func_name, *_args, **_kwargs):
        if not has_jupyter_cadquery:
            raise cf_errors.DependencyError("JupyterMonitor requires jupyter_cadquery")


class CqKitMonitor(Monitor):
    def __init__(self, kit) -> None:
        pass

    def show_object(self, obj, *args, **kwargs):
        ck.pprint_obj(obj)

class FallbackCompositeMonitor(Monitor):
    def __init__(self, monitors) -> None:
        self.monitors = monitors

    def show_object(self, *args, **kwargs):
        for monitor in self.monitors:
            try:
                return monitor.show_object(*args, **kwargs)
            except cf_errors.DependencyError:
                pass
        raise cf_errors.RuntimeError("All monitors failed to show object")


monitor = FallbackCompositeMonitor([OcpMonitor(), JupyterMonitor(), NoOpMonitor()])
