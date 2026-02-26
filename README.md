## Installation

### 1. Create a virtual environment

It is recommended to use a virtual environment to isolate dependencies.

```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Create the environment file

Copy the example file:

```bash
cp .env.example .env
```

- Add your weather API key to `.env`
- The `NEXT_URL` variable can be ignored

### 4. Configure device settings

Copy the example device configuration:

```bash
cd config
cp device.py.example device.py
cd ..
```

Edit `config/device.py` as needed for your matrix setup.

---

## Running the Application

When running the app, you will likely encounter a permission error related to `/dev/mem`.

The `rpi_ws281x` library requires elevated permissions because it accesses physical memory and PWM hardware directly.

Run the app as root using the Python interpreter inside your virtual environment:

```bash
sudo /home/user/led-matrix/venv/bin/python /home/user/led-matrix/app.py
```

Replace `/home/user/led-matrix` with the correct path to your project.