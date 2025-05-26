# Example Usage

## Install Codeplay oneAPI Plugins

### Step 1) Setup Spack

```bash
    git clone --depth=2 --branch=codeplay-oneapi https://github.com/scottstraughan/spack.git ~/spack
    cd ~/spack && . share/spack/setup-env.sh
    spack bootstrap now
```

###  Step 2) Install a Plugin

```bash
    spack install codeplay-oneapi-nvidia
    spack install codeplay-oneapi-amd
```

**You can install plugins the in the following ways:**

- `spack install codeplay-oneapi-nvidia` (use latest)
- `spack install codeplay-oneapi-nvidia driver=11.7` (use latest, target CUDA 11.7)
- `spack install codeplay-oneapi-nvidia@2025.1.0 driver=11.7` (use 2025.1.0 version, target 11.7)
- `spack install codeplay-oneapi-nvidia@2025.1.0` - (use 2025.1.0 version, use latest driver)]
- `spack install codeplay-oneapi-amd` (use latest)
- etc

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

## Support

Please contact scotts@codeplay.com
