import json
import os
import stat

from spack.package import *


class CodeplayOneapi:
    """
    This is the base package for Codeplay oneAPI. Since the plugins for AMD/NVIDIA are almost identical, we want to
    reuse as much code as possible. All shared code/functionality is stored here. Its important to not inherit from this
    class but instead use composition to avoid class collisions.
    """

    def __init__(self, spec, version_map, gpu_vendor):
        self.spec = spec
        self.supported_version_list = version_map
        self.gpu_vendor = gpu_vendor
        self.backend_name = "hip" if gpu_vendor == "amd" else "cuda"

    def url_for_version(self, version_):
        """
        Generate a URL for a specific version of the plugin that can be used to download from the Codeplay
        developer portal.
        """
        args = "?product=oneapi"
        args += f"&variant={self.gpu_vendor}"
        args += f"&version={self._package_version(version_)}"
        args += f"&filters[]={self._gpu_driver_version(version_)}"
        args += f"&filters[]=linux"

        return f"https://developer.codeplay.com/api/v1/products/download{args}"

    def install_plugin(self, spec, stage, prefix, version_):
        """
        Install the plugin into the prefix directory and create symlinks into the oneapi compiler directory.
        """
        print("Resolved version: ")
        print(json.dumps(self._get_supported_version(version_)))

        if not spec.satisfies("%oneapi"):
            raise InstallError("Oneapi is not satisfied")

        print("OneAPI is satisfied!")

        oneapi_base_path = os.path.join(
            spec["intel-oneapi-compilers"].prefix,
            "compiler",
            self._oneapi_compiler_version(version_),
            "lib"
        )

        # Run the plugin installing in extract only mode
        bash = Executable("bash")
        bash(stage.archive_file, "-x", "-f", ".")

        print('Installer extracted successfully')

        # Install the plugins into all oneapi installation
        self._install_into_oneapi(prefix, version_, oneapi_base_path)

        print(f"oneAPI for {self.gpu_vendor} ({self.backend_name}) plugin installation complete.")

    def _install_into_oneapi(self, prefix, version_, oneapi_base_path):
        """
        Create all the symlinks into the oneapi compiler directory.
        """
        print(f"Installing into found oneAPI installation at {oneapi_base_path}.")

        # Install the plugin files
        lib_filename = (f"{self.backend_name}"
                        f"-{self._gpu_driver_version(version_)}"
                        f"-libur_adapter_{self.backend_name}.so.{self._universal_runtime(version_)}")

        source_lib_path = os.path.join(os.getcwd(), lib_filename)
        target_prefix_lib_path = os.path.join(prefix, lib_filename)

        # Install the plugin into prefix
        self._install_file(source_lib_path, target_prefix_lib_path)

        # Set permissions to the plugin in prefix
        current_permissions = os.stat(target_prefix_lib_path).st_mode
        new_permissions = current_permissions | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH
        os.chmod(target_prefix_lib_path, new_permissions)

        # Create all the symlink targets inside the oneapi lib directory
        for symlink_target in self._get_library_symlink_targets(version_, oneapi_base_path):
            self._create_symlink(target_prefix_lib_path, symlink_target)

        print(f"Successfully installed into found oneAPI installation at {oneapi_base_path}.")

    def _get_library_symlink_targets(self, version_, oneapi_base_path):
        """
        The universal runtime expects files names in a series of formats, create as many as possible to ensure success.
        """
        ur_segments = str(self._universal_runtime(version_)).split('.')

        file_names = [
            f"libur_adapter_{self.backend_name}.so",
            f"libur_adapter_{self.backend_name}.so.{ur_segments[0]}",
            f"libur_adapter_{self.backend_name}.so.{ur_segments[0]}.{ur_segments[1]}",
            f"libur_adapter_{self.backend_name}.so.{ur_segments[0]}.{ur_segments[1]}.{ur_segments[2]}"
        ]

        return [os.path.join(oneapi_base_path, x) for x in file_names]

    def _get_latest_supported_version(self) -> dict:
        return self.supported_version_list[0]

    def _get_supported_version(self, version_):
        """
        We can accept various version formats. For example, we will try to the resolve the following:
        - codeplay-oneapi-amd@6.0-2025.1.0
        - codeplay-oneapi-amd@6.0
        - codeplay-oneapi-amd@2025.1.0
        - codeplay-oneapi-amd
        """
        version_ = str(version_)

        if version_ is None:
            return self._get_latest_supported_version()

        package_version = None
        driver_version = None

        if "-" in version_:
            parts = version_.split("-")
            driver_version = parts[0]
            package_version = parts[1]

        found_version_reference = self._get_supported_version_reference(package_version, driver_version)

        # If we have not resolved any version reference by both package and driver version, attempt to load by
        # package version only
        if not found_version_reference:
            found_version_reference = self._get_supported_version_reference(version_, None)

        # If we have not resolved any version reference by both package and driver version, attempt to load by
        # driver version only
        if not found_version_reference:
            found_version_reference = self._get_supported_version_reference(None, version_)

        if not found_version_reference:
            raise InstallError(f"Could not satisfy a version reference based on version '{version_}'.")

        return found_version_reference

    def _get_supported_version_reference(self, package_version, driver_version):
        if package_version is not None:
            found_version = self._get_by_package_version(package_version)
        else:
            found_version = self._get_latest_supported_version()

        if found_version is None:
            return None

        if driver_version is not None:
            if driver_version in found_version["supported_driver_versions"]:
                return found_version

            return None
        else:
            return driver_version

    def _get_by_package_version(self, package_version):
        """
        Get a package reference by a provided package version. If nothing is found, will return None.
        """
        for supported_version in self.supported_version_list:
            if supported_version["version"] == package_version:
                return supported_version

        return None

    def _package_version(self, version_):
        """
        Returns something like 2025.1.0
        """
        supported_version_reference = self._get_supported_version(version_)
        return supported_version_reference["version"]

    def _gpu_driver_version(self, version_):
        """
        Returns something like 6.0
        """
        supported_version_reference = self._get_supported_version(version_)

        # If the user has specified something like codeplay-oneapi-amd@6.0-2025.1.0, extract the first part (6.0)
        version_ = str(version_)
        if "-" in version_:
            parts = version_.split('-')
            return parts[0]

        # If the user has specified nothing, use the latest
        return supported_version_reference["supported_driver_versions"][0]

    def _oneapi_compiler_version(self, version_):
        """
        From the version map, return the oneAPI compiler version based on the plugin version.
        """
        supported_version_reference = self._get_supported_version(version_)
        return supported_version_reference["oneapi_compiler_version"]

    def _universal_runtime(self, version_):
        """
        From the version map, return the universal runtime version based on the provider version.
        """
        supported_version_reference = self._get_supported_version(version_)
        return supported_version_reference["ur"]

    @staticmethod
    def iterate_supported_versions(supported_versions: list):
        """
        Generator function that will yield values that can be used within plugin classes to set versions and also
        dependencies.
        """
        first_item = True

        for supported_version in supported_versions:
            for si, supported_backend_version in enumerate(supported_version["supported_driver_versions"]):
                yield {
                    "version": f"{supported_backend_version}-{supported_version['version']}",
                    "sha256": supported_version["sha256"],
                    "preferred": False,
                    "oneapi_compiler_version": supported_version["oneapi_compiler_version"]
                }

                if first_item:
                    first_item = False

                    yield {
                        "version": supported_backend_version,
                        "sha256": supported_version["sha256"],
                        "preferred": si == 0,
                        "oneapi_compiler_version": supported_version["oneapi_compiler_version"]
                    }

    @staticmethod
    def _install_file(source, target):
        """
        Install a file, creating any directories if required.
        """
        target_directory = os.path.dirname(target)

        if not os.path.exists(target_directory):
            os.makedirs(target_directory)

        install(source, target)
        return target

    @staticmethod
    def _create_symlink(source_file_path, target_path):
        """
        Create a symlink target and create any required directories.
        """
        target_directory = os.path.dirname(target_path)

        if not os.path.exists(target_directory):
            os.makedirs(target_directory)

        print(f"Creating symlink from source '{source_file_path}' to target '{target_path}'")

        symlink(source_file_path, target_path)
