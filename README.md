# My Carbon Footprint

A Home Assistant integration to track your carbon footprint using your energy consumption and carbon intensity data.

## Features

- Calculates carbon footprint from energy usage and carbon intensity sensors
- Real-time and historical tracking
- Supports multiple energy sources
- Cumulative and per-source statistics

## Installation

- **HACS:** Search and install "My Carbon Footprint" via HACS Integrations
- **Manual:** Copy `custom_components/my_carbon_footprint` to your Home Assistant `custom_components` directory and restart Home Assistant

## Configuration

- Add the integration in Home Assistant and select your carbon intensity and energy consumption sensors
- Works with standard energy and carbon intensity sensors (kWh, gCO2/kWh)

## Usage

- Provides sensors for total and per-source carbon footprint
- View daily, monthly, and cumulative carbon emissions
- Includes a service to reset counters if needed

## Development & Testing

- Install all dependencies (including dev):
  - `uv sync --dev --group test`
- Run tests with `uv run pytest`

## License

MIT License