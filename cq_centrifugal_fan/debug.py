import sys
from typing import Any
import cq_centrifugal_fan.errors as cf_errors

import cqkit as ck


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
        super().__init__(None)  # NOTE: ocp_vscode at .initialize time
        self.defaults_kwargs = defaults_kwargs
        self.port = port
        self.is_initialized = False
        if not lazy_init:
            self.initialize()

    def on_call(self, _func_name, *_args, **_kwargs):
        if not self.is_initialized:
            self.initialize()

    def initialize(self):
        try:
            import ocp_vscode
        except ModuleNotFoundError as ex:
            print("Failed to import ocp_vscode", file=sys.stderr)
            raise cf_errors.DependencyError("OcpMonitor requires ocp_vscode", ex)

        self.module = ocp_vscode
        if defaults_kwargs is None:
            defaults_kwargs = {"reset_camera": ocp_vscode.Camera.CENTER}
        ocp_vscode.set_port(self.port)
        ocp_vscode.set_defaults(**self.defaults_kwargs)
        self.is_initialized = True


class JupyterMonitor(ModuleBasedMonitor):
    def __init__(self, lazy_init=True) -> None:
        super().__init__(None)  # Note: jupyter_cadquery at .initialize time
        self.is_initialized = False
        if not lazy_init:
            self.initialize()

    def initialize(self):
        try:
            import jupyter_cadquery
        except ModuleNotFoundError as ex:
            print("Failed to import jupyter_cadquery", file=sys.stderr)
            raise cf_errors.DependencyError(
                "JupyterMonitor requires jupyter_cadquery", ex
            )

        self.module = jupyter_cadquery
        self.is_initialized = True

    def on_call(self, _func_name, *_args, **_kwargs):
        if not self.is_initialized:
            self.initialize()


class CqKitMonitor(Monitor):
    def __init__(self) -> None:
        pass

    def show_object(self, obj, *args, **kwargs):
        ck.pprint_obj(obj)


class FallbackCompositeMonitor(Monitor):
    def __init__(self, monitors) -> None:
        self.monitors = monitors

    def show_object(self, *args, **kwargs):
        exceptions = []
        for monitor in self.monitors:
            try:
                return monitor.show_object(*args, **kwargs)
            except cf_errors.DependencyError as ex:
                exceptions.append(ex)
        raise cf_errors.RuntimeError(
            "All monitors failed to show object", exceptions=ex
        )


monitor = FallbackCompositeMonitor([OcpMonitor(), JupyterMonitor(), CqKitMonitor(), NoOpMonitor()])
