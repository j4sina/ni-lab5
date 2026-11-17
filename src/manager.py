from src.models import Apartment, ApartmentSettlement, Bill, Parameters, Tenant, TenantSettlement, Transfer


class Manager:
    def __init__(self, parameters: Parameters):
        self.parameters = parameters 

        self.apartments = {}
        self.tenants = {}
        self.transfers = []
        self.bills = []
       
        self.load_data()

    def load_data(self):
        self.apartments = Apartment.from_json_file(self.parameters.apartments_json_path)
        self.tenants = Tenant.from_json_file(self.parameters.tenants_json_path)
        self.transfers = Transfer.from_json_file(self.parameters.transfers_json_path)
        self.bills = Bill.from_json_file(self.parameters.bills_json_path)

    def get_apartment_costs(self, apartment_key: str, year: int | None = None, month: int | None = None) -> float | None:
        if apartment_key not in self.apartments:
            return None

        if month is not None and not (1 <= month <= 12):
            return None

        total = 0.0
        for bill in self.bills:
            if (
                bill.apartment == apartment_key
                and (year is None or bill.settlement_year == year)
                and (month is None or bill.settlement_month == month)
            ):
                total += bill.amount_pln

        return total

    def create_apartment_settlement(self, apartment_key: str, year: int, month: int) -> ApartmentSettlement | None:
        if apartment_key not in self.apartments:
            return None

        bills_cost = self.get_apartment_costs(apartment_key, year, month)
        if bills_cost is None:
            return None

        total_rent = 0.0
        total_bills = bills_cost
        total_due = total_rent + total_bills

        return ApartmentSettlement(
            apartment=apartment_key,
            month=month,
            year=year,
            total_rent_pln=total_rent,
            total_bills_pln=total_bills,
            total_due_pln=total_due,
        )

    get_apartment_settlement = create_apartment_settlement

    def create_tenant_settlements(
        self,
        apartment_settlement: ApartmentSettlement | str,
        year: int | None = None,
        month: int | None = None,
    ) -> list[TenantSettlement]:
        if isinstance(apartment_settlement, str):
            settlement = self.create_apartment_settlement(apartment_settlement, year, month)
            if settlement is None:
                return []
            apartment_settlement = settlement

        apartment_key = apartment_settlement.apartment
        active_tenants = [
            (t_key, tenant)
            for t_key, tenant in self.tenants.items()
            if tenant.apartment == apartment_key
        ]

        if not active_tenants:
            return []

        tenant_count = len(active_tenants)
        bills_share = apartment_settlement.total_bills_pln / tenant_count

        return [
            TenantSettlement(
                tenant=t_key,
                apartment_settlement=apartment_settlement.apartment,
                month=apartment_settlement.month,
                year=apartment_settlement.year,
                rent_pln=0.0,
                bills_pln=bills_share,
                total_due_pln=bills_share,
                balance_pln=-bills_share,
            )
            for t_key, tenant in active_tenants
        ]

    create_tenants_settlements = create_tenant_settlements
    get_tenant_settlements = create_tenant_settlements
    get_tenants_settlements = create_tenant_settlements

    def check_tenants_apartment_keys(self) -> bool:
        for tenant in self.tenants.values():
            if tenant.apartment not in self.apartments:
                return False
        return True