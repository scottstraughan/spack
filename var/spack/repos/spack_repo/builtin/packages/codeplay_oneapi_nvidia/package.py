from spack.directives import maintainers, depends_on, version
from spack_repo.builtin.build_systems.codeplay_oneapi import CodeplayOneapi
from spack_repo.builtin.build_systems.generic import Package


class CodeplayOneapiNvidia(Package):
    """
    Codeplay oneAPI for NVIDIA GPUs package.

    Plugin can be installed in the following ways:
        - spack install codeplay-nvidia-amd@all-2025.1.0
        - spack install codeplay-nvidia-amd@all
        - spack install codeplay-nvidia-amd@2025.1.0
        - spack install codeplay-nvidia-amd
    """

    # Supported version list
    supported_versions = [
        {
            "version": "2025.1.0",
            "oneapi_compiler_version": "2025.1",
            "sha256": "c68b5e2d18c4cb0bc4c3eb227dbc8cbadf2800e0102b61f8e8ca0d50a9f74928",
            "ur": "0.11.7",
            "supported_driver_versions": ["11.7"]
        }
    ]

    # Current maintainer of the packages
    maintainers("scottstraughan")

    # Dependencies
    depends_on("intel-oneapi-compilers")

    # Create all the versions
    for current_version in CodeplayOneapi.iterate_version_map(supported_versions):
        version(current_version[0], current_version[1], extension="sh", expand=False, preferred=current_version[2])

    def __init__(self, spec):
        super().__init__(spec)

        # Note: We can't use inheritance since many of the fields are class fields and data would leak between
        # the shared plugins. Instead, we will use composition of a base plugin and use shared methods.
        self.codeplay_oneapi = CodeplayOneapi(spec, CodeplayOneapiNvidia.supported_versions, "nvidia")

    def install(self, spec, prefix):
        """
        Install the plugin.
        """
        self.codeplay_oneapi.install_plugin(spec, self.stage, prefix, self.version)

    def url_for_version(self, version):
        """
        Generate a URL to download from developer portal.
        """
        url = self.codeplay_oneapi.url_for_version(version)

        # Small hack as we transition to universal driver packages
        return url.replace("11.7", "all")
