## Example Usage

### Step 1) Setup Spack

```bash
    git clone --depth=2 --branch=codeplay-oneapi-plugins https://github.com/scottstraughan/spack.git ~/spack
    cd ~/spack && . share/spack/setup-env.sh
    spack bootstrap now
```

###  Step 2) Install a Plugin

```bash
    spack install codeplay-oneapi-nvidia
```

You can install plugins the in the following ways:

- `spack install codeplay-oneapi-nvidia` (use latest)
- `spack install codeplay-oneapi-nvidia@11.7` (specify driver version - use latest package)
- `spack install codeplay-oneapi-nvidia@11.7-2025.1.0` (specify both driver and package versions)
- `spack install codeplay-oneapi-nvidia@2025.1.0` - (specify just package version)]
- `spack install codeplay-oneapi-amd` (use latest)
- `spack install codeplay-oneapi-amd@5.7` (specify driver version - use latest package)
- `spack install codeplay-oneapi-amd@6.0-2025.1.0` (specify both driver and package versions)
- `spack install codeplay-oneapi-amd@2025.1.0` - (specify just package version)

### Step 3) Setup Environment

```bash
    spack load intel-oneapi-compilers
    spack compiler find
    source /root/spack/opt/spack/linux-*/intel-oneapi-compilers*/setvars.sh # Required to make sycl-ls available
```


###  Step 4) Check Everything is Ready

```bash
    sycl-ls
```

