"""Privacy-safe diagnostics for Yahoo! Japan Weather."""

from __future__ import annotations

from homeassistant.core import HomeAssistant

from . import YahooConfigEntry


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: YahooConfigEntry
) -> dict[str, bool | int | str | None]:
    """Return operational metadata without location or forecast contents."""
    coordinator = entry.runtime_data
    data = coordinator.data
    return {
        "last_update_success": coordinator.last_update_success,
        "last_error_category": coordinator.last_error_category,
        "last_successful_update": (
            coordinator.last_successful_update.isoformat()
            if coordinator.last_successful_update is not None
            else None
        ),
        "published_at": data.published_at,
        "hourly_count": len(data.hourly),
        "daily_count": len(data.daily),
    }
