#!/usr/bin/env python
# coding: utf-8

import logging
import os
import re
import shutil
import subprocess
import time

from typing import Optional, Union, List


class ADB(object):
    def __init__(self, device: str = None, debug: bool = False):
        self.logger = logging.getLogger(
            "{0}.{1}".format(__name__, self.__class__.__name__)
        )
        self._device = device
        if debug:
            self.logger.setLevel(logging.DEBUG)
        if "ADB_PATH" in os.environ:
            self.adb_path: str = os.environ["ADB_PATH"]
        else:
            self.adb_path: str = "adb"
        if not self.is_available():
            raise FileNotFoundError(
                "Adb executable is not available! Make sure to have adb (Android Debug Bridge) "
                "installed and added to the PATH variable, or specify the adb path by using the "
                "ADB_PATH environment variable."
            )

    @property
    def target_device(self) -> str:
        return self._device

    @target_device.setter
    def target_device(self, new_device: str):
        self._device = new_device

    def is_available(self) -> bool:
        return shutil.which(self.adb_path) is not None

    def execute(
        self, command: List[str], is_async: bool = False, timeout: Optional[int] = None
    ) -> Optional[str]:
        if not isinstance(command, list) or any(
            not isinstance(command_token, str) for command_token in command
        ):
            raise TypeError(
                "The command to execute should be passed as a list of strings"
            )

        if timeout is not None and (not isinstance(timeout, int) or timeout <= 0):
            raise ValueError("If a timeout is provided, it must be a positive integer")

        if is_async and timeout:
            raise RuntimeError(
                "The timeout cannot be used when executing the program in background"
            )

        try:
            if self.target_device:
                command[0:0] = ["-s", self.target_device]

            command.insert(0, self.adb_path)
            self.logger.debug(
                "Running command `{0}` (async={1}, timeout={2})".format(
                    " ".join(command), is_async, timeout
                )
            )
            if is_async:
                subprocess.Popen(command)
                return None
            else:
                process = subprocess.Popen(
                    command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
                )
                output = (
                    process.communicate(timeout=timeout)[0]
                    .strip()
                    .decode(errors="backslashreplace")
                )
                if process.returncode != 0:
                    raise subprocess.CalledProcessError(
                        process.returncode, command, output.encode()
                    )
                self.logger.debug(
                    "Command `{0}` successfully returned: {1}".format(
                        " ".join(command), output
                    )
                )
                time.sleep(1)

                return output
        except subprocess.TimeoutExpired as e:
            self.logger.error(
                "Command `{0}` timed out: {1}".format(
                    " ".join(command),
                    e.output.decode(errors="backslashreplace") if e.output else e,
                )
            )
            raise
        except subprocess.CalledProcessError as e:
            self.logger.error(
                "Command `{0}` exited with error: {1}".format(
                    " ".join(command),
                    e.output.decode(errors="backslashreplace") if e.output else e,
                )
            )
            raise
        except Exception as e:
            self.logger.error(
                "Generic error during `{0}` command execution: {1}".format(
                    " ".join(command), e
                )
            )
            raise

    def get_version(self, timeout: Optional[int] = None) -> str:
        output = self.execute(["version"], timeout=timeout)
        match = re.search(r"version\s(\S+)", output)
        if match:
            return match.group(1)
        else:
            raise RuntimeError("Unable to determine adb version")

    def get_available_devices(self, timeout: Optional[int] = None) -> List[str]:
        output = self.execute(["devices"], timeout=timeout)
        devices = []
        for line in output.splitlines():
            tokens = line.strip().split()
            if len(tokens) == 2 and tokens[1] == "device":
                # Add to the list the name / ip and port of the device.
                devices.append(tokens[0])
        return devices

    def shell(
        self, command: List[str], is_async: bool = False, timeout: Optional[int] = None
    ) -> Optional[str]:

        if not isinstance(command, list) or any(
            not isinstance(command_token, str) for command_token in command
        ):
            raise TypeError(
                "The command to execute should be passed as a list of strings"
            )
        command.insert(0, "shell")
        return self.execute(command, is_async=is_async, timeout=timeout)

    def get_property(self, property_name: str, timeout: Optional[int] = None) -> str:
        return self.shell(["getprop", property_name], timeout=timeout)

    def get_device_sdk_version(self, timeout: Optional[int] = None) -> int:
        return int(self.get_property("ro.build.version.sdk", timeout=timeout))

    def wait_for_device(self, timeout: Optional[int] = None) -> None:
        self.execute(["wait-for-device"], timeout=timeout)

    def kill_server(self, timeout: Optional[int] = None) -> None:
        self.execute(["kill-server"], timeout=timeout)

    def connect(self, host: str = None, timeout: Optional[int] = None) -> str:
        if host:
            connect_cmd = ["connect", host]
        else:
            connect_cmd = ["start-server"]

        output = self.execute(connect_cmd, timeout=timeout)
        if output and "unable to connect" in output.lower():
            raise RuntimeError(
                "Something went wrong during the connect operation: {0}".format(output)
            )
        else:
            return output

    def remount(self, timeout: Optional[int] = None) -> str:
        output = self.execute(["remount"], timeout=timeout)
        if output and "remount succeeded" in output.lower():
            return output
        else:
            raise RuntimeError(
                "Something went wrong during the remount operation: {0}".format(output)
            )

    def reboot(self, timeout: Optional[int] = None) -> None:
        return self.execute(["reboot"], timeout=timeout)

    def push_file(
        self,
        host_path: Union[str, List[str]],
        device_path: str,
        timeout: Optional[int] = None,
    ) -> str:
        if isinstance(host_path, list):
            for p in host_path:
                if not os.path.exists(p):
                    raise FileNotFoundError(
                        'Cannot copy "{0}" to the Android device: no such file or directory'.format(
                            p
                        )
                    )
        if isinstance(host_path, str) and not os.path.exists(host_path):
            raise FileNotFoundError(
                'Cannot copy "{0}" to the Android device: no such file or directory'.format(
                    host_path
                )
            )
        push_cmd = ["push"]
        if isinstance(host_path, list):
            push_cmd.extend(host_path)
        else:
            push_cmd.append(host_path)
        push_cmd.append(device_path)
        output = self.execute(push_cmd, timeout=timeout)
        match = re.search(r"\d+ files? pushed\.", output.splitlines()[-1])
        if match:
            return output
        else:
            raise RuntimeError("Something went wrong during the file push operation")

    def pull_file(
        self,
        device_path: Union[str, List[str]],
        host_path: str,
        timeout: Optional[int] = None,
    ) -> str:
        if isinstance(device_path, list) and not os.path.isdir(host_path):
            raise NotADirectoryError(
                "When copying multiple files, the destination host path should be an "
                'existing directory: "{0}" directory was not found'.format(host_path)
            )
        if not os.path.isdir(os.path.dirname(host_path)):
            raise NotADirectoryError(
                'The destination host directory "{0}" was not found'.format(
                    os.path.dirname(host_path)
                )
            )
        pull_cmd = ["pull"]
        if isinstance(device_path, list):
            pull_cmd.extend(device_path)
        else:
            pull_cmd.append(device_path)
        pull_cmd.append(host_path)
        output = self.execute(pull_cmd, timeout=timeout)
        match = re.search(r"\d+ files? pulled\.", output.splitlines()[-1])
        if match:
            return output
        else:
            raise RuntimeError("Something went wrong during the file pull operation")

    def install_app(
        self,
        apk_path: str,
        replace_existing: bool = False,
        grant_permissions: bool = False,
        timeout: Optional[int] = None,
    ):
        if not os.path.isfile(apk_path):
            raise FileNotFoundError('"{0}" apk file was not found'.format(apk_path))
        install_cmd = ["install"]
        if replace_existing:
            install_cmd.append("-r")
        if grant_permissions and self.get_device_sdk_version() >= 23:
            install_cmd.append("-g")
        install_cmd.append(apk_path)
        output = self.execute(install_cmd, timeout=timeout)
        match = re.search(r"Failure \[.+?\]", output, flags=re.IGNORECASE)
        if not match:
            return output
        else:
            raise RuntimeError(
                "Application installation failed: {0}".format(match.group())
            )

    def uninstall_app(self, package_name: str, timeout: Optional[int] = None):
        uninstall_cmd = ["uninstall", package_name]
        output = self.execute(uninstall_cmd, timeout=timeout)
        match = re.search(r"Failure \[.+?\]", output, flags=re.IGNORECASE)
        if not match:
            return output
        else:
            raise RuntimeError("Application removal failed: {0}".format(match.group()))
