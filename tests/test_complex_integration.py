from src.manager import Manager
from src.models import ApartmentSettlement, Bill, Parameters, Tenant, TenantSettlement


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


# Test z gałęzi 'extra-integration-test'
def test_apartment_costs_with_optional_parameters():
    manager = Manager(Parameters())
    manager.bills.append(Bill(
        apartment='apart-polanka',
        date_due='2025-03-15',
        settlement_year=2025,
        settlement_month=2,
        amount_pln=1250.0,
        type='rent'
    ))

    manager.bills.append(Bill(
        apartment='apart-polanka',
        date_due='2024-03-15',
        settlement_year=2024,
        settlement_month=2,
        amount_pln=1150.0,
        type='rent'
    ))

    manager.bills.append(Bill(
        apartment='apart-polanka',
        date_due='2024-02-02',
        settlement_year=2024,
        settlement_month=1,
        amount_pln=222.0,
        type='electricity'
    ))

    costs = manager.get_apartment_costs('apartment-1', 2024, 1)
    assert costs is None

    costs = manager.get_apartment_costs('apart-polanka', 2024, 3)
    assert costs == 0.0

    costs = manager.get_apartment_costs('apart-polanka', 2024, 1)
    assert costs == 222.0

    costs = manager.get_apartment_costs('apart-polanka', 2025, 1)
    assert costs == 910.0

    # Brak podanego miesiąca -> suma za cały rok 2024 (1150.0 + 222.0)
    costs = manager.get_apartment_costs('apart-polanka', 2024)
    assert costs == 1372.0

    # Brak podanego roku i miesiąca -> suma z całej historii
    costs = manager.get_apartment_costs('apart-polanka')
    assert costs == 3532.0


def test_apartment_costs_invalid_month():
    manager = Manager(Parameters())

    # Nieprawidłowy miesiąc (np. 13, 0, -1) -> zwraca None
    assert manager.get_apartment_costs('apart-polanka', 2024, 13) is None
    assert manager.get_apartment_costs('apart-polanka', 2024, 0) is None
    assert manager.get_apartment_costs('apart-polanka', 2024, -1) is None


def test_create_apartment_settlement():
    manager = Manager(Parameters())

    # Scenariusz 1: Mieszkanie z rachunkami w danym miesiącu (styczeń 2025: 760.0 + 150.0 = 910.0)
    settlement = manager.create_apartment_settlement('apart-polanka', 2025, 1)
    assert settlement is not None
    assert isinstance(settlement, ApartmentSettlement)
    assert settlement.apartment == 'apart-polanka'
    assert settlement.year == 2025
    assert settlement.month == 1
    assert settlement.total_bills_pln == 910.0
    assert settlement.total_rent_pln == 0.0
    assert settlement.total_due_pln == 910.0

    # Scenariusz 2: Mieszkanie bez rachunków w danym miesiącu (maj 2025: 0.0)
    settlement_no_bills = manager.create_apartment_settlement('apart-polanka', 2025, 5)
    assert settlement_no_bills is not None
    assert isinstance(settlement_no_bills, ApartmentSettlement)
    assert settlement_no_bills.apartment == 'apart-polanka'
    assert settlement_no_bills.year == 2025
    assert settlement_no_bills.month == 5
    assert settlement_no_bills.total_bills_pln == 0.0
    assert settlement_no_bills.total_rent_pln == 0.0
    assert settlement_no_bills.total_due_pln == 0.0

    # Przypadki brzegowe:
    # 1. Mieszkanie nie istnieje
    assert manager.create_apartment_settlement('non-existent-apartment', 2025, 1) is None
    # 2. Nieprawidłowy miesiąc
    assert manager.create_apartment_settlement('apart-polanka', 2025, 13) is None
    assert manager.create_apartment_settlement('apart-polanka', 2025, 0) is None


def test_create_tenant_settlements():
    manager = Manager(Parameters())

    # Scenariusz 1: Mieszkanie z 2 najemcami, równy podział kosztów (600 PLN / 2 = 300 PLN każdy)
    manager.tenants = {
        'tenant-1': Tenant(
            name='Jan Nowak',
            apartment='apart-polanka',
            room='room-1',
            rent_pln=1500.0,
            deposit_pln=3000.0,
            date_agreement_from='2024-01-01',
            date_agreement_to='2024-12-31',
        ),
        'tenant-2': Tenant(
            name='Adam Kowalski',
            apartment='apart-polanka',
            room='room-2',
            rent_pln=1400.0,
            deposit_pln=2900.0,
            date_agreement_from='2024-01-01',
            date_agreement_to='2024-12-31',
        ),
    }
    settlement_2_tenants = ApartmentSettlement(
        apartment='apart-polanka',
        month=1,
        year=2025,
        total_rent_pln=0.0,
        total_bills_pln=600.0,
        total_due_pln=600.0,
    )
    tenant_settlements_2 = manager.create_tenant_settlements(settlement_2_tenants)

    assert len(tenant_settlements_2) == 2
    assert all(isinstance(ts, TenantSettlement) for ts in tenant_settlements_2)
    assert tenant_settlements_2[0].bills_pln == 300.0
    assert tenant_settlements_2[1].bills_pln == 300.0
    assert tenant_settlements_2[0].total_due_pln == 300.0
    assert tenant_settlements_2[1].total_due_pln == 300.0
    assert tenant_settlements_2[0].apartment_settlement == 'apart-polanka'
    assert tenant_settlements_2[0].month == 1
    assert tenant_settlements_2[0].year == 2025

    # Scenariusz 2: Mieszkanie z tylko 1 najemcą (500 PLN / 1 = 500 PLN)
    manager.tenants = {
        'tenant-1': Tenant(
            name='Jan Nowak',
            apartment='apart-polanka',
            room='room-1',
            rent_pln=1500.0,
            deposit_pln=3000.0,
            date_agreement_from='2024-01-01',
            date_agreement_to='2024-12-31',
        )
    }
    settlement_1_tenant = ApartmentSettlement(
        apartment='apart-polanka',
        month=2,
        year=2025,
        total_rent_pln=0.0,
        total_bills_pln=500.0,
        total_due_pln=500.0,
    )
    tenant_settlements_1 = manager.create_tenant_settlements(settlement_1_tenant)

    assert len(tenant_settlements_1) == 1
    assert isinstance(tenant_settlements_1[0], TenantSettlement)
    assert tenant_settlements_1[0].tenant == 'tenant-1'
    assert tenant_settlements_1[0].bills_pln == 500.0
    assert tenant_settlements_1[0].total_due_pln == 500.0

    # Scenariusz 3: Mieszkanie nie ma żadnych najemców -> rozliczenia nie powinny być tworzone
    manager.tenants = {}
    settlement_0_tenants = ApartmentSettlement(
        apartment='apart-polanka',
        month=3,
        year=2025,
        total_rent_pln=0.0,
        total_bills_pln=400.0,
        total_due_pln=400.0,
    )
    tenant_settlements_0 = manager.create_tenant_settlements(settlement_0_tenants)

    assert isinstance(tenant_settlements_0, list)
    assert len(tenant_settlements_0) == 0

