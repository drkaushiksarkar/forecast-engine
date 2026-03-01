# Forecast Engine

Production-grade forecast engine with model registry, feature store, prediction serving, and ensemble methods.

## Architecture

```
forecast-engine/
  src/           # Core modules
  tests/         # Unit and integration tests
  config/        # Configuration files
  docs/          # Documentation
```

## Modules

- **model_runner**: Core model runner functionality
- **feature_store**: Core feature store functionality
- **prediction_server**: Core prediction server functionality
- **evaluator**: Core evaluator functionality
- **ensemble_builder**: Core ensemble builder functionality

## Quick Start

```bash
pip install -r requirements.txt
python -m forecast_engine.main
```

## Testing

```bash
pytest tests/ -v
```

## License

MIT License - see LICENSE for details.
