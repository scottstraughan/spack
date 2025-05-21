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
        args += f"&filters[]=linux"
        args += f"&via=spack"

        return f"https://developer.codeplay.com/api/v1/products/download{args}"

    def install_plugin(self, spec, stage, prefix, version_):
        """
        Install the plugin into the prefix directory and create symlinks into the oneapi compiler directory.
        """
        if not spec.satisfies("%oneapi"):
            raise InstallError("Oneapi is not satisfied")

        target_driver_version = self._get_target_driver_version(version_)

        tty.msg(f"Installing {self.gpu_vendor} plugin targeting {self.backend_name} {target_driver_version}")

        oneapi_base_path = os.path.join(
            spec["intel-oneapi-compilers"].prefix,
            "compiler",
            self._oneapi_compiler_version(version_),
            "lib")

        # Run the plugin installing in extract only mode
        bash = Executable("bash")
        bash(stage.archive_file, "-x", "-f", ".")

        tty.debug(f"Plugin installer has successfully extracted.")

        # Install the plugins into all oneapi installation
        self._install_into_oneapi(prefix, version_, target_driver_version, oneapi_base_path)

        tty.msg(f"oneAPI for {self.gpu_vendor} ({self.backend_name}) plugin installation complete.")

    def _install_into_oneapi(self, prefix, version_, target_driver_version, oneapi_base_path):
        """
        Create all the symlinks into the oneapi compiler directory.
        """
        tty.msg(f"Installing into found oneAPI installation at {oneapi_base_path}.")

        # Install the plugin files
        lib_filename = (f"{self.backend_name}"
                        f"-{target_driver_version}"
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

        tty.msg(f"Successfully installed into found oneAPI installation at {oneapi_base_path}.")

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
        version_ = str(version_)

        if version_ is None:
            tty.msg(f"Specific version has not been provided, using latest.")
            return self._get_latest_supported_version()

        for supported_version in self.supported_version_list:
            if supported_version["version"] == version_:
                tty.msg(f"Found supported version for {version_}, using that.")
                return supported_version

        raise InstallError(f"Could not satisfy a version reference based on version '{version_}'.")

    def _get_by_package_version(self, package_version):
        """
        Get a package reference by a provided package version. If nothing is found, will return None.
        """
        for supported_version in self.supported_version_list:
            if supported_version["version"] == package_version:
                tty.debug(f"Found targeted version '{package_version}' in supported version list.")
                return supported_version

        tty.debug(f"Could not find targeted version '{package_version}' in supported version list.")
        return None

    def _package_version(self, version_):
        """
        Returns something like 2025.1.0
        """
        supported_version_reference = self._get_supported_version(version_)
        return supported_version_reference["version"]

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

    def _get_target_driver_version(self, version_):
        supported_version_reference = self._get_supported_version(version_)
        latest_driver_version = supported_version_reference["supported_driver_versions"][0]

        if 'driver' in self.spec.variants:
            tty.debug(f"User has specified a custom driver variant.")

        return self.spec.variants['driver'].value if 'driver' in self.spec.variants else latest_driver_version

    @staticmethod
    def iterate_supported_versions(supported_versions: list):
        """
        Generator function that will yield values that can be used within plugin classes to set versions and also
        dependencies.
        """
        for index, supported_version in enumerate(supported_versions):
            yield {
                "version": supported_version["version"],
                "sha256": supported_version["sha256"],
                "preferred": index == 0,
                "oneapi_compiler_version": supported_version["oneapi_compiler_version"],
                "supported_driver_versions": supported_version["supported_driver_versions"]
            }

    @staticmethod
    def iterate_all_driver_versions(supported_versions: list):
        found_driver_versions = []

        for supported_version in supported_versions:
            found_driver_versions += supported_version["supported_driver_versions"]

        # Remove duplicates
        return list(set(found_driver_versions))

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

        tty.debug(f"Creating symlink from source '{source_file_path}' to target '{target_path}'")

        symlink(source_file_path, target_path)
