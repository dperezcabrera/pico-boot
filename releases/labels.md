# GitHub Topics — pico-boot

## Topics actuales

_(ninguno)_

## Topics propuestos (9)

```
pico-framework
dependency-injection
ioc
auto-discovery
entry-points
plugin-system
bootstrap
asyncio
python-plugins
```

### Justificación

| Topic | Razón |
|---|---|
| `pico-framework` | Ecosistema compartido |
| `dependency-injection` | Core del ecosistema |
| `ioc` | Abreviatura estándar |
| `auto-discovery` | Feature principal — descubre módulos DI automáticamente |
| `entry-points` | Mecanismo usado para plugin discovery (setuptools entry_points) |
| `plugin-system` | Es lo que hace: un sistema de plugins para pico-ioc |
| `bootstrap` | Su rol: arrancar la aplicación |
| `asyncio` | Compatible con async |
| `python-plugins` | Refuerza discoverability para quien busca plugins en Python |

## Comando para aplicar

```bash
gh repo edit dperezcabrera/pico-boot --add-topic pico-framework,dependency-injection,ioc,auto-discovery,entry-points,plugin-system,bootstrap,asyncio,python-plugins
```
