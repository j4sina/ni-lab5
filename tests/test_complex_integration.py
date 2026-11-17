from src.manager import Manager
from src.models import Parameters


def test_apartment_costs_for_specific_month():
    manager = Manager(Parameters())

    # 1. Mieszkanie nie istnieje
    assert manager.get_apartment_costs('non-existent-apartment', 2025, 1) is None

    # 2. Mieszkanie istnieje, ale nie ma żadnych rachunków w tym miesiącu
    assert manager.get_apartment_costs('apart-polanka', 2025, 5) == 0.0

    # 3. Rok się zgadza, ale miesiąc nie
    assert manager.get_apartment_costs('apart-polanka', 2025, 2) == 0.0

    # 4. Mieszkanie ma rachunki w tym miesiącu (760.0 + 150.0)
    assert manager.get_apartment_costs('apart-polanka', 2025, 1) == 910.0
