from datetime import date

from backend.app.data.trading_calendar import TradingCalendarProvider


def test_count_between_uses_inclusive_window():
    provider = TradingCalendarProvider(
        trade_dates=[date(2025, 1, 2), date(2025, 1, 3), date(2025, 1, 6)]
    )

    assert provider.count_between(date(2025, 1, 1), date(2025, 1, 7)) == 3
    assert provider.count_between(date(2025, 1, 3), date(2025, 1, 5)) == 1
    assert provider.count_between(date(2025, 1, 7), date(2025, 1, 31)) == 0


def test_as_callable_is_injectable_as_trading_days():
    provider = TradingCalendarProvider(trade_dates=[date(2025, 1, 2), date(2025, 1, 3)])

    trading_days = provider.as_callable()

    assert trading_days(date(2025, 1, 1), date(2025, 1, 31)) == 2


def test_can_inject_fetch_callable_instead_of_network():
    provider = TradingCalendarProvider(fetch=lambda: [date(2025, 1, 2), date(2025, 1, 3)])

    assert provider.get_trade_dates() == [date(2025, 1, 2), date(2025, 1, 3)]
