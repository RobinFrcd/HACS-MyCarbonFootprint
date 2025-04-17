# My Carbon Footprint

A Home Assistant integration that calculates your carbon footprint based on your energy consumption and carbon intensity data.

## Features

- Calculates carbon footprint based on energy consumption sensors and carbon intensity
- Provides real-time carbon footprint metrics
- Supports multiple energy consumption sensors
- Uses historical data to provide values immediately after setup
- Cumulative tracking of carbon emissions over time

## Installation

### HACS Installation
1. Open HACS in your Home Assistant instance
2. Go to "Integrations"
3. Click the "+" button
4. Search for "My Carbon Footprint"
5. Click Install

### Manual Installation
1. Copy the `custom_components/my_carbon_footprint` directory to your Home Assistant `custom_components` directory
2. Restart Home Assistant

## Configuration

1. Go to Settings > Devices & Services
2. Click "Add Integration"
3. Search for "My Carbon Footprint"
4. Follow the configuration steps to select your carbon intensity sensor and energy consumption sensors

### Configuration Details

- **Carbon Intensity Sensor**: This should be a sensor providing carbon intensity in grams of CO2 per kWh (g CO2/kWh)
- **Energy Consumption Sensors**: These should be cumulative energy sensors in kWh. Typically, these are utility meter sensors or energy monitoring devices that track total consumption.

## How It Works

1. When first set up, the integration will use historical data from the last 24 hours to initialize carbon footprint values.
2. It monitors changes in the energy consumption sensors to track new energy usage.
3. For each update, it calculates the new consumption and multiplies it by the current carbon intensity.
4. All values are stored cumulatively, so you can track your carbon footprint over time.
5. Both total and per-energy-source carbon footprints are provided.

## Usage

Once configured, the integration will create sensors showing:
- Total carbon footprint (kg CO2)
- Carbon footprint for each energy sensor
- Daily/monthly carbon statistics

## Services

The integration provides the following services:

### Reset Counter
Reset the carbon footprint counter for all or specific energy sensors.

**Service name:** `my_carbon_footprint.reset_counter`

**Parameters:**
- `energy_entity_id` (optional): The energy entity to reset. Leave empty to reset all entities.

## Development

### Setting Up a Development Environment

1. Clone the repository
2. Set up a virtual environment: `python -m venv venv`
3. Activate the virtual environment: `source venv/bin/activate` (Linux/Mac) or `venv\Scripts\activate` (Windows)
4. Install development dependencies: `pip install -r requirements-dev.txt`

### Running Tests

This integration includes comprehensive tests to ensure everything works as expected:

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=custom_components.my_carbon_footprint

# Run specific test files
pytest tests/test_config_flow/
pytest tests/test_sensor/
pytest tests/test_service.py
pytest tests/test_coordinator.py
```

### Test Coverage

The tests cover:
- Config flow functionality
- Sensor creation and updates
- Service functionality
- Coordinator calculations and error handling

## Credits

Developed by [Your Name]

## License

This project is licensed under the MIT License - see the LICENSE file for details.